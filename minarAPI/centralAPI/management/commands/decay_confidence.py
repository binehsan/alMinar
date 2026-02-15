"""
Management command: decay_confidence
======================================

Finds all ConfidenceRecords past their decayDate and drops each by one level.
Intended to be run periodically via cron or Celery beat.

Usage:
    python manage.py decay_confidence
"""

from django.core.management.base import BaseCommand

from centralAPI.services import decay_all_confidence


class Command(BaseCommand):
    help = "Decay confidence levels for masjids whose decayDate has passed."

    def handle(self, *args, **options):
        count = decay_all_confidence()
        self.stdout.write(
            self.style.SUCCESS(f"Decayed {count} confidence record(s).")
        )
