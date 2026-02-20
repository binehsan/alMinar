from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import (
    UserProfile,
    Masjid,
    LocationRecord,
    ConfidenceRecord,
    VerifiedBadge,
    MasjidAdmin,
    FavouriteMasjid,
    Signal,
    VerificationDocument,
    PrayerTimeRecord,
    PrayerTime,
    Prayer,
)


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

def home(request):
    masjid_count = Masjid.objects.filter(isActive=True).count()
    country_count = LocationRecord.objects.values("country").distinct().count()
    verified_count = ConfidenceRecord.objects.filter(confidenceLevel__gte=2).count()
    featured = (
        Masjid.objects.filter(isActive=True)
        .select_related("confidence_record", "location_record")
        .order_by("-created_at")[:6]
    )
    return render(request, "frontend/home.html", {
        "masjid_count": masjid_count,
        "country_count": country_count,
        "verified_count": verified_count,
        "featured": featured,
    })


def explore(request):
    return render(request, "frontend/explore.html")


def masjid_detail(request, masjid_id):
    masjid = get_object_or_404(
        Masjid.objects.select_related("confidence_record", "location_record"),
        pk=masjid_id,
    )
    # Latest prayer time record
    prayer_record = (
        PrayerTimeRecord.objects.filter(masjid=masjid)
        .prefetch_related("prayers__prayer")
        .order_by("-date")
        .first()
    )
    prayer_times = []
    if prayer_record:
        for pt in prayer_record.prayers.select_related("prayer").order_by("prayer__name"):
            prayer_times.append(pt)

    # Recent signals
    recent_signals = Signal.objects.filter(masjid=masjid).order_by("-created_at")[:10]

    # Badges
    badges = VerifiedBadge.objects.filter(masjid=masjid, isActive=True, isRevoked=False)

    return render(request, "frontend/masjid_detail.html", {
        "masjid": masjid,
        "prayer_record": prayer_record,
        "prayer_times": prayer_times,
        "recent_signals": recent_signals,
        "badges": badges,
    })


def verify_page(request, token):
    return render(request, "frontend/verify.html", {"token": token})


def about(request):
    return render(request, "frontend/about.html")


def report_page(request):
    """Report / add a masjid — available to all logged-in users."""
    if not request.user.is_authenticated:
        return render(request, "frontend/report.html", {"auth_required": True})

    profile = getattr(request.user, "profile", None)
    is_admin = profile and profile.role == "masjid_admin"

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        city = request.POST.get("city", "").strip()
        country = request.POST.get("country", "")
        region = request.POST.get("region", "").strip()
        lat = request.POST.get("latitude", "")
        lng = request.POST.get("longitude", "")

        if not name or not city or not country:
            messages.error(request, "Name, city and country are required.")
            return redirect("report")

        try:
            lat = float(lat)
            lng = float(lng)
        except (ValueError, TypeError):
            messages.error(request, "Valid latitude and longitude are required.")
            return redirect("report")

        # Duplicate location check (within ~100m)
        from django.db.models import Q
        nearby = LocationRecord.objects.filter(
            latitude__range=(lat - 0.001, lat + 0.001),
            longitude__range=(lng - 0.001, lng + 0.001),
        )
        if nearby.exists():
            messages.error(
                request,
                "A masjid already exists at or very near this location. "
                "Please check the Explore page first."
            )
            return redirect("report")

        masjid = Masjid.objects.create(
            name=name,
            description=description or None,
            isActive=True,
        )
        LocationRecord.objects.create(
            masjid=masjid, latitude=lat, longitude=lng,
            city=city, country=country, region=region or None,
        )
        ConfidenceRecord.objects.create(masjid=masjid, confidenceLevel=0)

        # Create initial signal
        Signal.objects.create(
            masjid=masjid, user=request.user,
            signalType="ACTIVE", sourceType="ADMIN" if is_admin else "USER",
            description="Reported via form",
        )

        if is_admin:
            MasjidAdmin.objects.get_or_create(
                user=request.user, masjid=masjid,
                defaults={"verifiedIdentity": False},
            )

        messages.success(
            request,
            f'Masjid "{name}" reported successfully! '
            + ("It starts at C0." if not is_admin else "It starts at C0 — upload a verification document in your dashboard to upgrade.")
        )
        return redirect("masjid-detail", masjid_id=masjid.masjidID)

    return render(request, "frontend/report.html", {
        "is_admin": is_admin,
        "countries": LocationRecord.countries,
    })


# ---------------------------------------------------------------------------
# Auth — server-side login / register / logout
# ---------------------------------------------------------------------------

