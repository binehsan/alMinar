from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    UserProfile,
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
    VerificationDocument,
)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["role", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile"]
        read_only_fields = ["id"]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=UserProfile.ROLE_CHOICES, default="user"
    )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def create(self, validated_data):
        role = validated_data.pop("role", "user")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        UserProfile.objects.create(user=user, role=role)
        return user


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

class ConfidenceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfidenceRecord
        fields = [
            "crID", "confidenceLevel", "masjid",
            "lastConfirmationDate", "decayDate",
            "created_at", "updated_at",
        ]
        read_only_fields = ["crID", "lastConfirmationDate", "created_at", "updated_at"]


class LocationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationRecord
        fields = [
            "lrID", "latitude", "longitude", "masjid",
            "city", "country", "region",
            "created_at", "updated_at",
        ]
        read_only_fields = ["lrID", "created_at", "updated_at"]


class MasjidSerializer(serializers.ModelSerializer):
    confidence_record = ConfidenceRecordSerializer(read_only=True)
    location_record = LocationRecordSerializer(read_only=True)

    class Meta:
        model = Masjid
        fields = [
            "masjidID", "name", "description", "isActive",
            "confidence_record", "location_record",
            "created_at", "updated_at",
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
            "prayerTimeID", "record",
            "prayer", "prayer_id",
            "adhan_time", "iqama_time",
            "created_at", "updated_at",
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
            "ptrID", "masjid", "modelType", "isVariable",
            "date", "lastUpdated", "prayers",
            "created_at", "updated_at",
        ]
        read_only_fields = ["ptrID", "lastUpdated", "created_at", "updated_at"]


class SignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signal
        fields = [
            "signalID", "masjid", "user",
            "signalType", "sourceType", "description",
            "created_at", "updated_at",
        ]
        read_only_fields = ["signalID", "created_at", "updated_at"]


class VerifiedBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerifiedBadge
        fields = [
            "badgeID", "token", "masjid", "issuedBy",
            "issueDate", "expiryDate",
            "isActive", "isRevoked", "lastCheckedAt",
            "created_at", "updated_at",
        ]
        read_only_fields = ["badgeID", "token", "issueDate", "created_at", "updated_at"]


class MasjidAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasjidAdmin
        fields = [
            "masjidAdminID", "user", "masjid",
            "verifiedIdentity", "verifiedAt",
            "created_at", "updated_at",
        ]
        read_only_fields = ["masjidAdminID", "verifiedAt", "created_at", "updated_at"]


class FavouriteMasjidSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavouriteMasjid
        fields = ["favID", "user", "masjid", "created_at", "updated_at"]
        read_only_fields = ["favID", "created_at", "updated_at"]


class VerificationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationDocument
        fields = [
            "docID", "masjid_admin_link", "document",
            "description", "reviewed", "approved",
            "review_notes", "created_at", "updated_at",
        ]
        read_only_fields = [
            "docID", "reviewed", "approved",
            "review_notes", "created_at", "updated_at",
        ]
