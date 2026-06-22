# Local Running Script for Windows (Using SQLite and bypassing Docker/Postgres/Redis)

# 1. Update the .env file to use SQLite instead of Postgres
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    $content = Get-Content $envFile
    # Replace Database URL and Redis configs for local execution
    $content = $content -replace "DATABASE_URL=postgresql.*", "DATABASE_URL=sqlite+aiosqlite:///local_db.db"
    $content = $content -replace "REDIS_URL=redis.*", "REDIS_URL="
    $content = $content -replace "UPLOAD_DIR=.*", "UPLOAD_DIR=data/uploads"
    $content = $content -replace "CLONE_DIR=.*", "CLONE_DIR=data/cloned"
    Set-Content $envFile $content
}

Write-Host "Configured .env to use local SQLite and bypass Redis." -ForegroundColor Green

# 2. Setup Python backend
Write-Host "Setting up Python backend virtual environment..." -ForegroundColor Cyan
cd "$PSScriptRoot\backend"
if (!(Test-Path "venv")) {
    python -m venv venv
}

# Run setup in the active terminal to verify requirements are met
& ".\venv\Scripts\Activate.ps1"
pip install -r requirements.txt

# Start backend in a separate terminal window
Write-Host "Launching backend FastAPI server on port 8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; & '.\venv\Scripts\Activate.ps1'; uvicorn app.main:app --reload --port 8000"

# 3. Setup React frontend
Write-Host "Setting up React frontend dependencies..." -ForegroundColor Cyan
cd "$PSScriptRoot\frontend"
npm install

# Start frontend in a separate terminal window
Write-Host "Launching frontend Vite dev server..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host "--------------------------------------------------------" -ForegroundColor Green
Write-Host "Application launched successfully!" -ForegroundColor Green
Write-Host "  Frontend Server: http://localhost:5173" -ForegroundColor Yellow
Write-Host "  Backend API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------" -ForegroundColor Green