def login_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # ensure profile exists
            UserProfile.objects.get_or_create(user=user, defaults={"role": "user"})
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "frontend/login.html")


def register_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm", "")
        role = request.POST.get("accountType", "user")

        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if User.objects.filter(username=username).exists():
            errors.append("Username already taken.")
        if User.objects.filter(email=email).exists():
            errors.append("Email already registered.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, "frontend/register.html", {
                "form_username": username,
                "form_email": email,
                "form_role": role,
            })

        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        UserProfile.objects.create(user=user, role=role)
        login(request, user)
        messages.success(request, "Account created successfully!")
        return redirect("dashboard")

    return render(request, "frontend/register.html")


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


# ---------------------------------------------------------------------------
# Dashboard — routes to user or masjid-admin dashboard
# ---------------------------------------------------------------------------

@login_required(login_url="/login/")
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user, defaults={"role": "user"}
    )
    if profile.role == "masjid_admin":
        return _masjid_admin_dashboard(request, profile)
    return _user_dashboard(request, profile)


def _user_dashboard(request, profile):
    """Dashboard for regular users."""
    favourites = FavouriteMasjid.objects.filter(
        user=request.user
    ).select_related("masjid__confidence_record", "masjid__location_record")

    signals = Signal.objects.filter(user=request.user).select_related("masjid").order_by("-created_at")[:10]

    all_masjids = Masjid.objects.filter(isActive=True).select_related(
        "location_record"
    ).order_by("name")

    return render(request, "frontend/dashboard_user.html", {
        "profile": profile,
        "favourites": favourites,
        "signals": signals,
        "all_masjids": all_masjids,
    })


def _masjid_admin_dashboard(request, profile):
    """Dashboard for masjid admins."""
    admin_links = MasjidAdmin.objects.filter(
        user=request.user
    ).select_related("masjid__confidence_record", "masjid__location_record")

    docs = VerificationDocument.objects.filter(
        masjid_admin_link__user=request.user
    ).select_related("masjid_admin_link__masjid").order_by("-created_at")

    all_masjids = Masjid.objects.filter(isActive=True).select_related(
        "location_record"
    ).order_by("name")

    return render(request, "frontend/dashboard_masjid_admin.html", {
        "profile": profile,
        "admin_links": admin_links,
        "docs": docs,
        "all_masjids": all_masjids,
    })


# ---------------------------------------------------------------------------
# Dashboard actions
# ---------------------------------------------------------------------------

@login_required(login_url="/login/")
def add_favourite(request):
    """POST — add a masjid to favourites."""
    if request.method == "POST":
        masjid_id = request.POST.get("masjid_id")
        masjid = get_object_or_404(Masjid, pk=masjid_id)
        FavouriteMasjid.objects.get_or_create(user=request.user, masjid=masjid)
        messages.success(request, f"Added {masjid.name} to your favourites.")
    return redirect("dashboard")


@login_required(login_url="/login/")
def remove_favourite(request, fav_id):
    """POST — remove a favourite."""
    if request.method == "POST":
        fav = get_object_or_404(FavouriteMasjid, pk=fav_id, user=request.user)
        fav.delete()
        messages.success(request, "Removed from favourites.")
    return redirect("dashboard")


@login_required(login_url="/login/")
def send_signal(request):
    """POST — send a signal for a masjid."""
    if request.method == "POST":
        masjid_id = request.POST.get("masjid_id")
        signal_type = request.POST.get("signal_type", "PRAYED")
        masjid = get_object_or_404(Masjid, pk=masjid_id)

        profile = getattr(request.user, "profile", None)
        source = "ADMIN" if profile and profile.role == "masjid_admin" else "USER"

        signal = Signal.objects.create(
            masjid=masjid,
            user=request.user,
            signalType=signal_type,
            sourceType=source,
            description=request.POST.get("description", ""),
        )
        from .services import process_signal
        process_signal(signal)
        messages.success(request, f"Signal sent for {masjid.name}!")
    return redirect("dashboard")


@login_required(login_url="/login/")
def upload_document(request):
    """POST — masjid admin uploads a verification document."""
    if request.method == "POST":
        link_id = request.POST.get("masjid_admin_link_id")
        link = get_object_or_404(MasjidAdmin, pk=link_id, user=request.user)
        doc_file = request.FILES.get("document")
        desc = request.POST.get("description", "")

        if not doc_file:
            messages.error(request, "Please select a file to upload.")
            return redirect("dashboard")

        # Validate file size (5 MB max)
        if doc_file.size > 5 * 1024 * 1024:
            messages.error(request, "File size must be under 5 MB.")
            return redirect("dashboard")

        VerificationDocument.objects.create(
            masjid_admin_link=link,
            document=doc_file,
            description=desc,
        )
        messages.success(request, "Document uploaded successfully! It will be reviewed by our team.")
    return redirect("dashboard")


