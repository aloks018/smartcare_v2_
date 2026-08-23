from __future__ import annotations

from pathlib import Path

from fastapi import (
    FastAPI,
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
    Provider,
    SearchResponse,
    VoiceAnalysisRequest,
    VoiceAnalysisResponse,
)


# ============================================================
# DATA
# ============================================================

from backend.app.data.providers import (
    PROVIDERS,
    HEALTH_PROFESSIONS,
    OFFICIAL_DATA_SOURCES,
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

from backend.app.services.ml_models import (
    model_catalog,
    resolve_model_stack,
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = Path(
    __file__
).resolve().parents[2]

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


# ============================================================
# CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
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

        "providers_loaded":
            len(PROVIDERS),
    }


# ============================================================
# PROVIDERS
# ============================================================

@app.get(
    "/api/providers",
    response_model=list[Provider],
)
def get_providers():

    return PROVIDERS


# ============================================================
# PROFESSIONS
# ============================================================

@app.get(
    "/api/professions",
    response_model=list[str],
)
def get_professions():

    return HEALTH_PROFESSIONS


# ============================================================
# DATA SOURCES
# ============================================================

@app.get(
    "/api/data-sources",
    response_model=list[DataSource],
)
def get_data_sources():

    return OFFICIAL_DATA_SOURCES


# ============================================================
# ML MODELS
# ============================================================

@app.get(
    "/api/ml/models"
)
def get_models():

    return model_catalog()


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

        query=query,

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

    intent = (
        classify_intent(
            normalized_text,
            symptoms
        )
    )


    # --------------------------------------------------------
    # 6. Specialty
    # --------------------------------------------------------

    suggested_specialty = (
        predict_specialty(
            symptoms
        )
    )


    # --------------------------------------------------------
    # 7. Explain recommendation
    # --------------------------------------------------------

    reasons = (
        recommendation_reasons(
            symptoms,
            suggested_specialty,
        )
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

        query=transcript,
    
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


    # --------------------------------------------------------
    # 13. Voice response
    # --------------------------------------------------------

    spoken_response = (

        "I understood your request as "

        + intent.replace(
            "_",
            " "
        )

        + ". "

        + f"The possible care area is "
        f"{suggested_specialty}. "

        + assessment.message

        + " "

        + recommended_action

        + " This is not a medical diagnosis."
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

        possible_area_of_care=
            possible_area,

        why_this_recommendation=
            reasons,

        model_stack=
            resolve_model_stack(

                request.speech_model,

                request.language_model,
            ),

        assessment=
            assessment,

        recommended_next_action=
            recommended_action,

        providers=
            providers,

        spoken_response=
            spoken_response,

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