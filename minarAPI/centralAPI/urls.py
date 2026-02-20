from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    register_user,
    current_user,
    MasjidViewSet,
    ConfidenceRecordViewSet,
    LocationRecordViewSet,
    PrayerTimeRecordViewSet,
    PrayerViewSet,
    PrayerTimeViewSet,
    SignalViewSet,
    VerifiedBadgeViewSet,
    MasjidAdminViewSet,
    FavouriteMasjidViewSet,
    VerificationDocumentViewSet,
    verify_badge,
)

router = DefaultRouter()
router.register(r"masjids", MasjidViewSet, basename="masjid")
router.register(r"confidence-records", ConfidenceRecordViewSet, basename="confidence-record")
router.register(r"location-records", LocationRecordViewSet, basename="location-record")
router.register(r"prayer-time-records", PrayerTimeRecordViewSet, basename="prayer-time-record")
router.register(r"prayers", PrayerViewSet, basename="prayer")
router.register(r"prayer-times", PrayerTimeViewSet, basename="prayer-time")
router.register(r"signals", SignalViewSet, basename="signal")
router.register(r"badges", VerifiedBadgeViewSet, basename="badge")
router.register(r"masjid-admins", MasjidAdminViewSet, basename="masjid-admin")
router.register(r"favourites", FavouriteMasjidViewSet, basename="favourite")
router.register(r"verification-docs", VerificationDocumentViewSet, basename="verification-doc")

urlpatterns = [
    # Auth
    path("register/", register_user, name="api-register"),
    path("me/", current_user, name="api-me"),

    # Public badge verification
    path("verify/<uuid:token>/", verify_badge, name="verify-badge"),

    # DRF router
    path("", include(router.urls)),
]
