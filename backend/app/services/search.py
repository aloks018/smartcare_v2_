
from __future__ import annotations

from pathlib import Path
from math import asin, cos, radians, sin, sqrt

import pandas as pd

from backend.app.schemas import Provider


# ============================================================
# DEMO PROVIDER DATASET
# ============================================================

DATA_DIR = (
    Path(__file__).resolve().parents[2] / "data"
)

PROVIDERS_FILE = DATA_DIR / "providers.csv"


# ============================================================
# SPECIALTY NORMALIZATION
# ============================================================

SPECIALTY_ALIASES = {
    "cardiology": "Cardiology",
    "cardiologist": "Cardiology",

    "dermatology": "Dermatology",
    "dermatologist": "Dermatology",

    "gastroenterology": "Gastroenterology",
    "gastroenterologist": "Gastroenterology",

    "orthopedics": "Orthopedics",
    "orthopedic": "Orthopedics",

    "pediatrics": "Pediatrics",
    "paediatrics": "Pediatrics",
    "pediatrician": "Pediatrics",

    "obstetrics & gynecology": "Obstetrics & Gynecology",
    "obstetrics and gynecology": "Obstetrics & Gynecology",
    "gynecology": "Obstetrics & Gynecology",
    "gynaecology": "Obstetrics & Gynecology",

    "general medicine": "General Medicine",
    "general": "General Medicine",

    "emergency medicine": "Emergency Medicine",
}


# ============================================================
# LOAD DEMO PROVIDERS
# ============================================================

def load_demo_providers() -> list[Provider]:
    """
    Load healthcare providers from the project's
    existing providers.csv file.
    """

    if not PROVIDERS_FILE.exists():
        return []

    try:
        df = pd.read_csv(PROVIDERS_FILE).fillna("")
    except Exception:
        return []

    providers: list[Provider] = []

    for _, row in df.iterrows():

        specialty = str(
            row.get("specialty", "")
        ).strip()

        fee_value = row.get(
            "consultation_fee_inr",
            ""
        )

        distance_value = row.get(
            "distance_km",
            ""
        )

        try:
            fee = (
                float(fee_value)
                if str(fee_value).strip()
                else None
            )
        except (ValueError, TypeError):
            fee = None

        try:
            distance = (
                float(distance_value)
                if str(distance_value).strip()
                else None
            )
        except (ValueError, TypeError):
            distance = None

        verified_value = str(
            row.get("verified", "")
        ).strip().lower()

        provider = Provider(
            id=str(row.get("id", "")),

            name=str(
                row.get("name", "Healthcare Provider")
            ),

            provider_type=str(
                row.get("type", "Hospital")
            ),

            ownership=str(
                row.get("ownership", "Unknown")
            ),

            specialty=specialty or None,

            city=str(
                row.get("city", "")
            ) or None,

            district=str(
                row.get("district", "")
            ) or None,

            state="",

            address=None,

            phone=None,

            website=None,

            consultation_fee_inr=fee,

            emergency_available=(
                specialty.lower()
                == "emergency medicine"
            ),

            distance_km=distance,

            verified_source="SmartCare demo dataset",

            verified=(
                verified_value
                in {
                    "true",
                    "yes",
                    "verified",
                }
            ),

            match_score=None,

            match_reasons=[],
        )

        providers.append(provider)

    return providers


# ============================================================
# SPECIALTY NORMALIZATION
# ============================================================

def normalize_specialty(
    specialty: str | None,
) -> str | None:

    if not specialty:
        return None

    normalized = (
        specialty
        .strip()
        .lower()
    )

    return SPECIALTY_ALIASES.get(
        normalized,
        specialty.strip(),
    )


# ============================================================
# FACILITY TYPE
# ============================================================

def normalize_provider_type(
    provider_type: str | None,
) -> str | None:

    if not provider_type:
        return None

    value = (
        provider_type
        .strip()
        .lower()
    )

    mapping = {
        "hospital": "Hospital",
        "clinic": "Clinic",
        "doctor": "Doctor",
        "doctor's office": "Doctor",
    }

    return mapping.get(
        value,
        provider_type.strip(),
    )


