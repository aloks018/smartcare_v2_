# SmartCare AI — GUI run

From PowerShell:

```powershell
cd "C:\Users\alok\OneDrive\Desktop\SMARTcareAI"
.\run_all.ps1
```

Open:

http://127.0.0.1:8000/

FastAPI serves the GUI and `/api` from the same origin, so all interactive features use the normal local URL without a separate frontend server.
