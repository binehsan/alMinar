import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class AbstractModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# User Profile  (linked to Django auth.User for real login)
# ---------------------------------------------------------------------------

class UserProfile(AbstractModel):
    """
    Every Django auth.User gets a profile.
    `role` distinguishes regular users from masjid admins.
    """

    ROLE_CHOICES = [
        ("user", "Regular User"),
        ("masjid_admin", "Masjid Admin"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


# ---------------------------------------------------------------------------
# Masjid  — NO circular FK.  Confidence / Location point here via OneToOne.
# ---------------------------------------------------------------------------

class Masjid(AbstractModel):
    name = models.CharField(max_length=255)
    masjidID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(blank=True, null=True)
    isActive = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Confidence Record  (OneToOne → Masjid — no circular ref)
# ---------------------------------------------------------------------------

class ConfidenceRecord(AbstractModel):

    CONFIDENCE_LEVELS = [
        (0, "C0 - Community Reported"),
        (1, "C1 - Community Confirmed"),
        (2, "C2 - Masjid Verified"),
        (3, "C3 - Actively Maintained"),
    ]

    # Decay schedule: C3→C2 = 90 days, C2→C1 = 180 days, C1→C0 = 365 days
    DECAY_DAYS = {3: 90, 2: 180, 1: 365}

    crID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    confidenceLevel = models.IntegerField(default=0, choices=CONFIDENCE_LEVELS)
    masjid = models.OneToOneField(
        Masjid, on_delete=models.CASCADE, related_name="confidence_record"
    )
    lastConfirmationDate = models.DateTimeField(auto_now=True)
    decayDate = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.masjid.name} - C{self.confidenceLevel}"


# ---------------------------------------------------------------------------
# Location Record  (OneToOne → Masjid)
# ---------------------------------------------------------------------------

class LocationRecord(AbstractModel):

    countries = [
        "AF - Islamic Republic of Afghanistan",
        "AL - Republic of Albania",
        "DZ - People's Democratic Republic of Algeria",
        "AD - Principality of Andorra",
        "AO - Republic of Angola",
        "AG - Antigua and Barbuda",
        "AR - Argentine Republic",
        "AM - Republic of Armenia",
        "AU - Commonwealth of Australia",
        "AT - Republic of Austria",
        "AZ - Republic of Azerbaijan",
        "BS - Commonwealth of the Bahamas",
        "BH - Kingdom of Bahrain",
        "BD - People's Republic of Bangladesh",
        "BB - Barbados",
        "BY - Republic of Belarus",
        "BE - Kingdom of Belgium",
        "BZ - Belize",
        "BJ - Republic of Benin",
        "BT - Kingdom of Bhutan",
        "BO - Plurinational State of Bolivia",
        "BA - Bosnia and Herzegovina",
        "BW - Republic of Botswana",
        "BR - Federative Republic of Brazil",
        "BN - Brunei Darussalam",
        "BG - Republic of Bulgaria",
        "BF - Burkina Faso",
        "BI - Republic of Burundi",
        "CV - Republic of Cabo Verde",
        "KH - Kingdom of Cambodia",
        "CM - Republic of Cameroon",
        "CA - Canada",
        "CF - Central African Republic",
        "TD - Republic of Chad",
        "CL - Republic of Chile",
        "CN - People's Republic of China",
        "CO - Republic of Colombia",
        "KM - Union of the Comoros",
        "CG - Republic of the Congo",
        "CD - Democratic Republic of the Congo",
        "CR - Republic of Costa Rica",
        "CI - Republic of Côte d'Ivoire",
        "HR - Republic of Croatia",
        "CU - Republic of Cuba",
        "CY - Republic of Cyprus",
        "CZ - Czech Republic",
        "DK - Kingdom of Denmark",
        "DJ - Republic of Djibouti",
        "DM - Commonwealth of Dominica",
        "DO - Dominican Republic",
        "EC - Republic of Ecuador",
        "EG - Arab Republic of Egypt",
        "SV - Republic of El Salvador",
        "GQ - Republic of Equatorial Guinea",
        "ER - State of Eritrea",
        "EE - Republic of Estonia",
        "SZ - Kingdom of Eswatini",
        "ET - Federal Democratic Republic of Ethiopia",
        "FJ - Republic of Fiji",
        "FI - Republic of Finland",
        "FR - French Republic",
        "GA - Gabonese Republic",
        "GM - Republic of the Gambia",
        "GE - Georgia",
        "DE - Federal Republic of Germany",
        "GH - Republic of Ghana",
        "GR - Hellenic Republic",
        "GD - Grenada",
        "GT - Republic of Guatemala",
        "GN - Republic of Guinea",
        "GW - Republic of Guinea-Bissau",
        "GY - Co-operative Republic of Guyana",
        "HT - Republic of Haiti",
        "HN - Republic of Honduras",
        "HU - Hungary",
        "IS - Republic of Iceland",
        "IN - Republic of India",
        "ID - Republic of Indonesia",
        "IR - Islamic Republic of Iran",
        "IQ - Republic of Iraq",
        "IE - Ireland",
        "IL - State of Israel",
        "IT - Italian Republic",
        "JM - Jamaica",
        "JP - Japan",
        "JO - Hashemite Kingdom of Jordan",
        "KZ - Republic of Kazakhstan",
        "KE - Republic of Kenya",
        "KI - Republic of Kiribati",
        "KP - Democratic People's Republic of Korea",
        "KR - Republic of Korea",
        "KW - State of Kuwait",
        "KG - Kyrgyz Republic",
        "LA - Lao People's Democratic Republic",
        "LV - Republic of Latvia",
        "LB - Lebanese Republic",
        "LS - Kingdom of Lesotho",
        "LR - Republic of Liberia",
        "LY - State of Libya",
        "LI - Principality of Liechtenstein",
        "LT - Republic of Lithuania",
        "LU - Grand Duchy of Luxembourg",
        "MG - Republic of Madagascar",
        "MW - Republic of Malawi",
        "MY - Malaysia",
        "MV - Republic of Maldives",
        "ML - Republic of Mali",
        "MT - Republic of Malta",
        "MH - Republic of the Marshall Islands",
        "MR - Republic of Mauritania",
        "MU - Republic of Mauritius",
        "MX - United Mexican States",
        "FM - Federated States of Micronesia",
        "MD - Republic of Moldova",
        "MC - Principality of Monaco",
        "MN - Mongolia",
        "ME - Montenegro",
        "MA - Kingdom of Morocco",
        "MZ - Republic of Mozambique",
        "MM - Republic of the Union of Myanmar",
        "NA - Republic of Namibia",
        "NR - Republic of Nauru",
        "NP - Federal Democratic Republic of Nepal",
        "NL - Kingdom of the Netherlands",
        "NZ - New Zealand",
        "NI - Republic of Nicaragua",
        "NE - Republic of the Niger",
        "NG - Federal Republic of Nigeria",
        "MK - Republic of North Macedonia",
        "NO - Kingdom of Norway",
        "OM - Sultanate of Oman",
        "PK - Islamic Republic of Pakistan",
        "PA - Republic of Panama",
        "PG - Independent State of Papua New Guinea",
        "PY - Republic of Paraguay",
        "PE - Republic of Peru",
        "PH - Republic of the Philippines",
        "PL - Republic of Poland",
        "PT - Portuguese Republic",
        "QA - State of Qatar",
        "RO - Romania",
        "RU - Russian Federation",
        "RW - Republic of Rwanda",
        "SA - Kingdom of Saudi Arabia",
        "RS - Republic of Serbia",
        "SG - Republic of Singapore",
        "ZA - Republic of South Africa",
        "ES - Kingdom of Spain",
        "LK - Democratic Socialist Republic of Sri Lanka",
        "SE - Kingdom of Sweden",
        "CH - Swiss Confederation",
        "SY - Syrian Arab Republic",
        "TH - Kingdom of Thailand",
        "TR - Republic of Türkiye",
        "UA - Ukraine",
        "AE - United Arab Emirates",
        "UK - United Kingdom of Great Britain and Northern Ireland",
        "US - United States of America",
        "VN - Socialist Republic of Viet Nam",
        "YE - Republic of Yemen",
        "ZM - Republic of Zambia",
        "ZW - Republic of Zimbabwe",
    ]

    lrID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    latitude = models.FloatField()
    longitude = models.FloatField()
    masjid = models.OneToOneField(
        Masjid, on_delete=models.CASCADE, related_name="location_record"
    )
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, choices=[(c, c) for c in countries])
    region = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.masjid.name} — {self.city}, {self.country}"


