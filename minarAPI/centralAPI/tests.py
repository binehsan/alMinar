"""
Al-Minār — Comprehensive Test Suite
=====================================

Covers:
  • Model creation & constraints
  • Serializer validation & output
  • API endpoint CRUD, permissions & filtering
  • Custom actions (badge revoke, verify, nested masjid actions)

Run with:  python manage.py test centralAPI
"""

import uuid
from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import (
    AdminUser,
    RegularUser,
    Masjid,
    ConfidenceRecord,
    LocationRecord,
    PrayerTimeRecord,
    Prayer,
    PrayerTime,
    Signal,
    VerifiedBadge,
    MasjidAdmin as MasjidAdminModel,
    FavouriteMasjid,
)
from .serializers import (
    MasjidSerializer,
    ConfidenceRecordSerializer,
    LocationRecordSerializer,
    PrayerTimeRecordSerializer,
    PrayerTimeSerializer,
    SignalSerializer,
    VerifiedBadgeSerializer,
    MasjidAdminSerializer,
    FavouriteMasjidSerializer,
)


# ===========================================================================
# Helper mixin — creates shared test data once per test method
# ===========================================================================

class TestDataMixin:
    """Creates reusable objects that most tests need."""

    def setUp(self):
        # Django auth users (needed for JWT / session auth)
        self.django_admin = User.objects.create_superuser(
            username="superadmin", password="testpass123"
        )
        self.django_user = User.objects.create_user(
            username="regularuser", password="testpass123"
        )

        # App-level users
        self.admin_user = AdminUser.objects.create(
            username="admin1", email="admin1@alminar.org"
        )
        self.regular_user = RegularUser.objects.create(
            username="user1", email="user1@alminar.org"
        )

        # A masjid (no confidence / location yet)
        self.masjid = Masjid.objects.create(name="Masjid Al-Noor")

        # API client
        self.client = APIClient()

    # ----- auth helpers -----
    def auth_as_admin(self):
        self.client.force_authenticate(user=self.django_admin)

    def auth_as_user(self):
        self.client.force_authenticate(user=self.django_user)

    def auth_none(self):
        self.client.force_authenticate(user=None)


# ===========================================================================
# 1.  MODEL TESTS
# ===========================================================================

class MasjidModelTest(TestDataMixin, TestCase):
    """Tests for the Masjid model itself."""

    def test_masjid_creation_generates_uuid(self):
        """Masjid PK is a UUID, auto-generated."""
        self.assertIsInstance(self.masjid.masjidID, uuid.UUID)

    def test_masjid_default_active(self):
        """New masjids default to isActive=True."""
        self.assertTrue(self.masjid.isActive)

    def test_masjid_timestamps(self):
        """created_at and updated_at are auto-set."""
        self.assertIsNotNone(self.masjid.created_at)
        self.assertIsNotNone(self.masjid.updated_at)


