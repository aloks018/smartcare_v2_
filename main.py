from __future__ import annotations

from sqlalchemy import text

from backend.db.session import engine

from backend.app.api.auth import router as auth_router

from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.responses import (
    FileResponse,
)

from fastapi.staticfiles import (
    StaticFiles,
)


# ============================================================
# SCHEMAS
# ============================================================

from backend.app.schemas import (
    DataSource,
    MedicalSearchResponse,
    Provider,
    SearchResponse,
    VoiceAnalysisRequest,
    VoiceAnalysisResponse,
)


# ============================================================
# DATA
# ============================================================

from backend.app.data.providers import (
    DATA_SOURCES,
)


# ============================================================
# SERVICES
# ============================================================

from backend.app.services.language import (
    detect_language,
    normalize_text,
)

from backend.app.services.nlp import (
    classify_intent,
    extract_symptoms,
    predict_specialty,
    recommendation_reasons,
)

from backend.app.services.triage import (
    assess_urgency,
    next_action,
)

from backend.app.services.search import (
    search_providers,
)

from backend.app.services.medical_catalog import (
    catalog_stats,
    list_specialties,
    search_medical_catalog,
    specialty_detail,
)

from backend.app.services.ml_models import (
    model_catalog,
    resolve_model_stack,
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(
    __file__
).resolve().parent

FRONTEND_DIR = (
    ROOT_DIR / "frontend"
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(

    title="SmartCareAI",

    version="1.0.0",

    description=(
        "Voice-first AI healthcare "
        "discovery and provider search."
    ),
)

app.include_router(auth_router)


# ============================================================
# CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# STATIC FRONTEND
# ============================================================

if FRONTEND_DIR.exists():

    app.mount(

        "/static",

        StaticFiles(
            directory=FRONTEND_DIR
        ),

        name="static",
    )


# ============================================================
# DISCLAIMER
# ============================================================

DISCLAIMER = (

    "SmartCareAI provides healthcare "
    "navigation and educational support only. "
    "It does not provide medical diagnosis, "
    "prescription or emergency services."
)


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/")
def home():

    return FileResponse(

        FRONTEND_DIR
        / "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():

    return {

        "status": "ok",

        "service": "SmartCareAI",

        "version": "1.0.0",

        "provider_directory": "OpenStreetMap location search",
        "care_routing": "Deterministic medical-catalog navigation",
        "medical_catalog": catalog_stats(),
    }




# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

@app.get("/api/health/database")
def database_health():

    try:
        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception as exc:

        return {
            "status": "error",
            "database": "disconnected",
            "error": str(exc),
        }

































# ============================================================
# PROVIDERS
# ============================================================

@app.get(
    "/api/providers",
    response_model=list[Provider],
)
def get_providers(
    location: str | None = Query(default=None, max_length=120),
    query: str = Query(default="", max_length=200),
    limit: int = Query(default=12, ge=1, le=50),
):
    return search_providers(query=query, location=location, limit=limit)


# ============================================================
# PROFESSIONS
# ============================================================

@app.get(
    "/api/professions",
    response_model=list[str],
)
def get_professions():

    return [specialty["name"] for specialty in list_specialties()]


# ============================================================
# DATA SOURCES
# ============================================================

@app.get(
    "/api/data-sources",
    response_model=list[DataSource],
)
def get_data_sources():

    return DATA_SOURCES


# ============================================================
# ML MODELS
# ============================================================

@app.get(
    "/api/ml/models"
)
def get_models():

    return model_catalog()


# ============================================================
# MEDICAL NAVIGATION CATALOG
# ============================================================

@app.get("/api/medical/catalog/stats")
def get_medical_catalog_stats():
    return catalog_stats()


@app.get("/api/medical/specialties")
def get_medical_specialties(
    category: str | None = Query(default=None, max_length=80),
):
    return list_specialties(category)


@app.get("/api/medical/specialties/{specialty_id}")
def get_medical_specialty(specialty_id: str):
    result = specialty_detail(specialty_id)
    if not result:
        raise HTTPException(status_code=404, detail="Medical specialty not found")
    return result


@app.get(
    "/api/medical/search",
    response_model=MedicalSearchResponse,
)
def search_medical_specialties(
    query: str = Query(default="", max_length=300),
    limit: int = Query(default=5, ge=1, le=12),
):
    results = search_medical_catalog(query, limit=limit)
    return MedicalSearchResponse(
        query=query,
        total=len(results),
        results=results,
    )


# ============================================================
# FAST PROVIDER SEARCH
# ============================================================

@app.get(
    "/api/search",
    response_model=SearchResponse,
)
def search(

    query: str = Query(
        default="",
        max_length=200,
    ),

    location: str | None = Query(
        default=None,
        max_length=120,
    ),

    specialty: str | None = Query(
        default=None,
        max_length=100,
    ),

    ownership: str | None = Query(
        default=None,
        max_length=30,
    ),

    budget_max_inr: float | None = Query(
        default=None,
        ge=0,
    ),

    max_distance_km: float | None = Query(
        default=None,
        ge=0,
    ),

    sort: str = Query(
        default="recommended",
        pattern=(
            "^(recommended|distance|fee_low)$"
        ),
    ),
):

    results = search_providers(

        query=normalize_text(query),

        location=location,

        specialty=specialty,

        ownership=ownership,

        budget_max_inr=budget_max_inr,

        max_distance_km=max_distance_km,

        sort=sort,

        limit=12,
    )


    return SearchResponse(

        query=query,

        location=location,

        total=len(results),

        filters={

            "specialty":
                specialty,

            "ownership":
                ownership,

            "budget_max_inr":
                budget_max_inr,

            "max_distance_km":
                max_distance_km,

            "sort":
                sort,
        },

        results=results,
    )


# ============================================================
# VOICE + AI ANALYSIS
# ============================================================

@app.post("/api/analyze", response_model=VoiceAnalysisResponse)
def analyze_alias(request: VoiceAnalysisRequest):
    return analyze_voice(request)


@app.post(
    "/api/voice/analyze",
    response_model=VoiceAnalysisResponse,
)
def analyze_voice(

    request:
        VoiceAnalysisRequest,
):

    # --------------------------------------------------------
    # 1. Original text
    # --------------------------------------------------------

    transcript = (
        request.transcript.strip()
    )


    # --------------------------------------------------------
    # 2. Detect language
    # --------------------------------------------------------

    detected_language = (
        detect_language(
            transcript
        )
    )


    # --------------------------------------------------------
    # 3. Normalize
    # --------------------------------------------------------

    normalized_text = (
        normalize_text(
            transcript
        )
    )


    # --------------------------------------------------------
    # 4. Extract symptoms
    # --------------------------------------------------------

    symptoms = (
        extract_symptoms(
            normalized_text
        )
    )


    # --------------------------------------------------------
    # 5. Intent
    # --------------------------------------------------------

    intent = classify_intent(f"{transcript} {normalized_text}", symptoms)


    # --------------------------------------------------------
    # 6. Specialty
    # --------------------------------------------------------

    suggested_specialty = predict_specialty(symptoms)
    if intent in {"child_fever", "child_cough"}:
        suggested_specialty = "Pediatrics"
    elif intent == "emergency_navigation":
        suggested_specialty = "Emergency Medicine"

    medical_matches = search_medical_catalog(
        transcript,
        limit=3,
        fallback_specialty=suggested_specialty,
    )

    facility_type_by_intent = {
        "ambulance_search": "Ambulance service",
        "pharmacy_search": "Pharmacy",
        "diagnostic_service_search": "Diagnostic laboratory",
        "emergency_navigation": "Hospital",
    }
    suggested_facility_type = facility_type_by_intent.get(intent)


    # --------------------------------------------------------
    # 7. Explain recommendation
    # --------------------------------------------------------

    reasons = (
        recommendation_reasons(
            symptoms,
            suggested_specialty,
        )
    )
    reasons.append(
        "Care-area routing uses SmartCare's structured navigation catalog; it is not a clinical diagnosis."
    )


    # --------------------------------------------------------
    # 8. Safety triage
    # --------------------------------------------------------

    assessment = (
        assess_urgency(
            normalized_text,
            symptoms
        )
    )
    if assessment.urgency == "emergency":
        suggested_specialty = "Emergency Medicine"
        suggested_facility_type = "Hospital"
        medical_matches = search_medical_catalog(
            transcript,
            limit=3,
            fallback_specialty=suggested_specialty,
        )
        reasons = recommendation_reasons(symptoms, suggested_specialty)
        reasons.append(
            "Care-area routing uses SmartCare's structured navigation catalog; it is not a clinical diagnosis."
        )


    # --------------------------------------------------------
    # 9. Next action
    # --------------------------------------------------------

    recommended_action = (
        next_action(
            assessment,
            suggested_specialty,
        )
    )


    # --------------------------------------------------------
    # 10. Emergency specialty override
    # --------------------------------------------------------

    search_specialty = (

        "Emergency Medicine"

        if assessment.urgency
        == "emergency"

        else suggested_specialty
    )


    # --------------------------------------------------------
    # 11. Provider search
    # --------------------------------------------------------

    providers = search_providers(

        query=" ".join(filter(None, [suggested_facility_type, normalized_text])),
    
            location=request.location,
    
            specialty=search_specialty,
    
            ownership=request.ownership_preference,
    
            budget_max_inr=
                request.budget_max_inr,
    
            max_distance_km=
                request.max_distance_km,
    
            sort="recommended",
    
            limit=6,
        )


    # --------------------------------------------------------
    # 12. Area of care
    # --------------------------------------------------------

    if symptoms:

        symptom_names = ", ".join(

            symptom.name
            for symptom in symptoms
        )

        possible_area = (

            f"{suggested_specialty} "
            f"for symptoms such as "
            f"{symptom_names}"
        )

    else:

        possible_area = (
            "General Medicine for "
            "an initial clinical review"
        )

    if suggested_facility_type:
        possible_area = (
            f"{suggested_facility_type} listings near {request.location}"
            if request.location
            else f"{suggested_facility_type} listings (share a city to search nearby)"
        )


    # --------------------------------------------------------
    # 13. Voice response
    # --------------------------------------------------------

    symptom_summary = ", ".join(
        symptom.name
        for symptom in symptoms
    )
    facility_note = (
        "Paas ke mapped facility results neeche diye gaye hain; details confirm karein. "
        if providers
        else "Apna shehar batayein to paas ki facilities dekh sakein. "
        if not request.location
        else ""
    )

    if suggested_facility_type and assessment.urgency != "emergency":
        if not request.location:
            spoken_response = (
                "Paas ki facility dhoondhne ke liye apna shehar batayein."
                if detected_language in {"Hindi", "Hinglish"}
                else "Share your city to find nearby mapped facilities."
            )
        elif providers:
            spoken_response = (
                f"{len(providers)} OpenStreetMap par listed {suggested_facility_type} milin. "
                "Jaane se pehle facility se details confirm karein."
                if detected_language in {"Hindi", "Hinglish"}
                else f"Found {len(providers)} OpenStreetMap-listed {suggested_facility_type} options. Confirm services and availability before visiting."
            )
        else:
            spoken_response = (
                f"{request.location} ke liye koi mapped {suggested_facility_type} listing nahi mili."
                if detected_language in {"Hindi", "Hinglish"}
                else f"No mapped {suggested_facility_type} listings were found for {request.location}. Try a nearby area."
            )
    elif detected_language in {"Hindi", "Hinglish"}:
        if assessment.urgency == "emergency":
            safety_message = "Aapke message mein emergency warning mili hai. Abhi turant emergency medical care lein aur zarurat ho to local emergency services ko call karein."
        elif assessment.urgency == "urgent":
            safety_message = "Aapko jaldi medical evaluation karani chahiye."
        else:
            safety_message = "Agar symptoms bane rahein ya badhein, doctor se consultation lein."
        understanding = (
            f"Aapne {symptom_summary} ke baare mein bataya."
            if symptom_summary
            else f"Maine aapki baat ko {intent.replace('_', ' ')} ke roop mein samjha."
        )
        spoken_response = (
            f"{understanding} "
            f"Possible care area {suggested_specialty} hai. {safety_message} "
            f"{facility_note}"
            "Yeh medical diagnosis nahi hai."
        )
    else:
        understanding = (
            f"You mentioned {symptom_summary}."
            if symptom_summary
            else f"I understood your request as {intent.replace('_', ' ')}."
        )
        spoken_response = (
            f"{understanding} "
            f"The possible care area is {suggested_specialty}. "
            f"{assessment.message} {recommended_action} "
            f"{facility_note}"
            "This is not a medical diagnosis."
        )


    # --------------------------------------------------------
    # 14. Final response
    # --------------------------------------------------------

    return VoiceAnalysisResponse(

        detected_language=
            detected_language,

        transcript=
            transcript,

        normalized_text=
            normalized_text,

        intent=
            intent,

        symptoms=
            symptoms,

        suggested_specialty=
            suggested_specialty,

        suggested_facility_type=suggested_facility_type,

        possible_area_of_care=
            possible_area,

        why_this_recommendation=
            reasons,

        medical_matches=
            medical_matches,

        model_stack={
            "speech": "Browser Web Speech",
            "language": "Structured care catalog",
            "nlp": "deterministic medical-catalog navigation",
            "model_source": "structured-catalog",
            "ranking": "source-tagged facilities ordered by distance",
            "safety": "rule-based emergency warning checks",
        },

        assessment=
            assessment,

        recommended_next_action=
            recommended_action,

        providers=
            providers,

        spoken_response=
            spoken_response,

        confidence=None,
        model_source="structured-catalog",

        disclaimer=
            DISCLAIMER,
    )


# ============================================================
# SPEECH MODEL ADAPTER
# ============================================================

@app.post(
    "/api/voice/transcribe"
)
def transcribe():

    return {

        "status":
            "adapter_ready",

        "recommended_model":
            "Whisper",

        "message":
            (
                "Browser speech recognition "
                "is currently used by the frontend. "
                "A server-side Whisper adapter can "
                "be connected here later."
            ),
    }
