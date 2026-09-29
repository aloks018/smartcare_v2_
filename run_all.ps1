$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python is required and was not found on PATH." }
if (-not (Test-Path .venv)) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path "backend\models\symptom_router.joblib")) { & .\.venv\Scripts\python.exe -c "import os,runpy; os.environ['PYTHONPATH']=r'$PSScriptRoot'; runpy.run_path(r'$PSScriptRoot\backend\scripts\train_model.py')" }
$server = Start-Process -FilePath (Resolve-Path ".\.venv\Scripts\python.exe") -ArgumentList "-m uvicorn main:app --host 127.0.0.1 --port 8000" -PassThru
Start-Sleep -Seconds 2
Write-Host "SmartCareAI: http://127.0.0.1:8000"
Write-Host "API Docs: http://127.0.0.1:8000/docs"
Start-Process "chrome.exe" "http://127.0.0.1:8000/"
Write-Host "Press Ctrl+C to stop this launcher."
try { Wait-Process -Id $server.Id } finally { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
