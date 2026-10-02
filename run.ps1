# MuleTrace Launcher for Windows PowerShell
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  MULETRACE // Money-Mule Ring Detection System   " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "[1/3] Checking Python environment..." -ForegroundColor Yellow
python -c "import pandas, networkx, fastapi, uvicorn, yaml, pydantic, sklearn; print(' Python dependencies verified.')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Missing Python dependencies. Installing requirements.txt..." -ForegroundColor Red
    python -m pip install -r requirements.txt
}

# 2. Check Demo Data
if (-not (Test-Path "data/demo/transactions.csv")) {
    Write-Host "[2/3] Generating synthetic demo dataset..." -ForegroundColor Yellow
    python data/make_data.py --seed 42
} else {
    Write-Host "[2/3] Synthetic demo dataset exists." -ForegroundColor Green
}

# 3. Launch Services
Write-Host "[3/3] Starting MuleTrace Backend and Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload"
Set-Location frontend
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend node_modules..." -ForegroundColor Yellow
    npm.cmd install
}
npm.cmd run dev
