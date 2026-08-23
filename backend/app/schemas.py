from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# SYMPTOM
# ============================================================

class Symptom(BaseModel):
    name: str
    evidence: str = ""
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0
    )


# ============================================================
# TRIAGE
# ============================================================

class TriageAssessment(BaseModel):
    urgency: str
    message: str
    reasons: list[str] = Field(default_factory=list)


# ============================================================
# PROVIDER
# ============================================================

class Provider(BaseModel):
    id: str

    name: str
    provider_type: str = "Hospital"

    ownership: str = "Unknown"

    specialty: Optional[str] = None

    city: Optional[str] = None
    district: Optional[str] = None
    state: str = "Uttar Pradesh"

    address: Optional[str] = None

    phone: Optional[str] = None
    website: Optional[str] = None

    consultation_fee_inr: Optional[float] = None

    emergency_available: bool = False

    availability: Optional[str] = None

    languages: list[str] = Field(default_factory=list)

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    verified_source: Optional[str] = None
    verified: bool = False

    # Calculated by search.py
    distance_km: Optional[float] = None
    match_score: Optional[float] = None

    match_reasons: list[str] = Field(
        default_factory=list
    )


# ============================================================
# SEARCH RESPONSE
# ============================================================

class SearchResponse(BaseModel):
    query: str

    location: Optional[str] = None

    total: int

    filters: dict[str, object] = Field(
        default_factory=dict
    )

    results: list[Provider]


# ============================================================
# VOICE ANALYSIS REQUEST
# ============================================================

class VoiceAnalysisRequest(BaseModel):
    transcript: str = Field(
        min_length=1,
        max_length=4000
    )

    location: Optional[str] = Field(
        default=None,
        max_length=120
    )

    speech_model: str = "browser-web-speech"

    language_model: str = "rule-hybrid"

    ownership_preference: Optional[str] = None

    budget_max_inr: Optional[float] = Field(
        default=None,
        ge=0
    )

    max_distance_km: Optional[float] = Field(
        default=None,
        ge=0
    )


# ============================================================
# VOICE ANALYSIS RESPONSE
# ============================================================

class VoiceAnalysisResponse(BaseModel):

    detected_language: str

    transcript: str

    normalized_text: str

    intent: str

    symptoms: list[Symptom]

    suggested_specialty: str

    possible_area_of_care: str

    why_this_recommendation: list[str]

    model_stack: dict[str, str]

    assessment: TriageAssessment

    recommended_next_action: str

    providers: list[Provider]

    spoken_response: str

    disclaimer: str


# ============================================================
# DATA SOURCE
# ============================================================

class DataSource(BaseModel):
    name: str

    url: str

    description: str

    type: str = "official"