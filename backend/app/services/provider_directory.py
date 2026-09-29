from __future__ import annotations

import json
import time
from threading import Lock
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.app.schemas import Provider


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "SmartCareAI/1.0 (+https://smartcare-v2-as.onrender.com/)"
CACHE_SECONDS = 3600
SEARCH_RADIUS_METERS = 10000
MAX_RESULTS = 500

_cache_lock = Lock()
_nominatim_lock = Lock()
_geocode_cache: dict[str, tuple[float, tuple[float, float] | None]] = {}
_facility_cache: dict[str, tuple[float, list[Provider]]] = {}
_last_nominatim_request = 0.0


def _read_json(url: str, *, data: bytes | None = None) -> object:
    request = Request(
        url,
        data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _geocode(location: str) -> tuple[float, float] | None:
    global _last_nominatim_request

    key = " ".join(location.lower().split())
    now = time.monotonic()
    with _cache_lock:
        cached = _geocode_cache.get(key)
        if cached and now - cached[0] < CACHE_SECONDS:
            return cached[1]

    with _nominatim_lock:
        wait = 1.0 - (time.monotonic() - _last_nominatim_request)
        if wait > 0:
            time.sleep(wait)
        _last_nominatim_request = time.monotonic()
        params = urlencode({"q": location, "format": "jsonv2", "limit": 1, "countrycodes": "in"})
        try:
            results = _read_json(f"{NOMINATIM_URL}?{params}")
        except (OSError, ValueError):
            return None

    point = None
    if isinstance(results, list) and results:
        try:
            point = (float(results[0]["lat"]), float(results[0]["lon"]))
        except (KeyError, TypeError, ValueError):
            point = None

    with _cache_lock:
        _geocode_cache[key] = (time.monotonic(), point)
    return point


def _facility_type(tags: dict[str, str]) -> str | None:
    amenity = tags.get("amenity", "").lower()
    healthcare = tags.get("healthcare", "").lower()
    emergency = tags.get("emergency", "").lower()

    if amenity == "pharmacy" or healthcare == "pharmacy":
        return "Pharmacy"
    if amenity in {"doctors", "doctor"} or healthcare == "doctor":
        return "Doctor's office"
    if amenity == "dentist" or healthcare == "dentist":
        return "Dental clinic"
    if amenity == "hospital" or healthcare == "hospital":
        return "Hospital"
    if amenity == "clinic" or healthcare == "clinic":
        return "Clinic"
    if healthcare in {"laboratory", "lab"} or amenity == "laboratory":
        return "Diagnostic laboratory"
    if amenity == "ambulance_station" or emergency == "ambulance_station":
        return "Ambulance service"
    if healthcare == "physiotherapist":
        return "Physiotherapy"
    return None


def _provider_from_element(element: dict, origin: tuple[float, float]) -> Provider | None:
    tags = element.get("tags") or {}
    facility_type = _facility_type(tags)
    if not facility_type:
        return None

    name = tags.get("name") or tags.get("name:en") or tags.get("brand")
    if not name:
        return None

    center = element.get("center") or element
    try:
        latitude = float(center["lat"])
        longitude = float(center["lon"])
    except (KeyError, TypeError, ValueError):
        return None

    address_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
        tags.get("addr:postcode"),
    ]
    address = ", ".join(part for part in address_parts if part) or None
    specialty = tags.get("healthcare:speciality") or tags.get("healthcare:specialty") or tags.get("speciality")
    if specialty:
        specialty = ", ".join(part.strip() for part in specialty.split(";") if part.strip())

    operator_type = tags.get("operator:type", "").lower()
    ownership = "Government" if operator_type in {"government", "public"} else "Unknown"
    emergency = tags.get("emergency", "").lower() in {"yes", "ambulance_station"}
    distance_km = _distance_km(origin[0], origin[1], latitude, longitude)
    osm_type = element.get("type", "node")
    osm_id = element.get("id")

    return Provider(
        id=f"osm-{osm_type}-{osm_id}",
        name=name,
        provider_type=facility_type,
        ownership=ownership,
        specialty=specialty,
        city=tags.get("addr:city"),
        district=tags.get("addr:district"),
        state=tags.get("addr:state", "India"),
        address=address,
        phone=tags.get("contact:phone") or tags.get("phone"),
        website=f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
        emergency_available=emergency,
        latitude=latitude,
        longitude=longitude,
        verified_source="OpenStreetMap contributors",
        verified=False,
        distance_km=distance_km,
    )


def _distance_km(start_latitude: float, start_longitude: float, end_latitude: float, end_longitude: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    latitude_delta = radians(end_latitude - start_latitude)
    longitude_delta = radians(end_longitude - start_longitude)
    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(start_latitude))
        * cos(radians(end_latitude))
        * sin(longitude_delta / 2) ** 2
    )
    return 6371 * 2 * asin(sqrt(haversine))


def facilities_near(location: str) -> list[Provider]:
    """Fetch named, mapped health facilities near an end-user supplied Indian location."""

    if not location.strip():
        return []

    origin = _geocode(location.strip())
    if origin is None:
        return []

    cache_key = f"{origin[0]:.4f},{origin[1]:.4f}"
    now = time.monotonic()
    with _cache_lock:
        cached = _facility_cache.get(cache_key)
        if cached and now - cached[0] < CACHE_SECONDS:
            return [provider.model_copy(deep=True) for provider in cached[1]]

    latitude, longitude = origin
    query = (
        f"[out:json][timeout:18];("
        f"nwr(around:{SEARCH_RADIUS_METERS},{latitude},{longitude})"
        "[amenity~\"^(hospital|clinic|doctors|doctor|pharmacy|dentist|laboratory|ambulance_station)$\"];"
        f"nwr(around:{SEARCH_RADIUS_METERS},{latitude},{longitude})"
        "[healthcare~\"^(hospital|clinic|doctor|pharmacy|laboratory|lab|dentist|physiotherapist)$\"];"
        f"nwr(around:{SEARCH_RADIUS_METERS},{latitude},{longitude})"
        "[emergency=ambulance_station];);"
        f"out center tags {MAX_RESULTS};"
    )
    payload = None
    for attempt in range(2):
        try:
            payload = _read_json(OVERPASS_URL, data=urlencode({"data": query}).encode("utf-8"))
            break
        except (OSError, ValueError):
            if attempt == 0:
                time.sleep(0.5)
    if payload is None:
        if cached:
            return [provider.model_copy(deep=True) for provider in cached[1]]
        return []

    if not isinstance(payload, dict):
        return []

    providers = []
    seen: set[str] = set()
    for element in payload.get("elements", []):
        provider = _provider_from_element(element, origin)
        if provider and provider.id not in seen:
            providers.append(provider)
            seen.add(provider.id)

    with _cache_lock:
        _facility_cache[cache_key] = (time.monotonic(), providers)
    return [provider.model_copy(deep=True) for provider in providers]