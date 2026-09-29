"""Fast, local search over the versioned SmartCare medical navigation catalog.

This module deliberately performs transparent keyword matching. It is a
navigation layer, not a diagnostic engine, and can later be replaced or
augmented by embeddings, a vector index, or validated clinical models without
changing the public API routes.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CATALOG_FILES = (
    "specialties.json",
    "subspecialties.json",
    "symptoms.json",
    "conditions.json",
    "treatments.json",
    "medical_keywords.json",
)
STOP_WORDS = {
    "a", "an", "and", "are", "can", "doctor", "for", "have", "i", "in",
    "is", "me", "my", "need", "near", "of", "or", "please", "the", "to",
    "want", "with",
}
KIND_WEIGHTS = {
    "specialty": 8,
    "condition": 7,
    "symptom": 6,
    "subspecialty": 5,
    "treatment": 4,
    "related": 3,
}


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def _tokens(value: str) -> set[str]:
    return {token for token in _normalize(value).split() if len(token) > 2 and token not in STOP_WORDS}


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    """Load and index the JSON files once per application process."""

    loaded: dict[str, list[dict[str, Any]]] = {}
    for filename in CATALOG_FILES:
        path = DATA_DIR / filename
        with path.open(encoding="utf-8") as source:
            loaded[path.stem] = json.load(source)

    return {
        **loaded,
        "specialty_by_id": {row["id"]: row for row in loaded["specialties"]},
        "subspecialty_by_id": {row["id"]: row for row in loaded["subspecialties"]},
        "symptom_by_id": {row["id"]: row for row in loaded["symptoms"]},
        "condition_by_id": {row["id"]: row for row in loaded["conditions"]},
        "treatment_by_id": {row["id"]: row for row in loaded["treatments"]},
    }


def catalog_stats() -> dict[str, int]:
    catalog = load_catalog()
    counts = {name: len(catalog[name]) for name in (
        "specialties", "subspecialties", "symptoms", "conditions", "treatments", "medical_keywords",
    )}
    counts["total_records"] = sum(counts.values())
    return counts


def list_specialties(category: str | None = None) -> list[dict[str, str]]:
    normalized_category = _normalize(category or "")
    rows = load_catalog()["specialties"]
    result = [
        {
            "id": row["id"],
            "name": row["name"],
            "parent_category": row["parent_category"],
            "description": row["description"],
        }
        for row in rows
        if not normalized_category or _normalize(row["parent_category"]) == normalized_category
    ]
    return sorted(result, key=lambda row: row["name"])


def specialty_detail(specialty_id: str) -> dict[str, Any] | None:
    catalog = load_catalog()
    row = catalog["specialty_by_id"].get(specialty_id)
    if not row:
        return None

    def resolve(key: str, lookup_key: str) -> list[dict[str, Any]]:
        return [catalog[lookup_key][item_id] for item_id in row[key] if item_id in catalog[lookup_key]]

    return {
        "id": row["id"],
        "name": row["name"],
        "parent_category": row["parent_category"],
        "description": row["description"],
        "when_to_consult": row["when_to_consult"],
        "subspecialties": resolve("subspecialty_ids", "subspecialty_by_id"),
        "common_symptoms": resolve("common_symptom_ids", "symptom_by_id"),
        "related_conditions": resolve("related_condition_ids", "condition_by_id"),
        "common_treatments": resolve("treatment_ids", "treatment_by_id"),
    }


def _fallback_id(name: str | None) -> str | None:
    if not name:
        return None
    normalized = _normalize(name)
    for specialty in load_catalog()["specialties"]:
        if _normalize(specialty["name"]) == normalized:
            return specialty["id"]
    return None


def search_medical_catalog(
    query: str,
    *,
    limit: int = 5,
    fallback_specialty: str | None = None,
) -> list[dict[str, Any]]:
    """Return specialty recommendations for a free-text health enquiry."""

    normalized_query = _normalize(query)
    query_tokens = _tokens(query)
    if not normalized_query and not fallback_specialty:
        return []

    catalog = load_catalog()
    scores: dict[str, int] = defaultdict(int)
    matched_terms: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for keyword in catalog["medical_keywords"]:
        term = _normalize(keyword["normalized_term"])
        term_tokens = _tokens(term)
        exact_phrase = len(term) >= 4 and term in normalized_query
        token_match = len(term_tokens) == 1 and bool(term_tokens.intersection(query_tokens))
        if not exact_phrase and not token_match:
            continue

        kind = keyword["kind"]
        points = KIND_WEIGHTS.get(kind, 2)
        if exact_phrase and len(term_tokens) > 1:
            points += 2
        for specialty_id in keyword["specialty_ids"]:
            scores[specialty_id] += points
            matched_terms[specialty_id].append((str(keyword["term"]), kind))

    fallback_id = _fallback_id(fallback_specialty)
    if fallback_id:
        scores[fallback_id] = max(scores[fallback_id], 1)

    results: list[dict[str, Any]] = []
    for specialty_id, score in scores.items():
        detail = specialty_detail(specialty_id)
        if not detail:
            continue
        matches = matched_terms[specialty_id]
        matched_by_kind: dict[str, list[str]] = defaultdict(list)
        for term, kind in matches:
            if term not in matched_by_kind[kind]:
                matched_by_kind[kind].append(term)

        results.append({
            "specialty_id": specialty_id,
            "specialty_name": detail["name"],
            "parent_category": detail["parent_category"],
            "description": detail["description"],
            "when_to_consult": detail["when_to_consult"],
            "related_subspecialties": [row["name"] for row in detail["subspecialties"][:4]],
            "matching_symptoms": matched_by_kind["symptom"][:5],
            "matching_conditions": matched_by_kind["condition"][:5],
            "matching_keywords": [term for term, _ in matches][:8],
            "relevance": min(100, 25 + score * 4),
        })

    return sorted(
        results,
        key=lambda row: (row["relevance"], row["specialty_name"]),
        reverse=True,
    )[:max(1, min(limit, 12))]
