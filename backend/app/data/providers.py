from __future__ import annotations

from backend.app.schemas import (
    DataSource,
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

DATA_SOURCES = [

    DataSource(
        name="OpenStreetMap contributors",

        url="https://www.openstreetmap.org/copyright",

        description=(
            "Location-based facility listings are queried from OpenStreetMap. "
            "Listings are community-mapped, may be incomplete, and are not clinically verified."
        ),

        type="Open map data · ODbL",
    ),

]