from __future__ import annotations

from copy import deepcopy
from math import asin, cos, radians, sin, sqrt

from backend.app.data.providers import PROVIDERS
from backend.app.schemas import Provider


LOCATION_POINTS: dict[str, tuple[float, float]] = {
    "kanpur": (26.4499, 80.3319),
    "kanpur nagar": (26.4499, 80.3319),
    "lucknow": (26.8467, 80.9462),
    "varanasi": (25.3176, 82.9739),
    "prayagraj": (25.4358, 81.8463),
    "agra": (27.1767, 78.0081),
    "meerut": (28.9845, 77.7064),
    "noida": (28.5355, 77.3910),
    "uttar pradesh": (26.8467, 80.9462),
}


def _location_point(location: str | None) -> tuple[float, float] | None:
    normalized = (location or "").strip().lower()
    if not normalized:
        return None

    for name, point in LOCATION_POINTS.items():
        if name in normalized:
            return point

    return None


def _distance_km(
    start_latitude: float,
    start_longitude: float,
    end_latitude: float | None,
    end_longitude: float | None,
) -> float | None:
    if end_latitude is None or end_longitude is None:
        return None

    latitude_delta = radians(end_latitude - start_latitude)
    longitude_delta = radians(end_longitude - start_longitude)
    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(start_latitude))
        * cos(radians(end_latitude))
        * sin(longitude_delta / 2) ** 2
    )

    return 6371 * 2 * asin(sqrt(haversine))


def _score_provider(
    provider: Provider,
    query: str,
    location: str | None,
    specialty: str | None,
    ownership: str | None,
    budget_max_inr: float | None,
    max_distance_km: float | None,
) -> tuple[float, list[str]]:
    score = 20.0
    reasons: list[str] = []
    haystack = " ".join(
        filter(
            None,
            [
                provider.name,
                provider.provider_type,
                provider.specialty,
                provider.city,
                provider.district,
                provider.state,
            ],
        )
    ).lower()
    tokens = [token for token in query.lower().replace("&", " ").split() if len(token) > 2]
    matched_tokens = [token for token in tokens if token in haystack]

    if matched_tokens:
        score += min(44, 12 * len(matched_tokens))
        reasons.append("Matches your healthcare search")

    if specialty:
        score += 22
        reasons.append(f"Suitable for {specialty}")

    if ownership:
        score += 10
        reasons.append(f"Matches {ownership.lower()} care preference")

    if location and provider.distance_km is not None:
        if provider.distance_km <= 15:
            score += 18
            reasons.append("Located close to your selected area")
        elif provider.distance_km <= 60:
            score += 9
            reasons.append("Located within the selected region")

    if provider.emergency_available:
        score += 4
        reasons.append("Emergency service listed")

    if provider.verified:
        score += 4
        reasons.append("Public-source verification available")

    if budget_max_inr is not None and provider.consultation_fee_inr is None:
        reasons.append("Consultation fee should be confirmed with the provider")

    if max_distance_km is not None and provider.distance_km is None:
        reasons.append("Distance should be confirmed with the provider")

    return min(score, 100), reasons[:4]


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

    query = (query or "").strip()

    candidates = []

    user_point = _location_point(location)

    # ========================================================
    # IMPORTANT:
    # When AI already detected a specialty, don't require
    # the provider's name to match the entire patient sentence.
    #
    # Example:
    # "Mujhe fever aur khansi hai"
    #
    # should NOT be required to match:
    # "GSVM Medical College"
    # ========================================================

    for original in PROVIDERS:

        provider = deepcopy(original)

        # ----------------------------------------------------
        # Ownership filter
        # ----------------------------------------------------

        if ownership:

            if (
                provider.ownership.lower()
                != ownership.lower()
            ):
                continue

        # ----------------------------------------------------
        # Location
        # ----------------------------------------------------

        if user_point:

            provider.distance_km = _distance_km(
                user_point[0],
                user_point[1],
                provider.latitude,
                provider.longitude,
            )

        # ----------------------------------------------------
        # Distance filter
        # ----------------------------------------------------

        if (
            max_distance_km is not None
            and provider.distance_km is not None
        ):

            if provider.distance_km > max_distance_km:
                continue

        # ----------------------------------------------------
        # Specialty filter
        # ----------------------------------------------------

        if specialty:

            requested = specialty.lower().strip()

            provider_specialty = (
                provider.specialty or ""
            ).lower()

            # Multi-specialty hospital can satisfy
            # any specialist request.
            if (
                requested not in provider_specialty
                and
                provider_specialty not in requested
                and
                "multi-specialty" not in provider_specialty
                and
                not (
                    requested == "emergency medicine"
                    and provider.emergency_available
                )
            ):
                continue

        # ----------------------------------------------------
        # Budget
        # ----------------------------------------------------

        if (
            budget_max_inr is not None
            and provider.consultation_fee_inr is not None
        ):

            if provider.consultation_fee_inr > budget_max_inr:
                continue

        # ----------------------------------------------------
        # Calculate AI score
        # ----------------------------------------------------

        (
            provider.match_score,
            provider.match_reasons
        ) = _score_provider(

            provider,

            query,

            location,

            specialty,

            ownership,

            budget_max_inr,

            max_distance_km,
        )

        candidates.append(provider)

    # ========================================================
    # SORT
    # ========================================================

    if sort == "distance":

        candidates.sort(
            key=lambda provider:
                provider.distance_km
                if provider.distance_km is not None
                else float("inf")
        )

    elif sort == "fee_low":

        candidates.sort(
            key=lambda provider:
                provider.consultation_fee_inr
                if provider.consultation_fee_inr is not None
                else float("inf")
        )

    else:

        candidates.sort(
            key=lambda provider: (
                provider.match_score
                if provider.match_score is not None
                else 0,

                provider.verified,

                -(
                    provider.distance_km
                    if provider.distance_km is not None
                    else 999999
                ),
            ),
            reverse=True,
        )

    return candidates[:limit]
