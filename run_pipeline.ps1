# Automates: generate data (once), run triage, timestamp + archive outputs, open digest
$ErrorActionPreference = "Stop"
$folder = $PSScriptRoot
Set-Location $folder

Write-Host "Running ticket triage pipeline..." -ForegroundColor Cyan

if (!(Test-Path "tickets_raw.csv")) {
    python generate_data.py
}

python triage.py

$timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$archiveFolder = "archive"
if (!(Test-Path $archiveFolder)) { New-Item -ItemType Directory -Path $archiveFolder | Out-Null }
Copy-Item "digest.html" "$archiveFolder\digest_$timestamp.html"
Copy-Item "tickets_processed.csv" "$archiveFolder\processed_$timestamp.csv"

Write-Host "Pipeline complete. Digest archived as digest_$timestamp.html" -ForegroundColor Green
Start-Process "digest.html"

# To schedule daily: 
# schtasks /create /tn "TicketTriage" /tr "powershell -File $folder\run_pipeline.ps1" /sc daily /st 08:00