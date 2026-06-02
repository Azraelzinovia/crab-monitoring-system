# ============================================================
# run_windows.ps1
# Script PowerShell untuk menjalankan Crab Monitoring System
# di Windows — pengganti docker-compose dan bash
#
# Cara Pakai:
#   .\run_windows.ps1                    # Docker (default)
#   .\run_windows.ps1 -Method Docker     # Docker Compose
#   .\run_windows.ps1 -Method Python     # Backend Python + Frontend React
#   .\run_windows.ps1 -Method Frontend   # Hanya Frontend (demo)
#   .\run_windows.ps1 -Method Stop       # Hentikan semua
# ============================================================

param(
    [string]$Method = "Docker"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = "d:\Document\Michael\cek kepiting\crab-monitoring-system"
$BackendDir  = "$ProjectRoot\backend"
$FrontendDir = "$ProjectRoot\frontend"
$VenvDir     = "$ProjectRoot\.venv"

function Write-Header($text) {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host " $text" -ForegroundColor Cyan
    Write-Host "=============================================" -ForegroundColor Cyan
}

function Test-CommandExists($cmd) {
    return (Get-Command $cmd -ErrorAction SilentlyContinue) -ne $null
}

# ── OPSI A: Docker Compose ────────────────────────────────────────────────────
function Start-WithDocker {
    Write-Header "Metode Docker Compose"

    if (-not (Test-CommandExists "docker")) {
        Write-Host "❌ Docker tidak ditemukan!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Install Docker Desktop dari:" -ForegroundColor Yellow
        Write-Host "  https://www.docker.com/products/docker-desktop/" -ForegroundColor Blue
        Write-Host ""
        Write-Host "Setelah install, restart PowerShell dan jalankan lagi." -ForegroundColor Yellow
        return
    }

    # Pastikan .env ada
    if (-not (Test-Path "$ProjectRoot\.env")) {
        Copy-Item "$ProjectRoot\.env.example" "$ProjectRoot\.env"
        Write-Host "✅ File .env dibuat dari .env.example"
    }

    # Jalankan dengan docker compose (versi baru, tanpa tanda hubung)
    Set-Location $ProjectRoot
    Write-Host "🚀 Menjalankan docker compose..." -ForegroundColor Green

    docker compose -f docker/docker-compose.yml up -d --build

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Semua service berjalan!" -ForegroundColor Green
        Write-Host ""
        Write-Host "  📊 Dashboard  : http://localhost:3000" -ForegroundColor Cyan
        Write-Host "  🔧 API        : http://localhost:8000" -ForegroundColor Cyan
        Write-Host "  📖 API Docs   : http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Perintah berguna:" -ForegroundColor Yellow
        Write-Host "  docker compose -f docker/docker-compose.yml logs -f"
        Write-Host "  docker compose -f docker/docker-compose.yml down"
    }
}

# ── OPSI B: Python Backend + React Frontend ───────────────────────────────────
function Start-WithPython {
    Write-Header "Metode Python + Node.js (Tanpa Docker)"

    # Cek Python
    $pythonCmd = if (Test-CommandExists "python3") { "python3" } elseif (Test-CommandExists "python") { "python" } else { $null }

    if (-not $pythonCmd) {
        Write-Host "❌ Python tidak ditemukan!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Download Python 3.11 dari:" -ForegroundColor Yellow
        Write-Host "  https://www.python.org/downloads/" -ForegroundColor Blue
        Write-Host ""
        Write-Host "Centang 'Add Python to PATH' saat instalasi!" -ForegroundColor Yellow
        return
    }

    $pyVersion = & $pythonCmd --version 2>&1
    Write-Host "✅ Python ditemukan: $pyVersion"

    # Buat virtual environment jika belum ada
    if (-not (Test-Path $VenvDir)) {
        Write-Host "📦 Membuat virtual environment..." -ForegroundColor Yellow
        & $pythonCmd -m venv $VenvDir
        Write-Host "✅ Virtual environment dibuat di $VenvDir"
    }

    # Install dependencies
    $pip = "$VenvDir\Scripts\pip.exe"
    Write-Host "📦 Install Python dependencies..." -ForegroundColor Yellow
    & $pip install -r "$BackendDir\requirements_windows.txt" --quiet
    Write-Host "✅ Dependencies terinstall"

    # Buat .env jika belum ada
    if (-not (Test-Path "$BackendDir\.env")) {
        Copy-Item "$ProjectRoot\.env.example" "$BackendDir\.env"
        Write-Host "✅ File .env dibuat"
    }

    # Start backend di background
    Write-Host ""
    Write-Host "🚀 Menjalankan FastAPI backend..." -ForegroundColor Green
    $uvicorn = "$VenvDir\Scripts\uvicorn.exe"

    $backendProcess = Start-Process -FilePath $uvicorn `
        -ArgumentList "main:app --host 0.0.0.0 --port 8000 --reload" `
        -WorkingDirectory $BackendDir `
        -PassThru -NoNewWindow

    Write-Host "✅ Backend PID: $($backendProcess.Id)"
    $backendProcess.Id | Out-File "$ProjectRoot\.backend.pid"

    Start-Sleep -Seconds 3

    # Start frontend
    if (Test-CommandExists "npm") {
        Write-Host ""
        Write-Host "🚀 Menjalankan React frontend..." -ForegroundColor Green

        # Install npm deps jika perlu
        if (-not (Test-Path "$FrontendDir\node_modules")) {
            Write-Host "📦 Install npm packages (ini akan memakan beberapa menit)..." -ForegroundColor Yellow
            Set-Location $FrontendDir
            npm install --silent
        }

        Set-Location $FrontendDir
        $frontendProcess = Start-Process -FilePath "npm" `
            -ArgumentList "start" `
            -WorkingDirectory $FrontendDir `
            -PassThru -NoNewWindow

        $frontendProcess.Id | Out-File "$ProjectRoot\.frontend.pid"
        Write-Host "✅ Frontend PID: $($frontendProcess.Id)"
    }

    Write-Host ""
    Write-Host "✅ Sistem berjalan!" -ForegroundColor Green
    Write-Host "  📊 Dashboard  : http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  🔧 API        : http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  📖 API Docs   : http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Untuk menghentikan: .\run_windows.ps1 -Method Stop"
}

