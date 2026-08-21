# Backup PostgreSQL database + media files for portal_eskola.
# Usage:
#   .\scripts\backup.ps1
#   .\scripts\backup.ps1 -OutDir D:\backups\portal_eskola

param(
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not $OutDir) {
    $OutDir = Join-Path $Root "backups"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$DbName = "escola_atauro"
$EnvFile = Join-Path $Root ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*DB_NAME=(.+)$') { $DbName = $Matches[1].Trim() }
    }
}

$SqlPath = Join-Path $OutDir "db_$Stamp.dump"
$MediaZip = Join-Path $OutDir "media_$Stamp.zip"

Write-Host "Backing up database '$DbName' -> $SqlPath"
& pg_dump -Fc -f $SqlPath $DbName
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed. Is PostgreSQL bin on PATH?" }

$MediaPath = Join-Path $Root "media"
if (Test-Path $MediaPath) {
    Write-Host "Backing up media -> $MediaZip"
    if (Test-Path $MediaZip) { Remove-Item $MediaZip -Force }
    Compress-Archive -Path (Join-Path $MediaPath "*") -DestinationPath $MediaZip -Force
} else {
    Write-Host "No media folder to backup."
}

Write-Host "Backup complete:"
Write-Host "  $SqlPath"
if (Test-Path $MediaZip) { Write-Host "  $MediaZip" }
Write-Host "Verify with: pg_restore -l `"$SqlPath`""
