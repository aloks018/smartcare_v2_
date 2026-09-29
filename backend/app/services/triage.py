from __future__ import annotations

from backend.app.schemas import (
    Symptom,
    TriageAssessment,
)


# ============================================================
# EMERGENCY PATTERNS
# ============================================================

EMERGENCY_PATTERNS = (

    "severe chest pain",

    "chest pain and difficulty breathing",
    "chest pain and breathing difficulty",

    "cannot breathe",

    "can't breathe",

    "unconscious",

    "heavy bleeding",

    "seizure",

)


# ============================================================
# URGENT PATTERNS
# ============================================================

URGENT_PATTERNS = (

    "persistent high fever",

    "worsening breathing",

    "severe pain",

    "repeated vomiting",

)


# ============================================================
# TRIAGE
# ============================================================

def assess_urgency(
    text: str,
    symptoms: list[Symptom],
) -> TriageAssessment:

    lower = text.lower()


    # Emergency
    combined_breathing_chest = "chest pain" in lower and "breathing difficulty" in lower
    if combined_breathing_chest or any(
        pattern in lower
        for pattern in EMERGENCY_PATTERNS
    ):

        return TriageAssessment(

            urgency="emergency",

            message=(
                "The message contains a "
                "potentially urgent warning pattern."
            ),

            reasons=[
                "A potentially serious symptom "
                "combination was detected."
            ],
        )


    # Urgent
    if any(
        pattern in lower
        for pattern in URGENT_PATTERNS
    ):

        return TriageAssessment(

            urgency="urgent",

            message=(
                "Consider prompt professional "
                "medical evaluation."
            ),

            reasons=[
                "The wording suggests symptoms "
                "that may need timely assessment."
            ],
        )


    # Routine
    return TriageAssessment(

        urgency="routine",

        message=(
            "Consider an appropriate healthcare "
            "professional for an initial assessment."
        ),

        reasons=[
            "No emergency trigger was detected "
            "by the current safety rules."
        ],
    )


# ============================================================
# NEXT ACTION
# ============================================================

def next_action(
    assessment: TriageAssessment,
    specialty: str,
) -> str:

    if assessment.urgency == "emergency":

        return (
            "Seek emergency medical care now "
            "and use local emergency services "
            "if needed."
        )


    if assessment.urgency == "urgent":

        return (
            f"Consider arranging a prompt "
            f"consultation in {specialty} "
            "or General Medicine."
        )


    return (
        f"Consider a consultation in "
        f"{specialty} if symptoms persist "
        "or concern you."
    )