$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Start-Process "http://127.0.0.1:8000/"
Write-Host "SmartCareAI is served by FastAPI. Run .\run_backend.ps1 first if it is not already running."
