from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

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
    MasjidAdmin,
    FavouriteMasjid,
)
from .serializers import (
    AdminUserSerializer,
    RegularUserSerializer,
    MasjidSerializer,
    ConfidenceRecordSerializer,
    LocationRecordSerializer,
    PrayerTimeRecordSerializer,
    PrayerSerializer,
    PrayerTimeSerializer,
    SignalSerializer,
    VerifiedBadgeSerializer,
    MasjidAdminSerializer,
    FavouriteMasjidSerializer,
)
from .services import process_signal, check_badge_validity


# ---------------------------------------------------------------------------
# User ViewSets
# ---------------------------------------------------------------------------

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = AdminUser.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]


class RegularUserViewSet(viewsets.ModelViewSet):
    queryset = RegularUser.objects.all()
    serializer_class = RegularUserSerializer
    permission_classes = [IsAuthenticated]


# ---------------------------------------------------------------------------
# Masjid ViewSet
# ---------------------------------------------------------------------------

class MasjidViewSet(viewsets.ModelViewSet):
    queryset = Masjid.objects.select_related(
        "confidenceRecord", "locationRecord"
    ).all()
    serializer_class = MasjidSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["isActive"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve", "prayer_times", "signals", "badges"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["get"])
    def prayer_times(self, request, pk=None):
        """GET /api/masjids/{id}/prayer_times/ — latest prayer times for a masjid."""
        masjid = self.get_object()
        records = PrayerTimeRecord.objects.filter(masjid=masjid).prefetch_related("prayers__prayer")
        serializer = PrayerTimeRecordSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def signals(self, request, pk=None):
        """GET /api/masjids/{id}/signals/ — signals for a masjid."""
        masjid = self.get_object()
        sigs = Signal.objects.filter(masjid=masjid).order_by("-created_at")
        serializer = SignalSerializer(sigs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def badges(self, request, pk=None):
        """GET /api/masjids/{id}/badges/ — badges for a masjid."""
        masjid = self.get_object()
        badges = VerifiedBadge.objects.filter(masjid=masjid)
        serializer = VerifiedBadgeSerializer(badges, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Confidence Record ViewSet
# ---------------------------------------------------------------------------

class ConfidenceRecordViewSet(viewsets.ModelViewSet):
    queryset = ConfidenceRecord.objects.select_related("masjid").all()
    serializer_class = ConfidenceRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["confidenceLevel", "masjid"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]


# ---------------------------------------------------------------------------
# Location Record ViewSet
# ---------------------------------------------------------------------------

class LocationRecordViewSet(viewsets.ModelViewSet):
    queryset = LocationRecord.objects.select_related("masjid").all()
    serializer_class = LocationRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["country", "city", "masjid"]
    search_fields = ["city", "region", "country"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]


# ---------------------------------------------------------------------------
# Prayer ViewSets
# ---------------------------------------------------------------------------

class PrayerViewSet(viewsets.ReadOnlyModelViewSet):
    """Lookup table — read-only. Fajr, Dhuhr, Asr, Maghrib, Isha."""
    queryset = Prayer.objects.all()
    serializer_class = PrayerSerializer
    permission_classes = [AllowAny]


class PrayerTimeRecordViewSet(viewsets.ModelViewSet):
    queryset = PrayerTimeRecord.objects.select_related("masjid").prefetch_related(
        "prayers__prayer"
    ).all()
    serializer_class = PrayerTimeRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["masjid", "modelType", "date"]
    ordering_fields = ["date"]
    ordering = ["-date"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]


class PrayerTimeViewSet(viewsets.ModelViewSet):
    queryset = PrayerTime.objects.select_related("record", "prayer").all()
    serializer_class = PrayerTimeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["record", "prayer"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]


# ---------------------------------------------------------------------------
# Signal ViewSet
# ---------------------------------------------------------------------------

class SignalViewSet(viewsets.ModelViewSet):
    queryset = Signal.objects.select_related("masjid", "user").all()
    serializer_class = SignalSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["masjid", "signalType", "sourceType", "user"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Save the signal, then run confidence-upgrade logic."""
        signal = serializer.save()
        process_signal(signal)


# ---------------------------------------------------------------------------
# Verified Badge ViewSet
# ---------------------------------------------------------------------------

class VerifiedBadgeViewSet(viewsets.ModelViewSet):
    queryset = VerifiedBadge.objects.select_related("masjid", "issuedBy").all()
    serializer_class = VerifiedBadgeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["masjid", "isActive", "isRevoked"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAdminUser()]

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def revoke(self, request, pk=None):
        """POST /api/badges/{id}/revoke/ — revoke a badge."""
        badge = self.get_object()
        badge.isActive = False
        badge.isRevoked = True
        badge.save()
        return Response(VerifiedBadgeSerializer(badge).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def verify_badge(request, token):
    """
    Public endpoint: GET /api/verify/{token}/
    Used by masjid websites to confirm badge validity.
    """
    try:
        badge = VerifiedBadge.objects.select_related("masjid").get(token=token)
    except VerifiedBadge.DoesNotExist:
        return Response(
            {"valid": False, "detail": "Badge not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    badge.lastCheckedAt = timezone.now()
    badge.save(update_fields=["lastCheckedAt"])

    is_valid = check_badge_validity(badge)

    return Response({
        "valid": is_valid,
        "masjid": badge.masjid.name,
        "masjidID": str(badge.masjid.masjidID),
        "issuedAt": badge.issueDate,
        "expiresAt": badge.expiryDate,
    })


# ---------------------------------------------------------------------------
# Masjid Admin ViewSet
# ---------------------------------------------------------------------------

class MasjidAdminViewSet(viewsets.ModelViewSet):
    queryset = MasjidAdmin.objects.select_related("user", "masjid").all()
    serializer_class = MasjidAdminSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["masjid", "user", "verifiedIdentity"]
    permission_classes = [IsAuthenticated]


# ---------------------------------------------------------------------------
# Favourite Masjid ViewSet
# ---------------------------------------------------------------------------

class FavouriteMasjidViewSet(viewsets.ModelViewSet):
    serializer_class = FavouriteMasjidSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user", "masjid"]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavouriteMasjid.objects.select_related("user", "masjid").all()
