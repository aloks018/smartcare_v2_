# SmartCare AI — local run

## Start the application
```powershell
cd "C:\Users\alok\OneDrive\Desktop\SMARTcareAI"
.\run_all.ps1
```

Backend: http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs

Open SmartCare AI in Chrome:

http://127.0.0.1:8000/

## Voice
Chrome microphone access is required. The browser speech layer accepts Hindi/English; the backend then performs language detection, symptom/intent routing, and specialty-catalog matching. Text-to-speech uses the browser's Hindi/English voices when available.

## Deploy on Render
1. Push the repository, including `render.yaml`, to GitHub's `main` branch.
2. In Render, create a Blueprint and connect `aloks018/smartcare_v2_`.
3. Render creates the web service from `render.yaml` and generates `SMARTCARE_SECRET_KEY`.

Each commit pushed to `main` triggers a deployment. Local edits do not deploy until they are committed and pushed. The app uses SQLite by default; Render filesystems are temporary unless persistent storage is configured, so account data may be lost when the service restarts. Configure a persistent database before relying on deployed accounts.
