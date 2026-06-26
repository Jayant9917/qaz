param(
    [ValidateSet("backend", "frontend", "infra")]
    [string]$Target = "backend"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

switch ($Target) {
    "backend" {
        Set-Location (Join-Path $Root "backend")
        python -m uvicorn novo.main:app --reload --app-dir src
    }
    "frontend" {
        Set-Location $Root
        pnpm --filter @novo/frontend dev
    }
    "infra" {
        Set-Location $Root
        docker compose -f infra/compose/docker-compose.core.yml up -d
    }
}
