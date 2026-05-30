# Start backend safely: stop any process on port 8000, then start uvicorn
$port = 8000
$procs = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($procs) {
    Write-Host "Killing process(es) using port $port: $procs"
    foreach ($pid in $procs) { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 1
}

# Activate venv if present
if (Test-Path ".\.venv-backend\Scripts\Activate.ps1") {
    . ".\.venv-backend\Scripts\Activate.ps1"
}

$env:OPENAI_API_KEY = $env:OPENAI_API_KEY
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --log-level info