class ConfidenceRecordModelTest(TestDataMixin, TestCase):

    def test_default_confidence_level(self):
        """New confidence records start at C0."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid)
        self.assertEqual(cr.confidenceLevel, 0)

    def test_str_representation(self):
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=2)
        self.assertEqual(str(cr), "Masjid Al-Noor - C2")

    def test_decay_days_constant(self):
        """DECAY_DAYS maps each level to correct day count."""
        self.assertEqual(ConfidenceRecord.DECAY_DAYS, {3: 90, 2: 180, 1: 365})


class LocationRecordModelTest(TestDataMixin, TestCase):

    def test_creation(self):
        lr = LocationRecord.objects.create(
            masjid=self.masjid,
            latitude=51.5074,
            longitude=-0.1278,
            city="London",
            country="UK - United Kingdom of Great Britain and Northern Ireland",
        )
        self.assertIsInstance(lr.lrID, uuid.UUID)
        self.assertEqual(lr.city, "London")


class PrayerTimeRecordModelTest(TestDataMixin, TestCase):

    def test_unique_together_masjid_date(self):
        """Cannot create two records for the same masjid + date."""
        PrayerTimeRecord.objects.create(
            masjid=self.masjid, date=date(2026, 2, 15)
        )
        with self.assertRaises(Exception):
            PrayerTimeRecord.objects.create(
                masjid=self.masjid, date=date(2026, 2, 15)
            )

    def test_default_model_type(self):
        ptr = PrayerTimeRecord.objects.create(
            masjid=self.masjid, date=date(2026, 2, 15)
        )
        self.assertEqual(ptr.modelType, "UNKNOWN")


class PrayerTimeModelTest(TestDataMixin, TestCase):

    def test_clean_raises_without_times(self):
        """clean() rejects a PrayerTime with neither adhan nor iqama."""
        prayer = Prayer.objects.create(name="fajr")
        ptr = PrayerTimeRecord.objects.create(
            masjid=self.masjid, date=date(2026, 2, 15)
        )
        pt = PrayerTime(record=ptr, prayer=prayer)
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            pt.clean()


class SignalModelTest(TestDataMixin, TestCase):

    def test_signal_creation(self):
        sig = Signal.objects.create(
            masjid=self.masjid,
            user=self.regular_user,
            signalType="PRAYED",
            sourceType="USER",
        )
        self.assertIsInstance(sig.signalID, uuid.UUID)

    def test_system_signal_no_user(self):
        """System signals can have user=None."""
        sig = Signal.objects.create(
            masjid=self.masjid,
            signalType="ACTIVE",
            sourceType="SYSTEM",
            user=None,
        )
        self.assertIsNone(sig.user)


class VerifiedBadgeModelTest(TestDataMixin, TestCase):

    def test_badge_tokens_are_unique(self):
        b1 = VerifiedBadge.objects.create(
            masjid=self.masjid, issuedBy=self.admin_user
        )
        b2 = VerifiedBadge.objects.create(
            masjid=self.masjid, issuedBy=self.admin_user
        )
        self.assertNotEqual(b1.token, b2.token)

    def test_default_active_not_revoked(self):
        badge = VerifiedBadge.objects.create(
            masjid=self.masjid, issuedBy=self.admin_user
        )
        self.assertTrue(badge.isActive)
        self.assertFalse(badge.isRevoked)


class FavouriteMasjidModelTest(TestDataMixin, TestCase):

    def test_unique_together(self):
        """Same user cannot favourite the same masjid twice."""
        FavouriteMasjid.objects.create(user=self.regular_user, masjid=self.masjid)
        with self.assertRaises(Exception):
            FavouriteMasjid.objects.create(user=self.regular_user, masjid=self.masjid)


class MasjidAdminModelTest(TestDataMixin, TestCase):

    def test_creation(self):
        ma = MasjidAdminModel.objects.create(
            user=self.regular_user, masjid=self.masjid
        )
        self.assertFalse(ma.verifiedIdentity)

    def test_unique_together(self):
        MasjidAdminModel.objects.create(user=self.regular_user, masjid=self.masjid)
        with self.assertRaises(Exception):
            MasjidAdminModel.objects.create(
                user=self.regular_user, masjid=self.masjid
            )


# ===========================================================================
# 2.  SERIALIZER TESTS
# ===========================================================================

class MasjidSerializerTest(TestDataMixin, TestCase):

    def test_fields_present(self):
        """Serializer output contains all expected keys."""
        data = MasjidSerializer(self.masjid).data
        expected = {
            "masjidID", "name", "description", "isActive",
            "confidenceRecord", "locationRecord", "created_at", "updated_at",
        }
        self.assertEqual(set(data.keys()), expected)

    def test_read_only_fields(self):
        """masjidID, created_at, updated_at cannot be set via serializer."""
        fake_id = str(uuid.uuid4())
        ser = MasjidSerializer(data={
            "masjidID": fake_id,
            "name": "Test Masjid",
        })
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        # masjidID should be auto-generated, NOT the one we passed
        self.assertNotEqual(str(instance.masjidID), fake_id)


class PrayerTimeSerializerTest(TestDataMixin, TestCase):

    def test_validation_requires_at_least_one_time(self):
        """Serializer rejects payload with neither adhan nor iqama time."""
        prayer = Prayer.objects.create(name="fajr")
        ptr = PrayerTimeRecord.objects.create(
            masjid=self.masjid, date=date(2026, 2, 15)
        )
        ser = PrayerTimeSerializer(data={
            "record": str(ptr.ptrID),
            "prayer_id": prayer.pk,
            "adhan_time": None,
            "iqama_time": None,
        })
        self.assertFalse(ser.is_valid())

    def test_valid_with_iqama_only(self):
        """Serializer accepts iqama-only prayer time."""
        prayer = Prayer.objects.create(name="dhuhr")
        ptr = PrayerTimeRecord.objects.create(
            masjid=self.masjid, date=date(2026, 2, 15)
        )
        ser = PrayerTimeSerializer(data={
            "record": str(ptr.ptrID),
            "prayer_id": prayer.pk,
            "iqama_time": "13:30:00",
        })
        self.assertTrue(ser.is_valid(), ser.errors)


class SignalSerializerTest(TestDataMixin, TestCase):

    def test_includes_source_type(self):
        sig = Signal.objects.create(
            masjid=self.masjid, user=self.regular_user,
            signalType="PRAYED", sourceType="USER",
        )
        data = SignalSerializer(sig).data
        self.assertIn("sourceType", data)
        self.assertEqual(data["sourceType"], "USER")


class VerifiedBadgeSerializerTest(TestDataMixin, TestCase):

    def test_token_is_read_only(self):
        """Token should appear in output but not be settable."""
        badge = VerifiedBadge.objects.create(
            masjid=self.masjid, issuedBy=self.admin_user
        )
        data = VerifiedBadgeSerializer(badge).data
        self.assertIn("token", data)
        # Token is in read_only_fields
        ser = VerifiedBadgeSerializer(badge, data={"token": str(uuid.uuid4())}, partial=True)
        ser.is_valid()
        updated = ser.save()
        self.assertEqual(updated.token, badge.token)  # unchanged


# ===========================================================================
# 3.  API / VIEW TESTS — Masjid endpoints
# ===========================================================================

class MasjidAPITest(TestDataMixin, TestCase):

    def test_list_masjids_no_auth(self):
        """GET /api/masjids/ is public."""
        self.auth_none()
        resp = self.client.get("/api/masjids/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_masjid_no_auth(self):
        """GET /api/masjids/{id}/ is public."""
        self.auth_none()
        resp = self.client.get(f"/api/masjids/{self.masjid.masjidID}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Masjid Al-Noor")

    def test_create_masjid_requires_auth(self):
        """POST /api/masjids/ → 401 if unauthenticated."""
        self.auth_none()
        resp = self.client.post("/api/masjids/", {"name": "New Masjid"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_masjid_authenticated(self):
        """POST /api/masjids/ → 201 when authenticated."""
        self.auth_as_user()
        resp = self.client.post("/api/masjids/", {"name": "New Masjid"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["name"], "New Masjid")
        # UUID was auto-generated
        self.assertIn("masjidID", resp.data)

    def test_search_masjids(self):
        """GET /api/masjids/?search=noor filters by name."""
        Masjid.objects.create(name="Downtown Musalla")
        self.auth_none()
        resp = self.client.get("/api/masjids/?search=Noor")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [m["name"] for m in resp.data["results"]]
        self.assertIn("Masjid Al-Noor", names)
        self.assertNotIn("Downtown Musalla", names)

    def test_filter_by_active(self):
        """GET /api/masjids/?isActive=false returns only inactive."""
        Masjid.objects.create(name="Closed Masjid", isActive=False)
        self.auth_none()
        resp = self.client.get("/api/masjids/?isActive=false")
        for m in resp.data["results"]:
            self.assertFalse(m["isActive"])

    def test_delete_masjid_requires_auth(self):
        """DELETE /api/masjids/{id}/ → 401 unauthenticated."""
        self.auth_none()
        resp = self.client.delete(f"/api/masjids/{self.masjid.masjidID}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ===========================================================================
# 4.  API — Masjid nested actions (prayer_times, signals, badges)
# ===========================================================================

class MasjidNestedActionsTest(TestDataMixin, TestCase):

    def test_prayer_times_action(self):
        """GET /api/masjids/{id}/prayer_times/ returns related records."""
        PrayerTimeRecord.objects.create(
            masjid=self.masjid, date=date(2026, 2, 15), modelType="FULL_TIMETABLE"
        )
        self.auth_none()
        resp = self.client.get(f"/api/masjids/{self.masjid.masjidID}/prayer_times/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_signals_action(self):
        """GET /api/masjids/{id}/signals/ returns related signals."""
        Signal.objects.create(
            masjid=self.masjid, signalType="PRAYED", sourceType="USER",
            user=self.regular_user,
        )
        self.auth_none()
        resp = self.client.get(f"/api/masjids/{self.masjid.masjidID}/signals/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_badges_action(self):
        """GET /api/masjids/{id}/badges/ returns related badges."""
        VerifiedBadge.objects.create(masjid=self.masjid, issuedBy=self.admin_user)
        self.auth_none()
        resp = self.client.get(f"/api/masjids/{self.masjid.masjidID}/badges/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)


# ===========================================================================
# 5.  API — Confidence Record endpoints
# ===========================================================================

class ConfidenceRecordAPITest(TestDataMixin, TestCase):

    def test_list_public(self):
        """GET /api/confidence-records/ is public."""
        self.auth_none()
        resp = self.client.get("/api/confidence-records/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_requires_admin(self):
        """POST requires superuser — regular user gets 403."""
        self.auth_as_user()
        resp = self.client.post("/api/confidence-records/", {
            "masjid": str(self.masjid.masjidID),
            "confidenceLevel": 1,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_as_admin(self):
        """POST as superuser → 201."""
        self.auth_as_admin()
        resp = self.client.post("/api/confidence-records/", {
            "masjid": str(self.masjid.masjidID),
            "confidenceLevel": 2,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["confidenceLevel"], 2)

    def test_filter_by_level(self):
        """GET ?confidenceLevel=0 filters correctly."""
        ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=0)
        m2 = Masjid.objects.create(name="Other Masjid")
        ConfidenceRecord.objects.create(masjid=m2, confidenceLevel=3)
        self.auth_none()
        resp = self.client.get("/api/confidence-records/?confidenceLevel=0")
        for r in resp.data["results"]:
            self.assertEqual(r["confidenceLevel"], 0)


# ===========================================================================
# 6.  API — Location Record endpoints
# ===========================================================================

class LocationRecordAPITest(TestDataMixin, TestCase):

    def _create_location(self):
        return LocationRecord.objects.create(
            masjid=self.masjid,
            latitude=51.5074,
            longitude=-0.1278,
            city="London",
            country="UK - United Kingdom of Great Britain and Northern Ireland",
        )

    def test_list_public(self):
        self.auth_none()
        resp = self.client.get("/api/location-records/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_requires_auth(self):
        self.auth_none()
        resp = self.client.post("/api/location-records/", {
            "masjid": str(self.masjid.masjidID),
            "latitude": 51.5, "longitude": -0.12,
            "country": "UK - United Kingdom of Great Britain and Northern Ireland",
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_by_city(self):
        self._create_location()
        self.auth_none()
        resp = self.client.get("/api/location-records/?search=London")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data["results"]), 1)


# ===========================================================================
# 7.  API — Prayer endpoints
# ===========================================================================

class PrayerAPITest(TestDataMixin, TestCase):

    def test_list_public(self):
        """Prayers lookup is read-only and public."""
        Prayer.objects.create(name="fajr")
        self.auth_none()
        resp = self.client.get("/api/prayers/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_cannot_create(self):
        """ReadOnlyModelViewSet blocks POST."""
        self.auth_as_admin()
        resp = self.client.post("/api/prayers/", {"name": "fajr"})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class PrayerTimeRecordAPITest(TestDataMixin, TestCase):

    def test_list_public(self):
        self.auth_none()
        resp = self.client.get("/api/prayer-time-records/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_requires_auth(self):
        self.auth_none()
        resp = self.client.post("/api/prayer-time-records/", {
            "masjid": str(self.masjid.masjidID),
            "date": "2026-02-15",
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_authenticated(self):
        self.auth_as_user()
        resp = self.client.post("/api/prayer-time-records/", {
            "masjid": str(self.masjid.masjidID),
            "date": "2026-02-15",
            "modelType": "IQAMA_ONLY",
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["modelType"], "IQAMA_ONLY")

    def test_filter_by_model_type(self):
        PrayerTimeRecord.objects.create(
            masjid=self.masjid, date=date(2026, 1, 1), modelType="FULL_TIMETABLE"
        )
        PrayerTimeRecord.objects.create(
            masjid=self.masjid, date=date(2026, 1, 2), modelType="UNKNOWN"
        )
        self.auth_none()
        resp = self.client.get("/api/prayer-time-records/?modelType=FULL_TIMETABLE")
        for r in resp.data["results"]:
            self.assertEqual(r["modelType"], "FULL_TIMETABLE")


# ===========================================================================
# 8.  API — Signal endpoints
# ===========================================================================

class SignalAPITest(TestDataMixin, TestCase):

    def test_list_public(self):
        self.auth_none()
        resp = self.client.get("/api/signals/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_requires_auth(self):
        self.auth_none()
        resp = self.client.post("/api/signals/", {
            "masjid": str(self.masjid.masjidID),
            "signalType": "PRAYED",
            "sourceType": "USER",
            "user": self.regular_user.username,
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_signal_authenticated(self):
        self.auth_as_user()
        resp = self.client.post("/api/signals/", {
            "masjid": str(self.masjid.masjidID),
            "signalType": "JUMMAH",
            "sourceType": "USER",
            "user": self.regular_user.username,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["signalType"], "JUMMAH")

    def test_filter_by_signal_type(self):
        Signal.objects.create(
            masjid=self.masjid, signalType="PRAYED", sourceType="USER",
            user=self.regular_user,
        )
        Signal.objects.create(
            masjid=self.masjid, signalType="JUMMAH", sourceType="USER",
            user=self.regular_user,
        )
        self.auth_none()
        resp = self.client.get("/api/signals/?signalType=PRAYED")
        for r in resp.data["results"]:
            self.assertEqual(r["signalType"], "PRAYED")


# ===========================================================================
# 9.  API — Verified Badge endpoints + revoke + verify
# ===========================================================================

class VerifiedBadgeAPITest(TestDataMixin, TestCase):

    def _create_badge(self, **kwargs):
        defaults = {"masjid": self.masjid, "issuedBy": self.admin_user}
        defaults.update(kwargs)
        return VerifiedBadge.objects.create(**defaults)

    def test_list_public(self):
        self.auth_none()
        resp = self.client.get("/api/badges/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_requires_admin(self):
        """Regular user cannot create a badge."""
        self.auth_as_user()
        resp = self.client.post("/api/badges/", {
            "masjid": str(self.masjid.masjidID),
            "issuedBy": self.admin_user.username,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_as_admin(self):
        self.auth_as_admin()
        resp = self.client.post("/api/badges/", {
            "masjid": str(self.masjid.masjidID),
            "issuedBy": self.admin_user.username,
            "isActive": True,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp.data["isActive"])
        self.assertFalse(resp.data["isRevoked"])

    def test_revoke_action(self):
        """POST /api/badges/{id}/revoke/ sets isActive=False, isRevoked=True."""
        badge = self._create_badge()
        self.auth_as_admin()
        resp = self.client.post(f"/api/badges/{badge.badgeID}/revoke/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["isActive"])
        self.assertTrue(resp.data["isRevoked"])

    def test_revoke_requires_admin(self):
        badge = self._create_badge()
        self.auth_as_user()
        resp = self.client.post(f"/api/badges/{badge.badgeID}/revoke/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class BadgeVerifyEndpointTest(TestDataMixin, TestCase):
    """Tests for the public GET /api/verify/{token}/ endpoint."""

    def _create_badge(self, **kwargs):
        defaults = {"masjid": self.masjid, "issuedBy": self.admin_user}
        defaults.update(kwargs)
        return VerifiedBadge.objects.create(**defaults)

    def test_verify_active_badge(self):
        # Badge validity now requires C2+ confidence
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=2)
        self.masjid.confidenceRecord = cr
        self.masjid.save()
        badge = self._create_badge()
        resp = self.client.get(f"/api/verify/{badge.token}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["valid"])
        self.assertEqual(resp.data["masjid"], "Masjid Al-Noor")

    def test_verify_revoked_badge(self):
        badge = self._create_badge(isActive=False, isRevoked=True)
        resp = self.client.get(f"/api/verify/{badge.token}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["valid"])

    def test_verify_expired_badge(self):
        badge = self._create_badge(
            expiryDate=timezone.now() - timedelta(days=1)
        )
        resp = self.client.get(f"/api/verify/{badge.token}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["valid"])

    def test_verify_nonexistent_token(self):
        fake_token = uuid.uuid4()
        resp = self.client.get(f"/api/verify/{fake_token}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(resp.data["valid"])

    def test_verify_updates_last_checked(self):
        badge = self._create_badge()
        self.assertIsNone(badge.lastCheckedAt)
        self.client.get(f"/api/verify/{badge.token}/")
        badge.refresh_from_db()
        self.assertIsNotNone(badge.lastCheckedAt)


# ===========================================================================
# 10. API — MasjidAdmin endpoints
# ===========================================================================

class MasjidAdminAPITest(TestDataMixin, TestCase):

    def test_list_requires_auth(self):
        self.auth_none()
        resp = self.client.get("/api/masjid-admins/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authenticated(self):
        self.auth_as_user()
        resp = self.client.get("/api/masjid-admins/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_authenticated(self):
        self.auth_as_user()
        resp = self.client.post("/api/masjid-admins/", {
            "user": self.regular_user.username,
            "masjid": str(self.masjid.masjidID),
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertFalse(resp.data["verifiedIdentity"])


# ===========================================================================
# 11. API — FavouriteMasjid endpoints
# ===========================================================================

class FavouriteMasjidAPITest(TestDataMixin, TestCase):

    def test_list_requires_auth(self):
        self.auth_none()
        resp = self.client.get("/api/favourites/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_favourite(self):
        self.auth_as_user()
        resp = self.client.post("/api/favourites/", {
            "user": self.regular_user.username,
            "masjid": str(self.masjid.masjidID),
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_duplicate_favourite_rejected(self):
        """Same user + masjid combo → 400."""
        FavouriteMasjid.objects.create(user=self.regular_user, masjid=self.masjid)
        self.auth_as_user()
        resp = self.client.post("/api/favourites/", {
            "user": self.regular_user.username,
            "masjid": str(self.masjid.masjidID),
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_favourite(self):
        fav = FavouriteMasjid.objects.create(user=self.regular_user, masjid=self.masjid)
        self.auth_as_user()
        resp = self.client.delete(f"/api/favourites/{fav.favID}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


# ===========================================================================
# 12. API — User endpoints
# ===========================================================================

class AdminUserAPITest(TestDataMixin, TestCase):

    def test_requires_admin(self):
        """Regular user cannot access admin-users endpoint."""
        self.auth_as_user()
        resp = self.client.get("/api/admin-users/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list(self):
        self.auth_as_admin()
        resp = self.client.get("/api/admin-users/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class RegularUserAPITest(TestDataMixin, TestCase):

    def test_requires_auth(self):
        self.auth_none()
        resp = self.client.get("/api/users/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_can_list(self):
        self.auth_as_user()
        resp = self.client.get("/api/users/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ===========================================================================
# 13. JWT Token endpoints
# ===========================================================================

class JWTAuthTest(TestDataMixin, TestCase):

    def test_obtain_token(self):
        """POST /api/token/ with valid creds returns access + refresh."""
        resp = self.client.post("/api/token/", {
            "username": "regularuser",
            "password": "testpass123",
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_obtain_token_bad_creds(self):
        """POST /api/token/ with wrong password → 401."""
        resp = self.client.post("/api/token/", {
            "username": "regularuser",
            "password": "wrongpassword",
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        """POST /api/token/refresh/ with valid refresh → new access token."""
        resp = self.client.post("/api/token/", {
            "username": "regularuser",
            "password": "testpass123",
        })
        refresh = resp.data["refresh"]
        resp2 = self.client.post("/api/token/refresh/", {"refresh": refresh})
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp2.data)


# ===========================================================================
# 14.  BUSINESS LOGIC — Confidence upgrade from signals
# ===========================================================================

from .services import (
    process_signal,
    decay_confidence,
    decay_all_confidence,
    check_badge_validity,
    calculate_decay_date,
    MIN_COMMUNITY_SIGNALS,
    COMMUNITY_SIGNAL_WINDOW_DAYS,
)


class ConfidenceUpgradeFromSignalsTest(TestDataMixin, TestCase):
    """Test that signals cause the correct confidence-level upgrades."""

    def _create_users(self, count):
        """Create `count` distinct RegularUser objects."""
        return [
            RegularUser.objects.create(
                username=f"signaluser{i}", email=f"signaluser{i}@test.com"
            )
            for i in range(count)
        ]

    # ---- C0 → C1 via community signals ----

    def test_single_user_signal_does_not_upgrade(self):
        """One user's signal should NOT upgrade C0 → C1."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=0)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        sig = Signal.objects.create(
            masjid=self.masjid, user=self.regular_user,
            signalType="PRAYED", sourceType="USER",
        )
        process_signal(sig)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 0)

    def test_two_user_signals_not_enough(self):
        """Two unique users are still below the threshold (3)."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=0)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        users = self._create_users(2)
        for u in users:
            sig = Signal.objects.create(
                masjid=self.masjid, user=u,
                signalType="PRAYED", sourceType="USER",
            )
            process_signal(sig)

        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 0)

    def test_three_unique_users_upgrade_to_c1(self):
        """Three unique users within 30 days should upgrade C0 → C1."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=0)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        users = self._create_users(3)
        for u in users:
            sig = Signal.objects.create(
                masjid=self.masjid, user=u,
                signalType="PRAYED", sourceType="USER",
            )
            process_signal(sig)

        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 1)
        self.assertIsNotNone(cr.decayDate)

    def test_community_signals_cannot_exceed_c1(self):
        """Even many user signals won't push past C1."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=1)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        users = self._create_users(10)
        for u in users:
            sig = Signal.objects.create(
                masjid=self.masjid, user=u,
                signalType="ACTIVE", sourceType="USER",
            )
            process_signal(sig)

        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 1)

    def test_same_user_multiple_signals_counts_as_one(self):
        """Duplicate signals from the same user don't count multiple times."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=0)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        for _ in range(5):
            sig = Signal.objects.create(
                masjid=self.masjid, user=self.regular_user,
                signalType="PRAYED", sourceType="USER",
            )
            process_signal(sig)

        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 0)

    def test_old_signals_outside_window_ignored(self):
        """Signals older than 30 days should not count toward the threshold."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=0)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        users = self._create_users(3)
        old_date = timezone.now() - timedelta(days=COMMUNITY_SIGNAL_WINDOW_DAYS + 5)

        # Two old signals
        for u in users[:2]:
            sig = Signal.objects.create(
                masjid=self.masjid, user=u,
                signalType="PRAYED", sourceType="USER",
            )
            # Backdate created_at
            Signal.objects.filter(pk=sig.pk).update(created_at=old_date)

        # One recent signal
        sig = Signal.objects.create(
            masjid=self.masjid, user=users[2],
            signalType="PRAYED", sourceType="USER",
        )
        process_signal(sig)

        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 0)  # only 1 recent user

    # ---- ADMIN signals → C2 / C3 ----

    def test_admin_signal_upgrades_to_c2(self):
        """An ADMIN signal should jump a C0 masjid straight to C2."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=0)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        sig = Signal.objects.create(
            masjid=self.masjid, signalType="ADMIN_VERIFY", sourceType="ADMIN",
        )
        process_signal(sig)

        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 2)
        self.assertIsNotNone(cr.decayDate)

    def test_admin_signal_upgrades_c1_to_c2(self):
        """ADMIN signal from C1 → C2."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=1)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        sig = Signal.objects.create(
            masjid=self.masjid, signalType="ADMIN_VERIFY", sourceType="ADMIN",
        )
        process_signal(sig)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 2)

    def test_admin_signal_upgrades_c2_to_c3(self):
        """If already C2, another ADMIN signal → C3."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=2)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        sig = Signal.objects.create(
            masjid=self.masjid, signalType="ADMIN_VERIFY", sourceType="ADMIN",
        )
        process_signal(sig)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 3)

    def test_admin_signal_c3_stays_c3(self):
        """ADMIN signal on a C3 record stays at C3 (max level)."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=3)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        sig = Signal.objects.create(
            masjid=self.masjid, signalType="ADMIN_VERIFY", sourceType="ADMIN",
        )
        process_signal(sig)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 3)

    # ---- SYSTEM signals ----

    def test_system_signal_does_not_upgrade(self):
        """SYSTEM signals are informational and should not change confidence."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=0)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        sig = Signal.objects.create(
            masjid=self.masjid, signalType="ACTIVE", sourceType="SYSTEM",
        )
        process_signal(sig)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 0)

    # ---- Auto-create confidence record ----

    def test_process_signal_creates_confidence_record_if_missing(self):
        """If masjid has no ConfidenceRecord, process_signal creates one."""
        self.assertFalse(ConfidenceRecord.objects.filter(masjid=self.masjid).exists())

        sig = Signal.objects.create(
            masjid=self.masjid, signalType="ADMIN_VERIFY", sourceType="ADMIN",
        )
        record = process_signal(sig)

        self.assertIsNotNone(record)
        self.assertEqual(record.confidenceLevel, 2)

    # ---- API integration: signal create triggers process_signal ----

    def test_api_signal_create_triggers_confidence_upgrade(self):
        """POST /api/signals/ should trigger process_signal via perform_create."""
        cr = ConfidenceRecord.objects.create(masjid=self.masjid, confidenceLevel=0)
        self.masjid.confidenceRecord = cr
        self.masjid.save()

        self.auth_as_admin()
        resp = self.client.post("/api/signals/", {
            "masjid": str(self.masjid.masjidID),
            "signalType": "ADMIN_VERIFY",
            "sourceType": "ADMIN",
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 2)


# ===========================================================================
# 15.  BUSINESS LOGIC — Confidence decay over time
# ===========================================================================

class ConfidenceDecayTest(TestDataMixin, TestCase):
    """Test that confidence decays correctly when decayDate passes."""

    def test_c3_decays_to_c2(self):
        """C3 past its decayDate should drop to C2."""
        cr = ConfidenceRecord.objects.create(
            masjid=self.masjid,
            confidenceLevel=3,
            decayDate=timezone.now() - timedelta(days=1),
        )
        decayed = decay_confidence(cr)
        self.assertTrue(decayed)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 2)
        self.assertIsNotNone(cr.decayDate)  # new decay date set for C2

    def test_c2_decays_to_c1(self):
        cr = ConfidenceRecord.objects.create(
            masjid=self.masjid,
            confidenceLevel=2,
            decayDate=timezone.now() - timedelta(days=1),
        )
        decay_confidence(cr)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 1)

    def test_c1_decays_to_c0(self):
        cr = ConfidenceRecord.objects.create(
            masjid=self.masjid,
            confidenceLevel=1,
            decayDate=timezone.now() - timedelta(days=1),
        )
        decay_confidence(cr)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 0)
        self.assertIsNone(cr.decayDate)  # C0 has no further decay

    def test_c0_does_not_decay_further(self):
        """C0 is the floor — should not decay."""
        cr = ConfidenceRecord.objects.create(
            masjid=self.masjid,
            confidenceLevel=0,
            decayDate=timezone.now() - timedelta(days=1),
        )
        decayed = decay_confidence(cr)
        self.assertFalse(decayed)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 0)

    def test_no_decay_before_date(self):
        """If decayDate is in the future, no decay should happen."""
        cr = ConfidenceRecord.objects.create(
            masjid=self.masjid,
            confidenceLevel=3,
            decayDate=timezone.now() + timedelta(days=30),
        )
        decayed = decay_confidence(cr)
        self.assertFalse(decayed)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 3)

    def test_no_decay_without_decay_date(self):
        """If decayDate is None, no decay should happen."""
        cr = ConfidenceRecord.objects.create(
            masjid=self.masjid,
            confidenceLevel=2,
            decayDate=None,
        )
        decayed = decay_confidence(cr)
        self.assertFalse(decayed)

    def test_decay_date_values(self):
        """Verify the correct decay periods for each level."""
        d3 = calculate_decay_date(3)
        d2 = calculate_decay_date(2)
        d1 = calculate_decay_date(1)
        d0 = calculate_decay_date(0)

        now = timezone.now()
        self.assertAlmostEqual((d3 - now).days, 90, delta=1)
        self.assertAlmostEqual((d2 - now).days, 180, delta=1)
        self.assertAlmostEqual((d1 - now).days, 365, delta=1)
        self.assertIsNone(d0)

    def test_batch_decay_multiple_records(self):
        """decay_all_confidence() should process all overdue records."""
        m2 = Masjid.objects.create(name="Second Masjid")
        m3 = Masjid.objects.create(name="Third Masjid")

        past = timezone.now() - timedelta(days=1)
        future = timezone.now() + timedelta(days=30)

        cr1 = ConfidenceRecord.objects.create(
            masjid=self.masjid, confidenceLevel=3, decayDate=past,
        )
        cr2 = ConfidenceRecord.objects.create(
            masjid=m2, confidenceLevel=2, decayDate=past,
        )
        cr3 = ConfidenceRecord.objects.create(
            masjid=m3, confidenceLevel=1, decayDate=future,  # not yet
        )

        count = decay_all_confidence()
        self.assertEqual(count, 2)

        cr1.refresh_from_db()
        cr2.refresh_from_db()
        cr3.refresh_from_db()
        self.assertEqual(cr1.confidenceLevel, 2)
        self.assertEqual(cr2.confidenceLevel, 1)
        self.assertEqual(cr3.confidenceLevel, 1)  # unchanged

    def test_cascading_decay_requires_multiple_runs(self):
        """C3 → C2 in one run, C2 → C1 requires a second run after new decay date passes."""
        cr = ConfidenceRecord.objects.create(
            masjid=self.masjid, confidenceLevel=3,
            decayDate=timezone.now() - timedelta(days=1),
        )
        # First decay
        decay_confidence(cr)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 2)
        # decayDate should be ~180 days in the future now
        self.assertTrue(cr.decayDate > timezone.now())

        # Second decay should NOT happen (not past decayDate yet)
        decayed = decay_confidence(cr)
        self.assertFalse(decayed)
        cr.refresh_from_db()
        self.assertEqual(cr.confidenceLevel, 2)


