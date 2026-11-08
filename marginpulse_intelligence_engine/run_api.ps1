$ErrorActionPreference = "Stop"
if (-not (Test-Path ".env")) { throw "Copy .env.example to .env and set MARGINPULSE_API_KEY first." }
if (-not $env:MARGINPULSE_STORAGE) { $env:MARGINPULSE_STORAGE = ".\storage" }
python -m uvicorn marginpulse_engine.api:app --host 127.0.0.1 --port 8000
