from __future__ import annotations

import re

from backend.app.schemas import Symptom
from backend.app.services.medical_catalog import load_catalog, search_medical_catalog


NEGATION_BEFORE = re.compile(
    r"\b(?:no|not|don't|dont|doesn't|doesnt|without|denies|denied|nahi|nahin)\b(?:\W+\w+){0,3}\W*$",
    re.IGNORECASE,
)
NEGATION_AFTER = re.compile(r"^\W*(?:nahi|nahin)\b", re.IGNORECASE)


def is_negated_mention(text: str, start: int, end: int) -> bool:
    prefix = text[max(0, start - 48):start]
    suffix = text[end:end + 24]
    return bool(NEGATION_BEFORE.search(prefix) or NEGATION_AFTER.match(suffix))


# ============================================================
# SYMPTOM ALIASES
# ============================================================

SYMPTOM_ALIASES = {

    "fever": (
        "fever",
        "temperature",
    ),

    "cough": (
        "cough",
    ),

    "headache": (
        "headache",
        "head pain",
    ),

    "chest discomfort": (
        "chest pain",
        "chest discomfort",
    ),

    "breathing difficulty": (
        "breathing difficulty",
        "difficulty breathing",
        "shortness of breath",
        "breathlessness",
        "cannot breathe",
        "can't breathe",
        "trouble breathing",
        "unable to breathe",
    ),

    "abdominal pain": (
        "abdominal pain",
        "stomach pain",
    ),

    "vomiting": (
        "vomiting",
        "vomit",
    ),

    "diarrhea": (
        "diarrhea",
        "loose motion",
    ),

    "dizziness": (
        "dizziness",
    ),

    "rash": (
        "rash",
        "skin rash",
    ),

    "joint pain": (
        "joint pain",
    ),

    "palpitations": (
        "palpitations",
        "heart racing",
    ),
}


# ============================================================
# SPECIALTY RULES
# ============================================================

SPECIALTY_RULES = [

    (
        "Cardiology",
        {
            "chest pain",
            "palpitations",
        }
    ),

    (
        "Pulmonology",
        {
            "breathing difficulty",
            "shortness of breath",
            "cough",
        }
    ),

    (
        "Neurology",
        {
            "headache",
            "dizziness",
        }
    ),

    (
        "Dermatology",
        {
            "rash",
        }
    ),

    (
        "Gastroenterology",
        {
            "abdominal pain",
            "vomiting",
            "diarrhea",
        }
    ),

    (
        "Orthopedics",
        {
            "joint pain",
        }
    ),
]


# ============================================================
# EXTRACT SYMPTOMS
# ============================================================

def extract_symptoms(
    text: str
) -> list[Symptom]:

    if not text:
        return []

    lower = text.lower()

    aliases_by_name = {name: list(aliases) for name, aliases in SYMPTOM_ALIASES.items()}
    for catalog_symptom in load_catalog()["symptoms"]:
        canonical = catalog_symptom["name"]
        aliases = aliases_by_name.setdefault(canonical, [])
        for alias in catalog_symptom.get("aliases", []):
            if alias not in aliases:
                aliases.append(alias)

    found: dict[str, Symptom] = {}

    for canonical, aliases in aliases_by_name.items():

        for alias in aliases:

            match = re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", lower)

            if match and not is_negated_mention(lower, match.start(), match.end()):

                found[canonical] = Symptom(
                    name=canonical,

                    evidence=alias,
                )

                break

    return list(found.values())


# ============================================================
# INTENT CLASSIFICATION
# ============================================================

def classify_intent(
    text: str,
    symptoms: list[Symptom]
) -> str:

    lower = text.lower()

    child_terms = ["child", "baby", "bacche", "bache", "बच्चे", "बच्चा", "बच्चे को"]
    if any(term in lower for term in child_terms) and "fever" in lower:
        return "child_fever"
    if any(term in lower for term in child_terms) and "cough" in lower:
        return "child_cough"

    ambulance_terms = ["ambulance", "paramedic", "108", "112"]
    if any(term in lower for term in ambulance_terms):
        return "ambulance_search"

    emergency_terms = [
        "emergency",
        "unconscious",
        "cannot breathe",
        "can't breathe",
        "severe chest pain",
    ]
    if any(term in lower for term in emergency_terms):
        return "emergency_navigation"

    pharmacy_terms = ["pharmacy", "chemist", "medical store", "medicine shop", "dawai ki dukan"]
    if any(term in lower for term in pharmacy_terms):
        return "pharmacy_search"

    diagnostic_terms = ["diagnostic lab", "laboratory", "blood test centre", "blood test center", "pathology lab", "test centre", "test center"]
    if any(term in lower for term in diagnostic_terms):
        return "diagnostic_service_search"

    doctor_terms = [
        "find doctor",
        "doctor near",
        "doctor in",
        "doctor chahiye",
        "cardiologist near",
    ]
    if any(term in lower for term in doctor_terms):
        return "doctor_search"

    facility_terms = ["hospital", "clinic", "government hospital", "private hospital", "facility"]
    if any(term in lower for term in facility_terms):
        return "facility_search"

    if symptoms:
        return "symptom_help"

    return "general_health_search"


# ============================================================
# SPECIALTY PREDICTION
# ============================================================

def predict_specialty(
    symptoms: list[Symptom]
) -> str:
    if not symptoms:
        return "General Medicine"

    matches = search_medical_catalog(
        " ".join(symptom.name for symptom in symptoms),
        limit=1,
    )
    return matches[0]["specialty_name"] if matches else "General Medicine"


# ============================================================
# EXPLANATION
# ============================================================

def recommendation_reasons(
    symptoms: list[Symptom],
    specialty: str,
) -> list[str]:

    if not symptoms:

        return [
            (
                "No clear symptom entity was "
                "extracted. General Medicine may "
                "be a reasonable initial care area."
            )
        ]

    reasons = []

    for symptom in symptoms[:5]:

        reasons.append(
            f"You mentioned: {symptom.name}"
        )

    reasons.append(
        (
            f"The extracted symptom pattern "
            f"maps to the {specialty} care area."
        )
    )

    return reasons