# ── OPSI C: Hanya Frontend (Demo Mode) ───────────────────────────────────────
function Start-FrontendOnly {
    Write-Header "Frontend Only — Demo Mode"

    if (-not (Test-CommandExists "npm")) {
        Write-Host "❌ Node.js/npm tidak ditemukan!" -ForegroundColor Red
        Write-Host "Download dari: https://nodejs.org/" -ForegroundColor Blue
        return
    }

    Write-Host "Node.js: $(node --version)" -ForegroundColor Green

    Set-Location $FrontendDir

    if (-not (Test-Path "node_modules")) {
        Write-Host "📦 Install npm packages..." -ForegroundColor Yellow
        npm install
    }

    # Set API URL ke mock atau localhost
    $env:REACT_APP_API_URL = "http://localhost:8000"
    $env:BROWSER = "none"  # Jangan auto-open browser

    Write-Host ""
    Write-Host "🚀 Menjalankan React Dashboard..." -ForegroundColor Green
    Write-Host "   Akses: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "   (Backend tidak berjalan — tampilan demo)" -ForegroundColor Yellow
    Write-Host ""

    npm start
}

# ── Stop semua ────────────────────────────────────────────────────────────────
function Stop-All {
    Write-Header "Menghentikan Semua Service"

    # Stop Docker services
    if (Test-CommandExists "docker") {
        Set-Location $ProjectRoot
        docker compose -f docker/docker-compose.yml down 2>$null
        Write-Host "✅ Docker services dihentikan"
    }

    # Stop Python processes
    @(".backend.pid", ".frontend.pid") | ForEach-Object {
        $pidFile = "$ProjectRoot\$_"
        if (Test-Path $pidFile) {
            $pid = Get-Content $pidFile
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Remove-Item $pidFile
            Write-Host "✅ Process $pid dihentikan"
        }
    }

    Write-Host "✅ Semua service dihentikan"
}

# ── Main ──────────────────────────────────────────────────────────────────────
Write-Host "🦀 Crab Monitoring System — Windows Runner" -ForegroundColor Magenta
Write-Host "Metode: $Method" -ForegroundColor Gray

switch ($Method.ToLower()) {
    "docker"       { Start-WithDocker }
    "python"       { Start-WithPython }
    "frontend"     { Start-FrontendOnly }
    "frontendonly" { Start-FrontendOnly }
    "stop"         { Stop-All }
    default {
        Write-Host ""
        Write-Host "Penggunaan:" -ForegroundColor Yellow
        Write-Host "  .\run_windows.ps1 -Method Docker     # Gunakan Docker" -ForegroundColor White
        Write-Host "  .\run_windows.ps1 -Method Python     # Python + Node.js" -ForegroundColor White
        Write-Host "  .\run_windows.ps1 -Method Frontend   # Hanya Dashboard" -ForegroundColor White
        Write-Host "  .\run_windows.ps1 -Method Stop       # Hentikan semua" -ForegroundColor White
    }
}
