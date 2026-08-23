# SmartCareAI

SmartCareAI is a voice-first healthcare discovery prototype with a Python/FastAPI backend and a connected browser UI. It gives cautious care-navigation suggestions and source-backed Uttar Pradesh provider search results. It does not diagnose, prescribe, or replace emergency care.

## Highlight Feature

The primary experience is the glowing voice assistant on the home page. Chrome captures speech, the backend detects the likely language/script, extracts symptoms, estimates urgency, predicts the likely care specialty, and returns nearby Uttar Pradesh provider cards.

Current active stack:

- Speech: Chrome Web Speech API
- Medical NLP: rule-hybrid multilingual symptom extraction and safety triage
- Provider discovery: official-source seeded UP healthcare data

Adapter-ready model choices:

- Speech-to-text: Whisper, XLS-R, IndicConformer
- Indian-language NLP/translation: IndicBERT, XLM-R, IndicTrans

The app exposes these choices in the UI and `/api/ml/models`. Heavy model weights are intentionally not installed by default.

## Run Locally In Chrome

Open PowerShell in this folder:

```powershell
cd C:\Users\alok\OneDrive\Desktop\SMARTcareAI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open Chrome:

```powershell
start chrome http://127.0.0.1:8000
```

Chrome microphone access works on `localhost` / `127.0.0.1`. Click **Allow** when Chrome asks for microphone permission.

## Run Publicly For Testing

For a temporary public HTTPS URL, keep the FastAPI server running, then use one of these tunnel tools in a second PowerShell window:

### Option A: Cloudflare Tunnel

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Open the generated `https://...trycloudflare.com` URL in Chrome.

### Option B: ngrok

```powershell
ngrok http 8000
```

Open the generated `https://...ngrok-free.app` URL in Chrome.

Important: public microphone access requires HTTPS. A plain `http://` public URL usually will not allow the browser microphone API.

## API Endpoints

- `GET /api/health`
- `POST /api/voice/analyze`
- `POST /api/voice/transcribe`
- `GET /api/providers`
- `GET /api/professions`
- `GET /api/data-sources`
- `GET /api/ml/models`
- `GET /api/search?query=cardiologist%20near%20Kanpur`

## Official Data Sources

Seeded provider data and future import paths are based on public/official sources:

- National Hospital Directory on data.gov.in
- ABDM Health Facility Registry and Healthcare Professionals Registry
- ABDM Uttar Pradesh dashboard
- District Lucknow public utility hospital list
- District Varanasi public utility hospital list
- KGMU, SGPGIMS, UPUMS, Apollo Lucknow, and Medanta Lucknow official pages

To import a larger National Hospital Directory extract:

```powershell
python scripts\import_data_gov_hospitals.py --state "Uttar Pradesh" --limit 500 --out data\up_hospitals_import.json
```

If the API route is unavailable, download the CSV from data.gov.in and run:

```powershell
python scripts\import_data_gov_hospitals.py --csv path\to\national_hospital_directory.csv --state "Uttar Pradesh" --limit 500 --out data\up_hospitals_import.json
```

## Notes For Production

- Replace the seeded provider list with PostgreSQL/PostGIS.
- Enable the `WhisperSpeechToTextService` after installing the chosen Whisper package/model.
- Fine-tune/evaluate XLS-R, IndicConformer, IndicBERT, XLM-R, or IndicTrans before using them for medical production decisions.
- Add authentication before storing appointments or patient history.
- Keep patient health data private and avoid exposing sensitive medical information in public logs or URLs.