# ---------------------------------------------------------------------------
# Prayer Time Records
# ---------------------------------------------------------------------------

class PrayerTimeRecord(AbstractModel):

    MODEL_TYPE_CHOICES = [
        ("FULL_TIMETABLE", "Full timetable"),
        ("IQAMA_ONLY", "Iqama only"),
        ("ADHAN_ONLY", "Adhan only"),
        ("UNKNOWN", "Unknown"),
    ]

    ptrID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    masjid = models.ForeignKey(
        Masjid, on_delete=models.CASCADE, related_name="prayer_time_records"
    )
    modelType = models.CharField(max_length=20, choices=MODEL_TYPE_CHOICES, default="UNKNOWN")
    isVariable = models.BooleanField(default=False)
    date = models.DateField()
    lastUpdated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("masjid", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.masjid.name} - {self.date}"


class Prayer(AbstractModel):

    PRAYER_CHOICES = [
        ("fajr", "Fajr"),
        ("dhuhr", "Dhuhr"),
        ("asr", "Asr"),
        ("maghrib", "Maghrib"),
        ("isha", "Isha"),
    ]

    name = models.CharField(max_length=10, choices=PRAYER_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()


class PrayerTime(AbstractModel):

    prayerTimeID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(
        PrayerTimeRecord, on_delete=models.CASCADE, related_name="prayers"
    )
    prayer = models.ForeignKey(Prayer, on_delete=models.CASCADE)
    adhan_time = models.TimeField(blank=True, null=True)
    iqama_time = models.TimeField(blank=True, null=True)

    class Meta:
        unique_together = ("record", "prayer")

    def clean(self):
        if not self.adhan_time and not self.iqama_time:
            raise ValidationError(
                "At least one of adhan_time or iqama_time must be provided."
            )

    def __str__(self):
        return f"{self.prayer} - {self.record.masjid.name}"


# ---------------------------------------------------------------------------
# Signal
# ---------------------------------------------------------------------------

class Signal(AbstractModel):

    SIGNAL_TYPES = [
        ("PRAYED", "User prayed here"),
        ("JUMMAH", "Jummah observed"),
        ("ACTIVE", "Masjid confirmed active"),
        ("ADMIN_VERIFY", "Masjid self-verification"),
    ]

    SOURCE_TYPES = [
        ("USER", "Regular user"),
        ("ADMIN", "Masjid admin"),
        ("SYSTEM", "System generated"),
    ]

    signalID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    masjid = models.ForeignKey(Masjid, on_delete=models.CASCADE, related_name="signals")
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="signals"
    )
    signalType = models.CharField(max_length=20, choices=SIGNAL_TYPES)
    sourceType = models.CharField(max_length=10, choices=SOURCE_TYPES, default="USER")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_sourceType_display()}: {self.get_signalType_display()} @ {self.masjid.name}"


