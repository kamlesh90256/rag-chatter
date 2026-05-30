<#
PowerShell helper to check for Docker and run docker-compose for local development.
Usage: Open PowerShell, then run: .\scripts\run-local.ps1
#>

function Ensure-Command($cmd) {
    return (Get-Command $cmd -ErrorAction SilentlyContinue) -ne $null
}

if (-not (Ensure-Command "docker")) {
    Write-Host "Docker CLI not found. Please install Docker Desktop for Windows:" -ForegroundColor Yellow
    Write-Host "https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Cyan
    Write-Host "After installing, ensure Docker Desktop is running and that 'docker' is on your PATH." -ForegroundColor Yellow
    exit 1
}

if (-not (Ensure-Command "docker-compose")) {
    # On newer Docker Desktop, use 'docker compose' subcommand instead of docker-compose
    Write-Host "Using 'docker compose' CLI (docker-compose shim not found)." -ForegroundColor Green
}

# Defaults (override by setting env vars prior to running the script)
if (-not $env:OPENAI_API_KEY) { $env:OPENAI_API_KEY = 'test' }
if (-not $env:DATABASE_URL) { $env:DATABASE_URL = 'sqlite:///./data/app.db' }
if (-not $env:CHROMA_PERSIST_DIR) { $env:CHROMA_PERSIST_DIR = '/app/data/chroma' }

Write-Host "Starting docker compose (will build images)." -ForegroundColor Green

try {
    # Use the modern 'docker compose' command where available
    docker compose up --build
} catch {
    Write-Host "Failed to run 'docker compose'. If you have the legacy docker-compose binary, try:'docker-compose up --build'" -ForegroundColor Red
    throw
}
