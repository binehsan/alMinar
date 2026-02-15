from rest_framework import serializers
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


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = ["username", "email", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class RegularUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegularUser
        fields = ["username", "email", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class ConfidenceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfidenceRecord
        fields = [
            "crID",
            "confidenceLevel",
            "masjid",
            "lastConfirmationDate",
            "decayDate",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["crID", "lastConfirmationDate", "created_at", "updated_at"]


class LocationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationRecord
        fields = [
            "lrID",
            "latitude",
            "longitude",
            "masjid",
            "city",
            "country",
            "region",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["lrID", "created_at", "updated_at"]


class MasjidSerializer(serializers.ModelSerializer):
    confidenceRecord = ConfidenceRecordSerializer(read_only=True)
    locationRecord = LocationRecordSerializer(read_only=True)

    class Meta:
        model = Masjid
        fields = [
            "masjidID",
            "name",
            "description",
            "isActive",
            "confidenceRecord",
            "locationRecord",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["masjidID", "created_at", "updated_at"]


class PrayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prayer
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PrayerTimeSerializer(serializers.ModelSerializer):
    prayer = PrayerSerializer(read_only=True)
    prayer_id = serializers.PrimaryKeyRelatedField(
        queryset=Prayer.objects.all(), source="prayer", write_only=True
    )

    class Meta:
        model = PrayerTime
        fields = [
            "prayerTimeID",
            "record",
            "prayer",
            "prayer_id",
            "adhan_time",
            "iqama_time",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["prayerTimeID", "created_at", "updated_at"]

    def validate(self, data):
        if not data.get("adhan_time") and not data.get("iqama_time"):
            raise serializers.ValidationError(
                "At least one of adhan_time or iqama_time must be provided."
            )
        return data


class PrayerTimeRecordSerializer(serializers.ModelSerializer):
    prayers = PrayerTimeSerializer(many=True, read_only=True)

    class Meta:
        model = PrayerTimeRecord
        fields = [
            "ptrID",
            "masjid",
            "modelType",
            "isVariable",
            "date",
            "lastUpdated",
            "prayers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["ptrID", "lastUpdated", "created_at", "updated_at"]


class SignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signal
        fields = [
            "signalID",
            "masjid",
            "user",
            "signalType",
            "sourceType",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["signalID", "created_at", "updated_at"]


class VerifiedBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerifiedBadge
        fields = [
            "badgeID",
            "token",
            "masjid",
            "issuedBy",
            "issueDate",
            "expiryDate",
            "isActive",
            "isRevoked",
            "lastCheckedAt",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["badgeID", "token", "issueDate", "created_at", "updated_at"]


class MasjidAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasjidAdmin
        fields = [
            "masjidAdminID",
            "user",
            "masjid",
            "verifiedIdentity",
            "verifiedAt",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["masjidAdminID", "verifiedAt", "created_at", "updated_at"]


class FavouriteMasjidSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavouriteMasjid
        fields = [
            "favID",
            "user",
            "masjid",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["favID", "created_at", "updated_at"]