# ---------------------------------------------------------------------------
# Verified Badge
# ---------------------------------------------------------------------------

class VerifiedBadge(AbstractModel):
    badgeID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    masjid = models.ForeignKey(Masjid, on_delete=models.CASCADE, related_name="badges")
    issuedBy = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="issued_badges"
    )
    issueDate = models.DateTimeField(auto_now_add=True)
    expiryDate = models.DateTimeField(null=True, blank=True)
    isActive = models.BooleanField(default=True)
    isRevoked = models.BooleanField(default=False)
    lastCheckedAt = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "Active" if self.isActive and not self.isRevoked else "Inactive"
        return f"Badge {self.token} ({status}) - {self.masjid.name}"


# ---------------------------------------------------------------------------
# Masjid Admin Link  (a user who manages a masjid)
# ---------------------------------------------------------------------------

class MasjidAdmin(AbstractModel):
    masjidAdminID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="managed_masjids"
    )
    masjid = models.ForeignKey(
        Masjid, on_delete=models.CASCADE, related_name="masjid_admins"
    )
    verifiedIdentity = models.BooleanField(default=False)
    verifiedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "masjid")

    def __str__(self):
        status = "Verified" if self.verifiedIdentity else "Unverified"
        return f"{self.user.username} → {self.masjid.name} ({status})"


# ---------------------------------------------------------------------------
# Favourite Masjid
# ---------------------------------------------------------------------------

class FavouriteMasjid(AbstractModel):
    favID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favourite_masjids"
    )
    masjid = models.ForeignKey(
        Masjid, on_delete=models.CASCADE, related_name="favourited_by"
    )

    class Meta:
        unique_together = ("user", "masjid")

    def __str__(self):
        return f"{self.user.username} ♥ {self.masjid.name}"


# ---------------------------------------------------------------------------
# Verification Documents  (uploaded by masjid admins for identity proof)
# ---------------------------------------------------------------------------

class VerificationDocument(AbstractModel):
    docID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    masjid_admin_link = models.ForeignKey(
        MasjidAdmin, on_delete=models.CASCADE, related_name="documents"
    )
    document = models.FileField(upload_to="verification_docs/%Y/%m/")
    description = models.CharField(max_length=255, blank=True, default="")
    reviewed = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_documents"
    )
    review_notes = models.TextField(blank=True, default="")

    def __str__(self):
        status = "Approved" if self.approved else ("Pending" if not self.reviewed else "Rejected")
        return f"Doc {str(self.docID)[:8]} — {self.masjid_admin_link.masjid.name} ({status})"
