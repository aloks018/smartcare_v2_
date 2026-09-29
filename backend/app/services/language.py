from __future__ import annotations

import re


# ============================================================
# DEVANAGARI DETECTION
# ============================================================

DEVANAGARI_PATTERN = re.compile(
    r"[\u0900-\u097F]"
)


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(text: str) -> str:

    if not text:
        return "Unknown"

    text = text.strip()

    # Hindi script
    if DEVANAGARI_PATTERN.search(text):
        return "Hindi"

    lower = text.lower()

    hindi_words = {
        "mujhe",
        "mujhko",
        "hai",
        "hain",
        "mein",
        "me",
        "se",
        "ka",
        "ki",
        "ke",
        "dard",
        "bukhar",
        "khansi",
        "saans",
        "takleef",
        "dikkat",
        "chahiye",
        "sarkari",
        "aspatal",
        "doctor",
        "kahan",
        "paas",
        "nazdik",
    }

    tokens = set(
        re.findall(
            r"[a-zA-Z]+",
            lower
        )
    )

    matched = tokens.intersection(
        hindi_words
    )

    if len(matched) >= 2:
        return "Hinglish"

    return "English"


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:

    if not text:
        return ""

    text = text.strip().lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    replacements = {

        # Fever
        "bukhar": "fever",
        "बुखार": "fever",

        # Cough
        "khansi": "cough",
        "khaansi": "cough",
        "खांसी": "cough",
        "खाँसी": "cough",

        # Breathing
        "saans ki takleef":
            "breathing difficulty",

        "saans lene mein dikkat":
            "breathing difficulty",
        "सांस लेने में दिक्कत":
            "breathing difficulty",
        "सांस लेने में कठिनाई":
            "breathing difficulty",
        "सांस फूलना":
            "shortness of breath",

        "saans lene me dikkat":
            "breathing difficulty",

        "saans phoolna":
            "shortness of breath",

        # Pain
        "sir dard":
            "headache",
        "sir mein dard":
            "headache",
        "sir me dard":
            "headache",
        "सिर दर्द":
            "headache",
        "सिर में दर्द":
            "headache",

        "seene mein dard":
            "chest pain",

        "seene me dard":
            "chest pain",

        "seene ka dard":
            "chest pain",
        "सीने में दर्द":
            "chest pain",
        "सीने का दर्द":
            "chest pain",

        "pet dard":
            "abdominal pain",
        "pet mein dard":
            "abdominal pain",
        "pet me dard":
            "abdominal pain",
        "pait mein dard":
            "abdominal pain",
        "pait me dard":
            "abdominal pain",
        "पेट दर्द":
            "abdominal pain",
        "पेट में दर्द":
            "abdominal pain",

        # Other
        "ulti":
            "vomiting",
        "उल्टी":
            "vomiting",

        "chakkar":
            "dizziness",
        "चक्कर":
            "dizziness",

        "jodon ka dard":
            "joint pain",
        "जोड़ों का दर्द":
            "joint pain",

        # Healthcare search
        "aspatal":
            "hospital",

        "sarkari aspatal":
            "government hospital",

        "sarkari hospital":
            "government hospital",

        "private hospital":
            "private hospital",
    }

    # Longest phrases first
    for source, target in sorted(
        replacements.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):

        text = text.replace(
            source,
            target
        )

    return text
