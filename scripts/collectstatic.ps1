# Collect static files for production.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput
Write-Host "Static files collected to staticfiles/"
