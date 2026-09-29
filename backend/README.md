# SmartCare AI backend

## What this backend does
- FastAPI REST API for the existing SmartCare frontend.
- TF-IDF + Logistic Regression for symptom/intent routing.
- Hindi, English and Hinglish language detection.
- Urgency guardrails for obvious emergency phrases.
- Provider search from the current application provider repository.
- Modular specialty navigation search from `data/*.json`.
- Official public-health source links from `/api/data-sources`.

## Important data note
`data/symptom_training_data.csv` is a small **baseline/demo training set**, not real patient data. It must not be presented as clinical evidence or as a validated medical dataset. For production accuracy, replace it with a properly licensed, de-identified clinical dataset and validate the model with medical professionals.

`data/providers.csv` is example directory data. Replace it with verified provider records from your licensed/official source before production use.

## Run
PowerShell:
```powershell
cd "C:\Users\alok\OneDrive\Desktop\SMARTcareAI"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

The FastAPI application serves the frontend and API from the same origin at
`http://127.0.0.1:8000/`.
