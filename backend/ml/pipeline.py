from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
from joblib import load
from sklearn.metrics import accuracy_score

from .preprocess import load_training_data
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

MODEL_NAME = "TF-IDF + Logistic Regression"

SPECIALTY_MAP = {
    "fever": "General Medicine",
    "cough": "General Medicine",
    "cold": "General Medicine",
    "headache": "General Medicine",
    "stomach": "Gastroenterology",
    "vomiting": "General Medicine",
    "diarrhea": "General Medicine",
    "chest_pain": "Emergency Medicine",
    "breathing": "Emergency Medicine",
    "palpitations": "Cardiology",
    "blood_pressure": "Cardiology",
    "pregnancy": "Obstetrics & Gynecology",
    "pregnancy_pain": "Obstetrics & Gynecology",
    "child_fever": "Pediatrics",
    "child_cough": "Pediatrics",
    "skin": "Dermatology",
    "joint_pain": "Orthopedics",
}

URGENT_KEYWORDS = [
    "chest pain", "सीने में दर्द", "difficulty breathing", "सांस लेने में दिक्कत",
    "can't breathe", "not breathing", "unconscious", "बेहोश", "seizure", "दौरा",
    "severe bleeding", "बहुत ज्यादा खून", "stroke", "लकवा",
]

def build_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1, max_features=12000)),
        ("clf", LogisticRegression(max_iter=1200, class_weight="balanced")),
    ])

