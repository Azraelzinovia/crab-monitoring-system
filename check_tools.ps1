# ============================================================
# Panduan Menjalankan Crab Monitoring System di Windows
# ============================================================
# Pilih salah satu dari 3 opsi di bawah ini:
#
# OPSI A: Docker Desktop (Rekomendasi — paling mudah)
# OPSI B: Python + Node.js Manual (tanpa Docker)
# OPSI C: Hanya Frontend (demo dashboard tanpa backend)
# ============================================================

Write-Host "🦀 Crab Monitoring System - Windows Setup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# ── Cek tool yang tersedia ────────────────────────────────────────────────────
function Check-Command($cmd) {
    return (Get-Command $cmd -ErrorAction SilentlyContinue) -ne $null
}

$hasDocker  = Check-Command "docker"
$hasPython  = Check-Command "python" -or (Check-Command "python3")
$hasNode    = Check-Command "node"

Write-Host ""
Write-Host "Status Tools:" -ForegroundColor Yellow
Write-Host "  Docker:  $(if($hasDocker){'✅ Installed'}else{'❌ Tidak ditemukan'})"
Write-Host "  Python:  $(if($hasPython){'✅ Installed'}else{'❌ Tidak ditemukan'})"
Write-Host "  Node.js: $(if($hasNode){'✅ v' + (node --version)}else{'❌ Tidak ditemukan'})"
Write-Host ""

if ($hasDocker) {
    Write-Host "✅ Docker ditemukan — gunakan: .\run_windows.ps1 -Method Docker" -ForegroundColor Green
} elseif ($hasPython) {
    Write-Host "✅ Python ditemukan — gunakan: .\run_windows.ps1 -Method Python" -ForegroundColor Green
} elseif ($hasNode) {
    Write-Host "✅ Node.js ditemukan — gunakan: .\run_windows.ps1 -Method FrontendOnly" -ForegroundColor Green
} else {
    Write-Host "⚠️  Belum ada tool yang terinstall." -ForegroundColor Yellow
    Write-Host "   Lihat panduan instalasi di bawah ini." -ForegroundColor Yellow
}
