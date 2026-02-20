from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

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


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = (
        "username", "email", "first_name", "last_name", "is_staff", "get_role",
    )

    @admin.display(description="Role")
    def get_role(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.get_role_display() if profile else "-"


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class ConfidenceRecordInline(admin.StackedInline):
    model = ConfidenceRecord
    extra = 0
    readonly_fields = ("crID", "lastConfirmationDate")


class LocationRecordInline(admin.StackedInline):
    model = LocationRecord
    extra = 0
    readonly_fields = ("lrID",)


class SignalInline(admin.TabularInline):
    model = Signal
    extra = 0
    readonly_fields = ("signalID", "created_at")


class VerifiedBadgeInline(admin.TabularInline):
    model = VerifiedBadge
    extra = 0
    readonly_fields = ("badgeID", "token", "issueDate")


class MasjidAdminInline(admin.TabularInline):
    model = MasjidAdmin
    extra = 0
    readonly_fields = ("masjidAdminID",)


class PrayerTimeInline(admin.TabularInline):
    model = PrayerTime
    extra = 0
    readonly_fields = ("prayerTimeID",)


class VerificationDocumentInline(admin.TabularInline):
    model = VerificationDocument
    extra = 0
    readonly_fields = ("docID", "created_at")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")


@admin.register(Masjid)
class MasjidModelAdmin(admin.ModelAdmin):
    list_display = ("name", "masjidID", "isActive", "get_confidence", "created_at")
    list_filter = ("isActive",)
    search_fields = ("name", "description")
    readonly_fields = ("masjidID",)
    inlines = [
        ConfidenceRecordInline,
        LocationRecordInline,
        SignalInline,
        VerifiedBadgeInline,
        MasjidAdminInline,
    ]

    @admin.display(description="Confidence")
    def get_confidence(self, obj):
        cr = getattr(obj, "confidence_record", None)
        return f"C{cr.confidenceLevel}" if cr else "-"


@admin.register(ConfidenceRecord)
class ConfidenceRecordAdmin(admin.ModelAdmin):
    list_display = ("masjid", "confidenceLevel", "lastConfirmationDate", "decayDate")
    list_filter = ("confidenceLevel",)
    search_fields = ("masjid__name",)
    readonly_fields = ("crID", "lastConfirmationDate")


@admin.register(LocationRecord)
class LocationRecordAdmin(admin.ModelAdmin):
    list_display = ("masjid", "city", "country", "latitude", "longitude")
    list_filter = ("country",)
    search_fields = ("masjid__name", "city", "region")
    readonly_fields = ("lrID",)


@admin.register(PrayerTimeRecord)
class PrayerTimeRecordAdmin(admin.ModelAdmin):
    list_display = ("masjid", "date", "modelType", "isVariable", "lastUpdated")
    list_filter = ("modelType", "isVariable", "date")
    search_fields = ("masjid__name",)
    readonly_fields = ("ptrID", "lastUpdated")
    inlines = [PrayerTimeInline]


@admin.register(Prayer)
class PrayerAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(PrayerTime)
class PrayerTimeAdmin(admin.ModelAdmin):
    list_display = ("prayer", "record", "adhan_time", "iqama_time")
    list_filter = ("prayer",)
    readonly_fields = ("prayerTimeID",)


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ("masjid", "signalType", "sourceType", "user", "created_at")
    list_filter = ("signalType", "sourceType")
    search_fields = ("masjid__name", "user__username")
    readonly_fields = ("signalID",)


@admin.register(VerifiedBadge)
class VerifiedBadgeAdmin(admin.ModelAdmin):
    list_display = (
        "masjid", "token", "isActive", "isRevoked", "issueDate", "expiryDate",
    )
    list_filter = ("isActive", "isRevoked")
    search_fields = ("masjid__name",)
    readonly_fields = ("badgeID", "token", "issueDate")


@admin.register(MasjidAdmin)
class MasjidAdminAdmin(admin.ModelAdmin):
    list_display = ("user", "masjid", "verifiedIdentity", "verifiedAt")
    list_filter = ("verifiedIdentity",)
    search_fields = ("user__username", "masjid__name")
    readonly_fields = ("masjidAdminID",)
    inlines = [VerificationDocumentInline]


@admin.register(FavouriteMasjid)
class FavouriteMasjidAdmin(admin.ModelAdmin):
    list_display = ("user", "masjid", "created_at")
    search_fields = ("user__username", "masjid__name")
    readonly_fields = ("favID",)


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "masjid_admin_link", "description", "reviewed", "approved", "created_at",
    )
    list_filter = ("reviewed", "approved")
    search_fields = (
        "masjid_admin_link__masjid__name",
        "masjid_admin_link__user__username",
    )
    readonly_fields = ("docID", "created_at")

    def save_model(self, request, obj, form, change):
        """When a doc is approved, auto-upgrade masjid to C3."""
        super().save_model(request, obj, form, change)
        if obj.approved and obj.reviewed:
            from .services import approve_verification_document
            approve_verification_document(obj)
