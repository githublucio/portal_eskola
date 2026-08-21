# Restore PostgreSQL dump + optional media zip.
# WARNING: overwrites target database / media.
# Usage:
#   .\scripts\restore.ps1 -DumpPath .\backups\db_YYYYMMDD_HHMMSS.dump
#   .\scripts\restore.ps1 -DumpPath .\backups\db_....dump -MediaZip .\backups\media_....zip

param(
    [Parameter(Mandatory = $true)][string]$DumpPath,
    [string]$MediaZip = "",
    [string]$DbName = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path $DumpPath)) { throw "Dump not found: $DumpPath" }

if (-not $DbName) {
    $DbName = "escola_atauro"
    $EnvFile = Join-Path $Root ".env"
    if (Test-Path $EnvFile) {
        Get-Content $EnvFile | ForEach-Object {
            if ($_ -match '^\s*DB_NAME=(.+)$') { $DbName = $Matches[1].Trim() }
        }
    }
}

Write-Host "Restoring '$DumpPath' into database '$DbName'..."
& pg_restore --clean --if-exists -d $DbName $DumpPath
if ($LASTEXITCODE -ne 0) {
    Write-Warning "pg_restore exited with code $LASTEXITCODE (some notices are normal)."
}

if ($MediaZip) {
    if (-not (Test-Path $MediaZip)) { throw "Media zip not found: $MediaZip" }
    $MediaPath = Join-Path $Root "media"
    New-Item -ItemType Directory -Force -Path $MediaPath | Out-Null
    Write-Host "Extracting media to $MediaPath"
    Expand-Archive -Path $MediaZip -DestinationPath $MediaPath -Force
}

Write-Host "Restore finished. Run migrations if needed:"
Write-Host "  .\.venv\Scripts\python.exe manage.py migrate"