@login_required(login_url="/login/")
def add_masjid(request):
    """POST — masjid admin adds a new masjid from the dashboard."""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        city = request.POST.get("city", "").strip()
        country = request.POST.get("country", "")
        region = request.POST.get("region", "").strip()
        lat = request.POST.get("latitude", "")
        lng = request.POST.get("longitude", "")

        if not name or not city or not country:
            messages.error(request, "Name, city and country are required.")
            return redirect("dashboard")

        try:
            lat = float(lat)
            lng = float(lng)
        except (ValueError, TypeError):
            messages.error(request, "Valid latitude and longitude are required.")
            return redirect("dashboard")

        # Duplicate location check (± 0.001 ≈ ~111 m)
        duplicate = LocationRecord.objects.filter(
            latitude__gte=lat - 0.001, latitude__lte=lat + 0.001,
            longitude__gte=lng - 0.001, longitude__lte=lng + 0.001,
        ).select_related("masjid").first()
        if duplicate:
            messages.error(
                request,
                f'A masjid already exists near this location: "{duplicate.masjid.name}". '
                "Please send a signal to the existing masjid instead of adding a duplicate.",
            )
            return redirect("dashboard")

        profile = getattr(request.user, "profile", None)
        is_admin = profile and profile.role == "masjid_admin"

        masjid = Masjid.objects.create(
            name=name,
            description=description or None,
            isActive=is_admin,
        )
        LocationRecord.objects.create(
            masjid=masjid,
            latitude=lat,
            longitude=lng,
            city=city,
            country=country,
            region=region or None,
        )
        ConfidenceRecord.objects.create(
            masjid=masjid,
            confidenceLevel=0,
        )

        if is_admin:
            MasjidAdmin.objects.get_or_create(
                user=request.user, masjid=masjid,
                defaults={"verifiedIdentity": False}
            )
            # Admin masjid starts at C0 — must be verified by 3+ users
            # or admin uploads verification document to upgrade
            Signal.objects.create(
                masjid=masjid,
                user=request.user,
                signalType="ADMIN_VERIFY",
                sourceType="ADMIN",
                description="Masjid admin direct submission",
            )
            messages.success(request, f'Masjid "{name}" added! It starts at C0 — upload a verification document in your dashboard to upgrade.')
        else:
            Signal.objects.create(
                masjid=masjid,
                user=request.user,
                signalType="ACTIVE",
                sourceType="USER",
                description="Community report",
            )
            messages.success(request, f'Masjid "{name}" reported! It needs community verification.')

    return redirect("dashboard")


@login_required(login_url="/login/")
def upload_prayer_times(request):
    """POST — masjid admin uploads prayer times for one of their masjids."""
    if request.method == "POST":
        from datetime import date as dt_date

        masjid_id = request.POST.get("masjid_id")
        masjid = get_object_or_404(Masjid, pk=masjid_id)

        # Verify the user manages this masjid
        if not MasjidAdmin.objects.filter(user=request.user, masjid=masjid).exists():
            messages.error(request, "You do not manage this masjid.")
            return redirect("dashboard")

        model_type = request.POST.get("model_type", "UNKNOWN")
        record_date = request.POST.get("date", "")
        try:
            record_date = dt_date.fromisoformat(record_date)
        except (ValueError, TypeError):
            record_date = dt_date.today()

        # Get or update existing record for this date
        record, _ = PrayerTimeRecord.objects.update_or_create(
            masjid=masjid, date=record_date,
            defaults={"modelType": model_type, "isVariable": False},
        )

        # Ensure Prayer objects exist
        prayer_names = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
        for pname in prayer_names:
            Prayer.objects.get_or_create(name=pname)

        saved_count = 0
        for pname in prayer_names:
            adhan = request.POST.get(f"{pname}_adhan", "").strip()
            iqama = request.POST.get(f"{pname}_iqama", "").strip()

            if not adhan and not iqama:
                # Skip prayers not provided — flexible, not required
                continue

            prayer_obj = Prayer.objects.get(name=pname)
            PrayerTime.objects.update_or_create(
                record=record, prayer=prayer_obj,
                defaults={
                    "adhan_time": adhan if adhan else None,
                    "iqama_time": iqama if iqama else None,
                },
            )
            saved_count += 1

        if saved_count > 0:
            messages.success(request, f"Prayer times updated for {masjid.name} ({record_date}).")
        else:
            messages.warning(request, "No prayer times were provided. Please enter at least one.")

    return redirect("dashboard")
