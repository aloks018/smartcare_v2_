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