#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start TruthStream AI — FastAPI backend + Streamlit dashboard.
    The Docker stack (Kafka, Spark, MongoDB) must already be running.

.EXAMPLE
    .\scripts\start-app.ps1
#>

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TruthStream AI — Starting services"    -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set env vars
$env:PYTHONPATH  = "."
$env:PYTHONUTF8  = "1"

# ------------------------------------------------------------------
# 1. FastAPI backend
# ------------------------------------------------------------------
Write-Host "[1/2] Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Yellow
$apiJob = Start-Process -NoNewWindow -PassThru `
    -FilePath "py" `
    -ArgumentList @("-3.12", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000") `
    -WorkingDirectory $Root

Start-Sleep -Seconds 3

# Quick health check
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   [OK] FastAPI running — status: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "   [WARN] FastAPI not yet responding — it may still be starting" -ForegroundColor Yellow
}

# ------------------------------------------------------------------
# 2. Streamlit dashboard
# ------------------------------------------------------------------
Write-Host "[2/2] Starting Streamlit dashboard on http://localhost:8501 ..." -ForegroundColor Yellow
$dashJob = Start-Process -NoNewWindow -PassThru `
    -FilePath "py" `
    -ArgumentList @("-3.12", "-m", "streamlit", "run", "dashboard/app.py",
                    "--server.port", "8501", "--server.headless", "true") `
    -WorkingDirectory $Root

Start-Sleep -Seconds 4

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Services started!" -ForegroundColor Green
Write-Host ""
Write-Host "  Dashboard:   http://localhost:8501" -ForegroundColor Cyan
Write-Host "  API:         http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs:    http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Kafka UI:    http://localhost:8080" -ForegroundColor Cyan
Write-Host "  Mongo:       http://localhost:8081" -ForegroundColor Cyan
Write-Host "  Spark UI:    http://localhost:8090" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop both services." -ForegroundColor Gray
Write-Host ""

# Keep running and wait for Ctrl+C
try {
    Wait-Process -Id $apiJob.Id, $dashJob.Id -ErrorAction SilentlyContinue
} finally {
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Stop-Process -Id $apiJob.Id  -ErrorAction SilentlyContinue
    Stop-Process -Id $dashJob.Id -ErrorAction SilentlyContinue
    Write-Host "Done." -ForegroundColor Green
}
