from django.db import models

# Create your models here.

class AbstractModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AbstractUserModel(AbstractModel):
    username = models.CharField(max_length=255, primary_key=True)
    email = models.EmailField(unique=True)

    class Meta:
        abstract = True

class AdminUser(AbstractUserModel):
    pass

class RegularUser(AbstractUserModel):
    pass

class Masjid(AbstractModel):
    name = models.CharField(max_length=255)
    masjidID = models.AutoField(primary_key=True)
    description = models.TextField(blank=True, null=True)
    isActive = models.BooleanField(default=True)
    confidenceRecord = models.ForeignKey('ConfidenceRecord', on_delete=models.CASCADE, null=True, blank=True)
    locationRecord = models.ForeignKey('LocationRecord', on_delete=models.CASCADE, null=True, blank=True)


class ConfidenceRecord(AbstractModel):
    crID = models.AutoField(primary_key=True)
    # Confidence Levels: 0 (User Reported), 1 (Community Verified), 2 (Masjid Verified - Maintained), 3 (Masjid Verified - not Maintained)
    confidenceLevel = models.IntegerField(default=0)
    masjid = models.ForeignKey(Masjid, on_delete=models.CASCADE)
    lastConfirmationDate = models.DateTimeField(auto_now=True)
    decayDate = models.DateTimeField(null=True, blank=True)

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
    "MR - Islamic Republic of Mauritania",
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
    "ZW - Republic of Zimbabwe"
]
    lrID = models.AutoField(primary_key=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    masjid = models.ForeignKey(Masjid, on_delete=models.CASCADE)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.OptionsField(choices=countries)
    region = models.CharField(max_length=255, blank=True, null=True)


class PrayerTimeRecord(AbstractModel):

    ptrID = models.AutoField(primary_key=True)

    masjid = models.ForeignKey(
        Masjid,
        on_delete=models.CASCADE,
        related_name="prayer_time_records"
    )

    # Date this set of prayer times applies to
    date = models.DateField()

    lastUpdated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("masjid", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.masjid.name} - {self.date}"


from django.core.exceptions import ValidationError


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

    prayerTimeID = models.AutoField(primary_key=True)

    record = models.ForeignKey(
        PrayerTimeRecord,
        on_delete=models.CASCADE,
        related_name="prayers"
    )

    prayer = models.ForeignKey(
        Prayer,
        on_delete=models.CASCADE
    )

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


class Signal(AbstractModel):
    signalID = models.AutoField(primary_key=True)
    masjid = models.ForeignKey(Masjid, on_delete=models.CASCADE)
    user = models.ForeignKey(RegularUser, on_delete=models.CASCADE)
    signalType = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    

    
class VerifiedBadge(AbstractModel):
    badgeID = models.AutoField(primary_key=True)
    masjid = models.ForeignKey(Masjid, on_delete=models.CASCADE)
    issuedBy = models.ForeignKey(AdminUser, on_delete=models.CASCADE)
    issueDate = models.DateTimeField(auto_now_add=True)
    expiryDate = models.DateTimeField(null=True, blank=True)


class FavouriteMasjid(AbstractModel):
    favID = models.AutoField(primary_key=True)
    user = models.ForeignKey(RegularUser, on_delete=models.CASCADE)
    masjid = models.ForeignKey(Masjid, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "masjid")



