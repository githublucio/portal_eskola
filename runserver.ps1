# Run portal on port 8001 (avoids conflict with other local apps on 8000).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
