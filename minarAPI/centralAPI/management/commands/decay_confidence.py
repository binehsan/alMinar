"""
Management command: decay_confidence
======================================

Finds all ConfidenceRecords past their decayDate and drops each by one level.
Also checks for masjid admins who haven't logged in for 90 days and decays
their C3 masjids to C2.

Intended to be run periodically via cron or Celery beat.

Usage:
    python manage.py decay_confidence
"""

from django.core.management.base import BaseCommand

from centralAPI.services import decay_all_confidence, decay_inactive_admins


class Command(BaseCommand):
    help = "Decay confidence levels for masjids whose decayDate has passed or whose admins are inactive."

    def handle(self, *args, **options):
        count = decay_all_confidence()
        self.stdout.write(
            self.style.SUCCESS(f"Decayed {count} confidence record(s) (overdue).")
        )
        inactive = decay_inactive_admins()
        self.stdout.write(
            self.style.SUCCESS(f"Decayed {inactive} C3 record(s) for inactive admins.")
        )
