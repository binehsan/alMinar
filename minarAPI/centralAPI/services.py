"""
Al-Minar  -  Service Layer
===========================
Pure business logic, no HTTP concerns.
"""

from datetime import timedelta

from django.utils import timezone

from .models import ConfidenceRecord, Signal, VerifiedBadge, MasjidAdmin


# ---------------------------------------------------------------------------
# Confidence - decay date calculation
# ---------------------------------------------------------------------------

def calculate_decay_date(confidence_level):
    """C3 decays in 90 days, C2 in 180, C1 in 365.  C0 doesn't decay."""
    days = ConfidenceRecord.DECAY_DAYS.get(confidence_level)
    if days is None:
        return None
    return timezone.now() + timedelta(days=days)


# ---------------------------------------------------------------------------
# Confidence - upgrade from signals
# ---------------------------------------------------------------------------

MIN_COMMUNITY_SIGNALS = 3
COMMUNITY_SIGNAL_WINDOW_DAYS = 30


def _count_unique_signal_users(masjid, days=COMMUNITY_SIGNAL_WINDOW_DAYS):
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
    Evaluate a new signal and potentially upgrade the masjid's confidence.
    - Community (USER) signals: 3+ unique users → C0→C1
    - Admin signals only log presence; upgrades to C2/C3 require doc verification.
    """
    masjid = signal.masjid
    record, _created = ConfidenceRecord.objects.get_or_create(
        masjid=masjid,
        defaults={"confidenceLevel": 0},
    )

    if signal.sourceType == "USER":
        unique_users = _count_unique_signal_users(masjid)
        if unique_users >= MIN_COMMUNITY_SIGNALS and record.confidenceLevel < 1:
            record.confidenceLevel = 1
            record.decayDate = calculate_decay_date(1)
            record.save()

    elif signal.sourceType == "ADMIN":
        # Admin signals refresh the decay timer if already at C2/C3
        if record.confidenceLevel >= 2:
            record.decayDate = calculate_decay_date(record.confidenceLevel)
            record.save()
        # But do NOT auto-upgrade; doc verification required for C2+

    return record


def approve_verification_document(doc):
    """
    Called when a VerificationDocument is approved.
    Upgrades the masjid directly to C3 (bypassing C2).
    Also marks the admin's identity as verified.
    """
    link = doc.masjid_admin_link
    masjid = link.masjid

    # Mark admin identity verified
    link.verifiedIdentity = True
    link.verifiedAt = timezone.now()
    link.save(update_fields=["verifiedIdentity", "verifiedAt"])

    # Upgrade to C3 directly
    record, _ = ConfidenceRecord.objects.get_or_create(
        masjid=masjid, defaults={"confidenceLevel": 0}
    )
    record.confidenceLevel = 3
    record.decayDate = calculate_decay_date(3)
    record.save()


# ---------------------------------------------------------------------------
# Confidence - decay
# ---------------------------------------------------------------------------

def decay_confidence(record):
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
    """Decay all overdue confidence records."""
    overdue = ConfidenceRecord.objects.filter(
        decayDate__lte=timezone.now(),
        confidenceLevel__gt=0,
    )
    count = 0
    for record in overdue:
        if decay_confidence(record):
            count += 1
    return count


def decay_inactive_admins():
    """
    For C3 masjids managed by admins: if the admin hasn't logged in for
    90 days, start decaying their masjid's confidence.
    """
    cutoff = timezone.now() - timedelta(days=90)
    # Find MasjidAdmin links where the admin hasn't logged in recently
    stale_links = MasjidAdmin.objects.filter(
        verifiedIdentity=True,
        user__last_login__lt=cutoff,
        masjid__confidence_record__confidenceLevel__gte=3,
    ).select_related("masjid__confidence_record")

    count = 0
    for link in stale_links:
        cr = getattr(link.masjid, "confidence_record", None)
        if cr and cr.confidenceLevel >= 3:
            cr.confidenceLevel = 2
            cr.decayDate = calculate_decay_date(2)
            cr.save()
            count += 1
    return count


# ---------------------------------------------------------------------------
# Badge validity
# ---------------------------------------------------------------------------

def check_badge_validity(badge):
    if badge.isRevoked:
        return False
    if not badge.isActive:
        return False

    should_deactivate = False

    if badge.expiryDate and badge.expiryDate < timezone.now():
        should_deactivate = True

    if not badge.masjid.isActive:
        should_deactivate = True

    cr = getattr(badge.masjid, "confidence_record", None)
    if cr is None:
        should_deactivate = True
    elif cr.confidenceLevel < 2:
        should_deactivate = True

    if should_deactivate:
        badge.isActive = False
        badge.save(update_fields=["isActive"])
        return False

    return True
