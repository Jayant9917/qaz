param(
    [ValidateSet("backend", "frontend", "infra", "all")]
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Start-DetachedProcess {
    param(
        [string]$FilePath,
        [string]$WorkingDirectory,
        [string[]]$Arguments
    )

    Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -WindowStyle Hidden
}

switch ($Target) {
    "infra" {
        Set-Location $Root
        docker compose --env-file .env -f infra/compose/docker-compose.core.yml up -d
    }
    "backend" {
        Start-DetachedProcess -FilePath "python.exe" -WorkingDirectory (Join-Path $Root "backend") -Arguments @("-m", "uvicorn", "novo.main:app", "--reload", "--app-dir", "src", "--host", "127.0.0.1", "--port", "8000")
    }
    "frontend" {
        Start-DetachedProcess -FilePath "cmd.exe" -WorkingDirectory $Root -Arguments @("/c", "pnpm", "--filter", "@novo/frontend", "dev")
    }
    "all" {
        Set-Location $Root
        docker compose --env-file .env -f infra/compose/docker-compose.core.yml up -d
        Start-Sleep -Seconds 2
        Start-DetachedProcess -FilePath "python.exe" -WorkingDirectory (Join-Path $Root "backend") -Arguments @("-m", "uvicorn", "novo.main:app", "--reload", "--app-dir", "src", "--host", "127.0.0.1", "--port", "8000")
        Start-Sleep -Seconds 2
        Start-DetachedProcess -FilePath "cmd.exe" -WorkingDirectory $Root -Arguments @("/c", "pnpm", "--filter", "@novo/frontend", "dev")
        Write-Host "NOVO dev environment is starting in the background."
        Write-Host "Frontend: http://127.0.0.1:3000"
        Write-Host "Backend:  http://127.0.0.1:8000"
    }
}