# ============================================================
# DISTANCE
# ============================================================

def _distance_km(
    start_latitude: float,
    start_longitude: float,
    end_latitude: float | None,
    end_longitude: float | None,
) -> float | None:

    if (
        end_latitude is None
        or end_longitude is None
    ):
        return None

    latitude_delta = radians(
        end_latitude - start_latitude
    )

    longitude_delta = radians(
        end_longitude - start_longitude
    )

    haversine = (
        sin(latitude_delta / 2) ** 2
        +
        cos(radians(start_latitude))
        *
        cos(radians(end_latitude))
        *
        sin(longitude_delta / 2) ** 2
    )

    return (
        6371
        * 2
        * asin(sqrt(haversine))
    )


# ============================================================
# PROVIDER SCORING
# ============================================================

def _score_provider(
    provider: Provider,
    query: str,
    location: str | None,
    specialty: str | None,
    ownership: str | None,
    budget_max_inr: float | None,
    max_distance_km: float | None,
) -> tuple[float, list[str]]:

    score = 0.0
    reasons: list[str] = []

    query_terms = _query_terms(query)
    searchable_text = _provider_search_text(provider)
    matched_query_terms = [
        term
        for term in query_terms
        if term in searchable_text
    ]

    if matched_query_terms:
        score += min(30, 10 * len(matched_query_terms))
        reasons.append("Matches your provider search")

    normalized_specialty = normalize_specialty(
        specialty
    )

    # --------------------------------------------------------
    # SPECIALTY MATCH
    # --------------------------------------------------------

    if normalized_specialty:

        provider_specialty = normalize_specialty(
            provider.specialty
        )

        if (
            provider_specialty
            == normalized_specialty
        ):

            score += 60

            reasons.append(
                f"Matches {normalized_specialty}"
            )

    # --------------------------------------------------------
    # LOCATION MATCH
    # --------------------------------------------------------

    if location:

        location_lower = (
            location.lower()
        )

        city = (
            provider.city or ""
        ).lower()

        district = (
            provider.district or ""
        ).lower()

        if (
            location_lower in city
            or location_lower in district
            or city in location_lower
        ):

            score += 20

            reasons.append(
                "Matches selected location"
            )

    # --------------------------------------------------------
    # PROVIDER TYPE
    # --------------------------------------------------------

    if provider.provider_type:

        score += 5

        reasons.append(
            f"Healthcare provider: "
            f"{provider.provider_type}"
        )

    # --------------------------------------------------------
    # OWNERSHIP
    # --------------------------------------------------------

    if ownership:

        if (
            provider.ownership.lower()
            == ownership.lower()
        ):

            score += 10

            reasons.append(
                f"Matches {ownership} preference"
            )

    # --------------------------------------------------------
    # DISTANCE
    # --------------------------------------------------------

    if provider.distance_km is not None:

        if provider.distance_km <= 5:

            score += 5

            reasons.append(
                "Nearby provider"
            )

        elif provider.distance_km <= 10:

            score += 3

            reasons.append(
                "Within nearby area"
            )

    # --------------------------------------------------------
    # BUDGET
    # --------------------------------------------------------

    if budget_max_inr is not None:

        if (
            provider.consultation_fee_inr
            is not None
            and
            provider.consultation_fee_inr
            <= budget_max_inr
        ):

            score += 5

            reasons.append(
                "Within selected budget"
            )

    return (
        min(score, 100),
        reasons,
    )


def _query_terms(query: str) -> list[str]:
    ignored_terms = {
        "a", "an", "and", "at", "care", "doctor", "doctors",
        "find", "for", "in", "my", "near", "of", "provider",
        "providers", "service", "services", "the", "to", "with",
    }
    terms = []
    for value in query.casefold().replace("&", " ").split():
        term = SPECIALTY_ALIASES.get(value, value).casefold()
        if len(term) > 2 and term not in ignored_terms:
            terms.append(term)
    return terms


