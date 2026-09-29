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
