"""
Al-Minār — Service Layer
=========================

Pure business logic, no HTTP concerns. Called by views and management commands.

Key functions:
  • process_signal()       — evaluate a new signal and upgrade confidence if warranted
  • decay_confidence()     — drop a single record's confidence if past its decay date
  • decay_all_confidence() — batch decay for scheduled jobs
  • check_badge_validity() — determine if a badge is currently valid
  • calculate_decay_date() — compute when a confidence level should next decay
"""

from datetime import timedelta

from django.utils import timezone

from .models import ConfidenceRecord, Signal, VerifiedBadge


# ---------------------------------------------------------------------------
# Confidence — decay date calculation
# ---------------------------------------------------------------------------

def calculate_decay_date(confidence_level):
    """
    Given a confidence level (0–3), return the datetime when it should
    decay to the next lower level.  Level 0 does not decay further.
    """
    days = ConfidenceRecord.DECAY_DAYS.get(confidence_level)
    if days is None:
        return None
    return timezone.now() + timedelta(days=days)


# ---------------------------------------------------------------------------
# Confidence — upgrade from signals
# ---------------------------------------------------------------------------

MIN_COMMUNITY_SIGNALS = 3          # unique users in 30 days to reach C1
COMMUNITY_SIGNAL_WINDOW_DAYS = 30  # look-back window for signal counting


def _count_unique_signal_users(masjid, days=COMMUNITY_SIGNAL_WINDOW_DAYS):
    """Count distinct users who sent USER signals for a masjid within `days`."""
    cutoff = timezone.now() - timedelta(days=days)
    return (
        Signal.objects.filter(
            masjid=masjid,
            sourceType="USER",
            created_at__gte=cutoff,
        )
        .exclude(user__isnull=True)
        .values("user")
        .distinct()
        .count()
    )


def process_signal(signal):
    """
    Evaluate a newly-created Signal and upgrade the masjid's confidence
    record if warranted.

    Rules (from spec):
      • ADMIN signal → C2 (or C3 if recent admin activity)
      • USER signals  → C1 when ≥ 3 unique users in 30 days

    Returns the (possibly updated) ConfidenceRecord.
    """
    masjid = signal.masjid

    # Ensure a ConfidenceRecord exists
    record, _created = ConfidenceRecord.objects.get_or_create(
        masjid=masjid,
        defaults={"confidenceLevel": 0},
    )

    if signal.sourceType == "ADMIN":
        # Admin verification → at least C2; if already C2 set to C3
        if record.confidenceLevel < 2:
            record.confidenceLevel = 2
        else:
            record.confidenceLevel = 3
        record.decayDate = calculate_decay_date(record.confidenceLevel)
        record.save()

    elif signal.sourceType == "USER":
        unique_users = _count_unique_signal_users(masjid)
        if unique_users >= MIN_COMMUNITY_SIGNALS and record.confidenceLevel < 1:
            record.confidenceLevel = 1
            record.decayDate = calculate_decay_date(1)
            record.save()

    # SYSTEM signals don't upgrade confidence — they're informational
    return record


# ---------------------------------------------------------------------------
# Confidence — decay
# ---------------------------------------------------------------------------

def decay_confidence(record):
    """
    If a ConfidenceRecord's decayDate has passed and its level is > 0,
    drop it by one level and set a new decayDate.

    Returns True if the record was decayed, False otherwise.
    """
    if record.confidenceLevel <= 0:
        return False
    if record.decayDate is None:
        return False
    if timezone.now() < record.decayDate:
        return False

    record.confidenceLevel -= 1
    record.decayDate = calculate_decay_date(record.confidenceLevel)
    record.save()
    return True


def decay_all_confidence():
    """
    Batch decay: find all ConfidenceRecords past their decayDate and
    drop each by one level.  Returns the number of records decayed.
    """
    overdue = ConfidenceRecord.objects.filter(
        decayDate__lte=timezone.now(),
        confidenceLevel__gt=0,
    )
    count = 0
    for record in overdue:
        if decay_confidence(record):
            count += 1
    return count


# ---------------------------------------------------------------------------
# Badge validity
# ---------------------------------------------------------------------------

def check_badge_validity(badge):
    """
    Determine whether a VerifiedBadge is currently valid.

    Invalid if:
      • isRevoked is True
      • isActive is False
      • expiryDate has passed
      • masjid's confidence is below C2
      • masjid is inactive

    Side effect: sets isActive=False and saves if the badge is found invalid
    due to confidence or expiry (auto-revocation).

    Returns True/False.
    """
    if badge.isRevoked:
        return False

    if not badge.isActive:
        return False

    should_deactivate = False

    # Expiry check
    if badge.expiryDate and badge.expiryDate < timezone.now():
        should_deactivate = True

    # Masjid inactive check
    if not badge.masjid.isActive:
        should_deactivate = True

    # Confidence check — badge requires at least C2
    if badge.masjid.confidenceRecord is None:
        # No confidence record at all — treat as C0
        should_deactivate = True
    elif badge.masjid.confidenceRecord.confidenceLevel < 2:
        should_deactivate = True

    if should_deactivate:
        badge.isActive = False
        badge.save(update_fields=["isActive"])
        return False

    return True