class CareRouter:
    def __init__(self, data_path: Path, model_path: Path | None = None):
        self.data_path = data_path
        self.df = load_training_data(data_path)
        self.training_examples = len(self.df)
        self.model_path = model_path or data_path.parent.parent / "models" / "symptom_router.joblib"
        if self.model_path.exists():
            self.pipeline = load(self.model_path)
            self.model_source = "saved-model"
        else:
            self.pipeline = build_pipeline()
            self.pipeline.fit(self.df["text"], self.df["intent"])
            self.model_source = "trained-at-startup"
        self.model_name = MODEL_NAME

    def _language(self, text: str) -> str:
        devanagari = len(re.findall(r"[\u0900-\u097F]", text))
        latin = len(re.findall(r"[A-Za-z]", text))
        hinglish_markers = [
            "mujhe", "mera", "meri", "mere", "hai", "ho raha", "dard", "bukhar",
            "khansi", "saans", "dil", "pet", "ulti", "baccha", "bache", "doctor chahiye",
        ]
        lower = text.lower()
        transliterated = sum(1 for marker in hinglish_markers if marker in lower)
        if devanagari and latin or transliterated >= 1 and latin >= 3:
            return "Hinglish"
        if devanagari:
            return "Hindi"
        return "English"

    def _rule_intent(self, text: str) -> str | None:
        t = text.lower()
        rules = [
            ("breathing", ["difficulty breathing", "cannot breathe", "can't breathe", "सांस लेने में दिक्कत", "saans phool", "saans lene mein dikkat"]),
            ("chest_pain", ["chest pain", "सीने में दर्द", "seene mein dard", "chest pressure", "seene mein pressure"]),
            ("palpitations", ["heart is racing", "heartbeat is very fast", "दिल बहुत तेज", "dil tez dhadak"]),
            ("child_fever", ["child has fever", "baby has fever", "बच्चे को बुखार", "bacche ko bukhar", "bache ko bukhar"]),
            ("child_cough", ["child is coughing", "baby is coughing", "बच्चे को खांसी", "bacche ko khansi", "bache ko khansi"]),
            ("pregnancy_pain", ["pregnant and have pain", "pregnancy with abdominal pain", "pregnancy mein dard", "pregnant हूं और पेट में दर्द", "pregnancy me dard"]),
            ("pregnancy", ["pregnancy checkup", "pregnancy consultation", "गर्भावस्था की जांच", "pregnancy doctor chahiye"]),
            ("fever", ["fever", "बुखार", "bukhar"]),
            ("headache", ["headache", "सिर में दर्द", "sir dard", "sir mein dard"]),
            ("cough", ["dry cough", "coughing a lot", "खांसी", "khansi"]),
            ("cold", ["bad cold", "runny nose", "जुकाम", "naak beh"]),
            ("stomach", ["stomach pain", "पेट में दर्द", "pet dard", "pet mein dard"]),
            ("vomiting", ["vomiting", "उल्टी", "ulti"]),
            ("diarrhea", ["diarrhea", "loose motion", "दस्त", "dast"]),
            ("blood_pressure", ["blood pressure", "my bp", "मेरा बीपी", "bp high", "bp badha"]),
            ("skin", ["skin rash", "itchy skin", "त्वचा पर दाने", "skin par rash", "khujli"]),
            ("joint_pain", ["joint pain", "knee pain", "घुटने में दर्द", "joints mein pain", "ghutne mein dard"]),
        ]
        for intent, phrases in rules:
            if any(phrase in t for phrase in phrases):
                return intent
        return None

    def _urgency(self, text: str, intent: str) -> tuple[str, str]:
        lowered = text.lower()
        if any(k in lowered for k in URGENT_KEYWORDS):
            return "emergency", "Seek emergency medical care now. SmartCare is not an emergency service."
        if intent in {"chest_pain", "breathing"}:
            return "urgent", "Arrange prompt in-person medical assessment, and use emergency services if symptoms are severe or worsening."
        if intent in {"pregnancy_pain", "palpitations", "blood_pressure", "child_fever"}:
            return "priority", "Arrange an in-person clinical assessment soon, especially if symptoms persist or worsen."
        return "routine", "A routine medical consultation may be appropriate if symptoms persist, recur, or concern you."

    def analyze(self, transcript: str) -> dict[str, Any]:
        language = self._language(transcript)
        probs = self.pipeline.predict_proba([transcript])[0]
        classes = self.pipeline.classes_
        best_idx = probs.argmax()
        ml_intent = str(classes[best_idx])
        ml_confidence = float(probs[best_idx])
        rule_intent = self._rule_intent(transcript)
        intent = rule_intent or ml_intent
        confidence = max(ml_confidence, 0.92) if rule_intent else ml_confidence
        specialty = SPECIALTY_MAP.get(intent, "General Medicine")
        urgency, message = self._urgency(transcript, intent)
        symptoms = [{"name": intent.replace("_", " ").title(), "confidence": round(confidence, 3)}]
        return {
            "detected_language": language,
            "symptoms": symptoms,
            "suggested_specialty": specialty,
            "intent": intent,
            "confidence": round(confidence, 3),
            "model_source": self.model_source,
            "urgency": urgency,
            "assessment": {"message": message},
            "recommended_next_action": message,
            "why_this_recommendation": [
                f"The classifier matched the message most strongly to {intent.replace('_', ' ')}.",
                f"Recommended specialty: {specialty}.",
                f"Model confidence: {confidence:.0%}; this is a routing confidence, not a diagnosis probability.",
            ],
            "disclaimer": "SmartCare AI is a care-navigation aid. It does not diagnose disease or replace a licensed clinician.",
        }

    def all_providers(self) -> list[dict[str, Any]]:
        return self.df_provider_records()

    def df_provider_records(self) -> list[dict[str, Any]]:
        provider_path = self.data_path.parent / "providers.csv"
        pdf = pd.read_csv(provider_path).fillna("")
        return pdf.to_dict(orient="records")

    def search_providers(self, query: str, location: str | None = None, specialty: str | None = None,
                         ownership: str | None = None, budget_max_inr: int | None = None,
                         max_distance_km: float | None = None) -> list[dict[str, Any]]:
        records = self.all_providers()
        q = (query or "").lower().strip()
        out = []
        for item in records:
            hay = " ".join(str(item.get(k, "")) for k in ["name", "city", "district", "specialty", "type", "ownership"]).lower()
            if q and q not in hay:
                # also allow specialty-only matches from model output
                if specialty and specialty.lower() not in hay:
                    continue
            if location and location.lower() not in hay:
                continue
            if ownership and item.get("ownership") != ownership:
                continue
            if specialty and item.get("specialty") != specialty:
                continue
            if budget_max_inr is not None and float(item.get("consultation_fee_inr", 0) or 0) > budget_max_inr:
                continue
            if max_distance_km is not None and float(item.get("distance_km", 9999) or 9999) > max_distance_km:
                continue
            out.append(item)
        return out

    def hindi_or_english_response(self, result: dict[str, Any]) -> str:
        lang = result.get("detected_language", "English")
        specialty = result.get("suggested_specialty", "General Medicine")
        urgency = result.get("urgency", "routine")
        if lang in {"Hindi", "Hinglish"}:
            if urgency == "emergency":
                return "आपके बताए लक्षणों में आपात स्थिति के संकेत हो सकते हैं। अभी नज़दीकी emergency care लें या स्थानीय emergency service से संपर्क करें।"
            return f"आपकी बात के आधार पर SmartCare आपको {specialty} से जुड़ी medical assessment की दिशा में मार्गदर्शन कर रहा है। यह diagnosis नहीं है।"
        if urgency == "emergency":
            return "Your symptoms may indicate an emergency. Please seek emergency medical care now."
        return f"Based on your message, SmartCare recommends considering {specialty} for an in-person assessment. This is not a diagnosis."