def _provider_search_text(provider: Provider) -> str:
    return " ".join(
        value or ""
        for value in (
            provider.name,
            provider.provider_type,
            provider.ownership,
            provider.specialty,
            provider.city,
            provider.district,
        )
    ).casefold()


# ============================================================
# MAIN PROVIDER SEARCH
# ============================================================

def search_providers(
    query: str = "",
    location: str | None = None,
    specialty: str | None = None,
    ownership: str | None = None,
    budget_max_inr: float | None = None,
    max_distance_km: float | None = None,
    sort: str = "recommended",
    limit: int = 12,
) -> list[Provider]:

    normalized_specialty = normalize_specialty(
        specialty
    )

    # ========================================================
    # 1. FIRST SEARCH DEMO DATASET
    # ========================================================

    candidates = load_demo_providers()

    # ========================================================
    # 2. SPECIALTY FILTER
    # ========================================================

    if normalized_specialty:

        specialty_matches = [
            provider
            for provider in candidates
            if normalize_specialty(
                provider.specialty
            )
            == normalized_specialty
        ]

        candidates = specialty_matches

    # ========================================================
    # 3. LOCATION FILTER
    # ========================================================

    if location and location.strip():

        location_lower = (
            location.strip().lower()
        )

        location_matches = [
            provider
            for provider in candidates
            if (
                location_lower
                in (provider.city or "").lower()
                or
                location_lower
                in (provider.district or "").lower()
                or
                (provider.city or "").lower()
                in location_lower
            )
        ]

        candidates = location_matches

    # ========================================================
    # 4. OWNERSHIP FILTER
    # ========================================================

    if ownership and ownership.strip():

        ownership_matches = [
            provider
            for provider in candidates
            if provider.ownership.lower()
            == ownership.lower()
        ]

        candidates = ownership_matches

    # ========================================================
    # 5. BUDGET FILTER
    # ========================================================

    if budget_max_inr is not None:

        candidates = [
            provider
            for provider in candidates
            if (
                provider.consultation_fee_inr
                is not None
                and provider.consultation_fee_inr <= budget_max_inr
            )
        ]

    # ========================================================
    # 6. DISTANCE FILTER
    # ========================================================

    if max_distance_km is not None:

        candidates = [
            provider
            for provider in candidates
            if (
                provider.distance_km is not None
                and provider.distance_km <= max_distance_km
            )
        ]

    query_terms = _query_terms(query)
    if query_terms:
        query_matches = [
            provider
            for provider in candidates
            if all(
                term in _provider_search_text(provider)
                for term in query_terms
            )
        ]
        if query_matches:
            candidates = query_matches
        elif not any((location, specialty, ownership, budget_max_inr is not None, max_distance_km is not None)):
            candidates = []

    # ========================================================
    # 7. SCORE RESULTS
    # ========================================================

    for provider in candidates:

        score, reasons = _score_provider(
            provider=provider,
            query=query,
            location=location,
            specialty=normalized_specialty,
            ownership=ownership,
            budget_max_inr=budget_max_inr,
            max_distance_km=max_distance_km,
        )

        provider.match_score = score
        provider.match_reasons = reasons

    # ========================================================
    # 8. SORT
    # ========================================================

    if sort == "distance":

        candidates.sort(
            key=lambda provider:
                provider.distance_km
                if provider.distance_km
                is not None
                else float("inf")
        )

    elif sort == "fee_low":

        candidates.sort(
            key=lambda provider:
                provider.consultation_fee_inr
                if provider.consultation_fee_inr
                is not None
                else float("inf")
        )

    else:

        candidates.sort(
            key=lambda provider: (
                -(provider.match_score or 0),
                provider.distance_km
                if provider.distance_km
                is not None
                else float("inf"),
            )
        )

    # ========================================================
    # 9. RETURN
    # ========================================================

    return candidates[:limit]