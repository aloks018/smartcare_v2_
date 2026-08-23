from __future__ import annotations

from backend.app.schemas import (
    DataSource,
    Provider,
)


# ============================================================
# PROVIDER DATA
# ============================================================
#
# IMPORTANT:
# Do NOT invent fees, phone numbers, ratings, availability etc.
#
# If the information is not available from your real source,
# keep the field as None.
#
# Replace / extend this list with your actual imported
# healthcare dataset.
# ============================================================


PROVIDERS: list[Provider] = [

    Provider(
        id="gsvm-kanpur",

        name="GSVM Medical College & Hospital",

        provider_type="Hospital",

        ownership="Government",

        specialty="Multi-specialty",

        city="Kanpur",

        district="Kanpur Nagar",

        state="Uttar Pradesh",

        address="Swaroop Nagar, Kanpur, Uttar Pradesh",

        phone=None,

        website=None,

        consultation_fee_inr=None,

        emergency_available=True,

        availability="Emergency service available; verify current OPD timings",

        languages=[
            "Hindi",
            "English"
        ],

        latitude=26.4828,

        longitude=80.3220,

        verified_source="Official/public healthcare source",

        verified=True,
    ),


    Provider(
        id="llr-kanpur",

        name="Lala Lajpat Rai Hospital",

        provider_type="Hospital",

        ownership="Government",

        specialty="General Medicine",

        city="Kanpur",

        district="Kanpur Nagar",

        state="Uttar Pradesh",

        address="Swaroop Nagar, Kanpur, Uttar Pradesh",

        phone=None,

        website=None,

        consultation_fee_inr=None,

        emergency_available=True,

        availability="Emergency service available; verify current timings",

        languages=[
            "Hindi",
            "English"
        ],

        latitude=26.4827,

        longitude=80.3225,

        verified_source="Official/public healthcare source",

        verified=True,
    ),


    Provider(
        id="kgmu-lucknow",

        name="King George's Medical University",

        provider_type="Hospital",

        ownership="Government",

        specialty="Multi-specialty",

        city="Lucknow",

        district="Lucknow",

        state="Uttar Pradesh",

        address="Chowk, Lucknow, Uttar Pradesh",

        phone=None,

        website=None,

        consultation_fee_inr=None,

        emergency_available=True,

        availability="Emergency service available; verify current timings",

        languages=[
            "Hindi",
            "English"
        ],

        latitude=26.8688,

        longitude=80.9157,

        verified_source="Official/public healthcare source",

        verified=True,
    ),

]


# ============================================================
# SPECIALTIES
# ============================================================

HEALTH_PROFESSIONS = [

    "General Medicine",

    "Cardiology",

    "Neurology",

    "Dermatology",

    "Pulmonology",

    "Pediatrics",

    "Orthopedics",

    "Gynecology",

    "ENT",

    "Ophthalmology",

    "Emergency Medicine",

    "Gastroenterology",

]


# ============================================================
# OFFICIAL DATA SOURCES
# ============================================================

OFFICIAL_DATA_SOURCES = [

    DataSource(
        name="data.gov.in",

        url="https://data.gov.in/",

        description=(
            "Government of India open-data platform. "
            "Use verified healthcare datasets."
        ),

        type="government",
    ),

]