$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPy = Join-Path $scriptRoot "..\venv\Scripts\python.exe"
$venvPy = (Resolve-Path $venvPy).Path

if (-not (Test-Path $venvPy)) {
    Write-Output "venv python not found at $venvPy"
    exit 2
}

& $venvPy --version
Write-Output "Iniciando Flask app... (CTRL+C para parar)"
& $venvPy -m flask --app app.main:create_app run --debug --host 127.0.0.1 --port 8000