# ===========================================================================
# 16.  BUSINESS LOGIC — Prayer time schemas
# ===========================================================================

class PrayerTimeSchemaTest(TestDataMixin, TestCase):
    """Test the four prayer-time schema patterns via the API."""

    def setUp(self):
        super().setUp()
        # Create all 5 prayer objects
        self.prayers = {}
        for name in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
            self.prayers[name] = Prayer.objects.create(name=name)
        self.auth_as_user()

    def _create_record(self, model_type, date_str):
        resp = self.client.post("/api/prayer-time-records/", {
            "masjid": str(self.masjid.masjidID),
            "date": date_str,
            "modelType": model_type,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        return resp.data["ptrID"]

    def test_full_timetable_both_times(self):
        """FULL_TIMETABLE: each prayer has both adhan and iqama times."""
        ptr_id = self._create_record("FULL_TIMETABLE", "2026-03-01")

        for name, prayer in self.prayers.items():
            resp = self.client.post("/api/prayer-times/", {
                "record": ptr_id,
                "prayer_id": prayer.pk,
                "adhan_time": "05:30:00",
                "iqama_time": "05:45:00",
            })
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED, f"Failed for {name}: {resp.data}")
            self.assertIsNotNone(resp.data["adhan_time"])
            self.assertIsNotNone(resp.data["iqama_time"])

        # Verify via nested action
        self.auth_none()
        resp = self.client.get(f"/api/masjids/{self.masjid.masjidID}/prayer_times/")
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["modelType"], "FULL_TIMETABLE")

    def test_iqama_only_schema(self):
        """IQAMA_ONLY: each prayer has only iqama_time, no adhan."""
        ptr_id = self._create_record("IQAMA_ONLY", "2026-03-02")

        for name, prayer in self.prayers.items():
            resp = self.client.post("/api/prayer-times/", {
                "record": ptr_id,
                "prayer_id": prayer.pk,
                "iqama_time": "13:00:00",
            })
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED, f"Failed for {name}")
            self.assertIsNotNone(resp.data["iqama_time"])

    def test_adhan_only_schema(self):
        """ADHAN_ONLY: each prayer has only adhan_time, no iqama."""
        ptr_id = self._create_record("ADHAN_ONLY", "2026-03-03")

        for name, prayer in self.prayers.items():
            resp = self.client.post("/api/prayer-times/", {
                "record": ptr_id,
                "prayer_id": prayer.pk,
                "adhan_time": "04:30:00",
            })
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED, f"Failed for {name}")
            self.assertIsNotNone(resp.data["adhan_time"])

    def test_unknown_schema_no_times_rejected(self):
        """UNKNOWN: a prayer with neither adhan nor iqama should be rejected."""
        ptr_id = self._create_record("UNKNOWN", "2026-03-04")

        resp = self.client.post("/api/prayer-times/", {
            "record": ptr_id,
            "prayer_id": self.prayers["fajr"].pk,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unique_together_prayer_per_record(self):
        """Cannot add the same prayer twice to the same record."""
        ptr_id = self._create_record("FULL_TIMETABLE", "2026-03-05")

        resp = self.client.post("/api/prayer-times/", {
            "record": ptr_id,
            "prayer_id": self.prayers["fajr"].pk,
            "adhan_time": "05:00:00",
            "iqama_time": "05:15:00",
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Duplicate → should fail
        resp = self.client.post("/api/prayer-times/", {
            "record": ptr_id,
            "prayer_id": self.prayers["fajr"].pk,
            "adhan_time": "05:05:00",
            "iqama_time": "05:20:00",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_variable_prayer_times(self):
        """isVariable=True records are accepted normally."""
        self.auth_as_user()
        resp = self.client.post("/api/prayer-time-records/", {
            "masjid": str(self.masjid.masjidID),
            "date": "2026-03-06",
            "modelType": "FULL_TIMETABLE",
            "isVariable": True,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp.data["isVariable"])

    def test_filter_prayer_time_records_by_date(self):
        """API filtering by date works correctly."""
        PrayerTimeRecord.objects.create(
            masjid=self.masjid, date=date(2026, 6, 1), modelType="FULL_TIMETABLE",
        )
        PrayerTimeRecord.objects.create(
            masjid=self.masjid, date=date(2026, 6, 2), modelType="IQAMA_ONLY",
        )
        self.auth_none()
        resp = self.client.get("/api/prayer-time-records/?date=2026-06-01")
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["modelType"], "FULL_TIMETABLE")


# ===========================================================================
# 17.  BUSINESS LOGIC — Badge verification lifecycle
# ===========================================================================

class BadgeVerificationLifecycleTest(TestDataMixin, TestCase):
    """Full badge lifecycle: issue → verify → expire → revoke, auto-deactivation."""

    def _create_badge(self, **kwargs):
        defaults = {"masjid": self.masjid, "issuedBy": self.admin_user}
        defaults.update(kwargs)
        return VerifiedBadge.objects.create(**defaults)

    def _setup_confidence(self, level):
        cr = ConfidenceRecord.objects.create(
            masjid=self.masjid, confidenceLevel=level,
        )
        self.masjid.confidenceRecord = cr
        self.masjid.save()
        return cr

    # ---- Basic validity ----

    def test_active_badge_with_c2_is_valid(self):
        """An active badge with C2 confidence is valid."""
        self._setup_confidence(2)
        badge = self._create_badge()
        self.assertTrue(check_badge_validity(badge))

    def test_active_badge_with_c3_is_valid(self):
        self._setup_confidence(3)
        badge = self._create_badge()
        self.assertTrue(check_badge_validity(badge))

    def test_revoked_badge_is_invalid(self):
        self._setup_confidence(2)
        badge = self._create_badge(isRevoked=True)
        self.assertFalse(check_badge_validity(badge))

    def test_inactive_badge_is_invalid(self):
        self._setup_confidence(2)
        badge = self._create_badge(isActive=False)
        self.assertFalse(check_badge_validity(badge))

    # ---- Auto-deactivation on low confidence ----

    def test_badge_auto_deactivates_on_c1(self):
        """If masjid drops to C1, badge should auto-deactivate."""
        self._setup_confidence(1)
        badge = self._create_badge()
        result = check_badge_validity(badge)
        self.assertFalse(result)
        badge.refresh_from_db()
        self.assertFalse(badge.isActive)

    def test_badge_auto_deactivates_on_c0(self):
        self._setup_confidence(0)
        badge = self._create_badge()
        result = check_badge_validity(badge)
        self.assertFalse(result)
        badge.refresh_from_db()
        self.assertFalse(badge.isActive)

    def test_badge_auto_deactivates_no_confidence_record(self):
        """If masjid has no confidence record at all, badge is invalid."""
        badge = self._create_badge()
        result = check_badge_validity(badge)
        self.assertFalse(result)
        badge.refresh_from_db()
        self.assertFalse(badge.isActive)

    # ---- Expiry ----

    def test_expired_badge_auto_deactivates(self):
        self._setup_confidence(3)
        badge = self._create_badge(
            expiryDate=timezone.now() - timedelta(days=1),
        )
        result = check_badge_validity(badge)
        self.assertFalse(result)
        badge.refresh_from_db()
        self.assertFalse(badge.isActive)

    def test_future_expiry_is_valid(self):
        self._setup_confidence(2)
        badge = self._create_badge(
            expiryDate=timezone.now() + timedelta(days=365),
        )
        self.assertTrue(check_badge_validity(badge))

    # ---- Inactive masjid ----

    def test_badge_deactivates_for_inactive_masjid(self):
        self._setup_confidence(3)
        self.masjid.isActive = False
        self.masjid.save()
        badge = self._create_badge()
        result = check_badge_validity(badge)
        self.assertFalse(result)

    # ---- API verify endpoint integration ----

    def test_verify_endpoint_uses_badge_validity_logic(self):
        """GET /api/verify/{token}/ should use check_badge_validity."""
        self._setup_confidence(1)  # below C2
        badge = self._create_badge()

        resp = self.client.get(f"/api/verify/{badge.token}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["valid"])

        badge.refresh_from_db()
        self.assertFalse(badge.isActive)  # auto-deactivated

    def test_verify_endpoint_valid_badge(self):
        self._setup_confidence(3)
        badge = self._create_badge()
        resp = self.client.get(f"/api/verify/{badge.token}/")
        self.assertTrue(resp.data["valid"])

    def test_verify_updates_last_checked(self):
        self._setup_confidence(2)
        badge = self._create_badge()
        self.assertIsNone(badge.lastCheckedAt)
        self.client.get(f"/api/verify/{badge.token}/")
        badge.refresh_from_db()
        self.assertIsNotNone(badge.lastCheckedAt)

    # ---- Full lifecycle ----

    def test_full_badge_lifecycle(self):
        """Issue → verify valid → confidence drops → verify invalid → revoke."""
        # 1. Setup C3
        cr = self._setup_confidence(3)
        badge = self._create_badge(
            expiryDate=timezone.now() + timedelta(days=365),
        )

        # 2. Valid verification
        self.assertTrue(check_badge_validity(badge))

        # 3. Confidence drops to C1
        cr.confidenceLevel = 1
        cr.save()
        self.masjid.refresh_from_db()

        # 4. Badge now invalid
        self.assertFalse(check_badge_validity(badge))
        badge.refresh_from_db()
        self.assertFalse(badge.isActive)

        # 5. Explicit revoke via API
        self.auth_as_admin()
        resp = self.client.post(f"/api/badges/{badge.badgeID}/revoke/")
        badge.refresh_from_db()
        self.assertTrue(badge.isRevoked)


# ===========================================================================
# 18.  BUSINESS LOGIC — User favourites
# ===========================================================================

class UserFavouritesLogicTest(TestDataMixin, TestCase):
    """Test marking, retrieving, filtering, and removing favourite masjids."""

    def setUp(self):
        super().setUp()
        self.masjid2 = Masjid.objects.create(name="Masjid Al-Huda")
        self.masjid3 = Masjid.objects.create(name="Islamic Center")
        self.user2 = RegularUser.objects.create(
            username="user2", email="user2@test.com"
        )

    def test_mark_favourite(self):
        """User can favourite a masjid via API."""
        self.auth_as_user()
        resp = self.client.post("/api/favourites/", {
            "user": self.regular_user.username,
            "masjid": str(self.masjid.masjidID),
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_mark_multiple_favourites(self):
        """User can favourite multiple different masjids."""
        self.auth_as_user()
        for m in [self.masjid, self.masjid2, self.masjid3]:
            resp = self.client.post("/api/favourites/", {
                "user": self.regular_user.username,
                "masjid": str(m.masjidID),
            })
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            FavouriteMasjid.objects.filter(user=self.regular_user).count(), 3
        )

    def test_duplicate_favourite_prevented(self):
        """Same user + same masjid → 400."""
        FavouriteMasjid.objects.create(user=self.regular_user, masjid=self.masjid)
        self.auth_as_user()
        resp = self.client.post("/api/favourites/", {
            "user": self.regular_user.username,
            "masjid": str(self.masjid.masjidID),
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_different_users_can_favourite_same_masjid(self):
        """Two different users can favourite the same masjid."""
        FavouriteMasjid.objects.create(user=self.regular_user, masjid=self.masjid)
        FavouriteMasjid.objects.create(user=self.user2, masjid=self.masjid)
        self.assertEqual(
            FavouriteMasjid.objects.filter(masjid=self.masjid).count(), 2
        )

    def test_filter_favourites_by_user(self):
        """GET /api/favourites/?user=X returns only that user's favourites."""
        FavouriteMasjid.objects.create(user=self.regular_user, masjid=self.masjid)
        FavouriteMasjid.objects.create(user=self.regular_user, masjid=self.masjid2)
        FavouriteMasjid.objects.create(user=self.user2, masjid=self.masjid)

        self.auth_as_user()
        resp = self.client.get(f"/api/favourites/?user={self.regular_user.username}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data["results"]
        self.assertEqual(len(results), 2)
        for fav in results:
            self.assertEqual(fav["user"], self.regular_user.username)

    def test_filter_favourites_by_masjid(self):
        """GET /api/favourites/?masjid=X returns all users who favourited it."""
        FavouriteMasjid.objects.create(user=self.regular_user, masjid=self.masjid)
        FavouriteMasjid.objects.create(user=self.user2, masjid=self.masjid)
        FavouriteMasjid.objects.create(user=self.regular_user, masjid=self.masjid2)

        self.auth_as_user()
        resp = self.client.get(f"/api/favourites/?masjid={self.masjid.masjidID}")
        results = resp.data["results"]
        self.assertEqual(len(results), 2)

    def test_unfavourite_via_delete(self):
        """DELETE /api/favourites/{id}/ removes the favourite."""
        fav = FavouriteMasjid.objects.create(
            user=self.regular_user, masjid=self.masjid,
        )
        self.auth_as_user()
        resp = self.client.delete(f"/api/favourites/{fav.favID}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FavouriteMasjid.objects.filter(pk=fav.favID).exists())

    def test_unfavourite_requires_auth(self):
        """DELETE /api/favourites/{id}/ → 401 if not authenticated."""
        fav = FavouriteMasjid.objects.create(
            user=self.regular_user, masjid=self.masjid,
        )
        self.auth_none()
        resp = self.client.delete(f"/api/favourites/{fav.favID}/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_favourites_requires_auth(self):
        self.auth_none()
        resp = self.client.get("/api/favourites/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ===========================================================================
# 19.  MANAGEMENT COMMAND — decay_confidence
# ===========================================================================

from django.core.management import call_command
from io import StringIO


class DecayConfidenceCommandTest(TestDataMixin, TestCase):
    """Test the management command runs decay_all_confidence correctly."""

    def test_command_output(self):
        """Running the command prints the count of decayed records."""
        ConfidenceRecord.objects.create(
            masjid=self.masjid, confidenceLevel=3,
            decayDate=timezone.now() - timedelta(days=1),
        )
        out = StringIO()
        call_command("decay_confidence", stdout=out)
        output = out.getvalue()
        self.assertIn("Decayed 1 confidence record(s)", output)

    def test_command_no_overdue(self):
        """Command prints 0 when nothing is overdue."""
        ConfidenceRecord.objects.create(
            masjid=self.masjid, confidenceLevel=3,
            decayDate=timezone.now() + timedelta(days=30),
        )
        out = StringIO()
        call_command("decay_confidence", stdout=out)
        self.assertIn("Decayed 0 confidence record(s)", out.getvalue())
