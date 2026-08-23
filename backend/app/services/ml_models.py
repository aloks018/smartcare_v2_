from __future__ import annotations


# ============================================================
# MODEL CATALOG
# ============================================================

def model_catalog():

    return {

        "speech": {

            "browser-web-speech": {

                "status": "active",

                "description":
                    "Browser speech recognition."
            },

            "whisper": {

                "status": "adapter",

                "description":
                    "Whisper server-side integration point."
            },

            "xls-r": {

                "status": "adapter",

                "description":
                    "XLS-R multilingual speech adapter."
            },

            "indicconformer": {

                "status": "adapter",

                "description":
                    "IndicConformer speech adapter."
            },
        },


        "language": {

            "rule-hybrid": {

                "status": "active",

                "description":
                    "Rule-based NLP baseline."
            },

            "indicbert": {

                "status": "adapter",

                "description":
                    "IndicBERT integration point."
            },

            "xlm-r": {

                "status": "adapter",

                "description":
                    "XLM-R integration point."
            },

            "indictrans": {

                "status": "adapter",

                "description":
                    "IndicTrans integration point."
            },
        },

    }


# ============================================================
# MODEL STACK
# ============================================================

def resolve_model_stack(
    speech_model: str,
    language_model: str,
) -> dict[str, str]:

    return {

        "speech": speech_model,

        "language": language_model,

        "nlp": "rule-hybrid",

        "ranking":
            "explainable-provider-ranking-v1",

        "safety":
            "rule-based-triage-v1",
    }
