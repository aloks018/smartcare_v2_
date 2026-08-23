from __future__ import annotations

from backend.app.schemas import Symptom


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

    "chest pain": (
        "chest pain",
        "chest discomfort",
    ),

    "breathing difficulty": (
        "breathing difficulty",
        "difficulty breathing",
        "shortness of breath",
        "breathlessness",
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

    found: dict[str, Symptom] = {}

    for canonical, aliases in SYMPTOM_ALIASES.items():

        for alias in aliases:

            if alias in lower:

                confidence = (
                    0.95
                    if alias == canonical
                    else 0.80
                )

                found[canonical] = Symptom(
                    name=canonical,

                    evidence=alias,

                    confidence=confidence,
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

    emergency_terms = [

        "emergency",

        "ambulance",

        "unconscious",

        "cannot breathe",

        "can't breathe",

        "severe chest pain",

    ]

    if any(
        term in lower
        for term in emergency_terms
    ):

        return "emergency_navigation"


    doctor_terms = [

        "find doctor",

        "doctor near",

        "doctor in",

        "doctor chahiye",

        "cardiologist near",

    ]

    if any(
        term in lower
        for term in doctor_terms
    ):

        return "doctor_search"


    facility_terms = [

        "hospital",

        "clinic",

        "government hospital",

        "private hospital",

        "facility",

    ]

    if any(
        term in lower
        for term in facility_terms
    ):

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

    symptom_names = {
        symptom.name
        for symptom in symptoms
    }

    for specialty, required in SPECIALTY_RULES:

        if symptom_names.intersection(
            required
        ):

            return specialty

    return "General Medicine"


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