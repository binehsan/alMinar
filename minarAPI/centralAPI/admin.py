from django.contrib import admin
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


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class ConfidenceRecordInline(admin.StackedInline):
    model = ConfidenceRecord
    extra = 0


class LocationRecordInline(admin.StackedInline):
    model = LocationRecord
    extra = 0


class PrayerTimeInline(admin.TabularInline):
    model = PrayerTime
    extra = 0
    readonly_fields = ("prayerTimeID",)


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


# ---------------------------------------------------------------------------
# Model Admin Classes
# ---------------------------------------------------------------------------

@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "created_at")
    search_fields = ("username", "email")


@admin.register(RegularUser)
class RegularUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "created_at")
    search_fields = ("username", "email")


@admin.register(Masjid)
class MasjidModelAdmin(admin.ModelAdmin):
    list_display = ("name", "masjidID", "isActive", "confidenceRecord", "created_at")
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
    list_display = ("masjid", "token", "isActive", "isRevoked", "issueDate", "expiryDate")
    list_filter = ("isActive", "isRevoked")
    search_fields = ("masjid__name",)
    readonly_fields = ("badgeID", "token", "issueDate")


@admin.register(MasjidAdmin)
class MasjidAdminAdmin(admin.ModelAdmin):
    list_display = ("user", "masjid", "verifiedIdentity", "verifiedAt")
    list_filter = ("verifiedIdentity",)
    search_fields = ("user__username", "masjid__name")
    readonly_fields = ("masjidAdminID",)


@admin.register(FavouriteMasjid)
class FavouriteMasjidAdmin(admin.ModelAdmin):
    list_display = ("user", "masjid", "created_at")
    search_fields = ("user__username", "masjid__name")
    readonly_fields = ("favID",)
