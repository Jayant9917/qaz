param(
    [ValidateSet("backend", "frontend", "all")]
    [string]$Target = "backend"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

if ($Target -eq "backend" -or $Target -eq "all") {
    Set-Location (Join-Path $Root "backend")
    python -m pytest
}

if ($Target -eq "frontend" -or $Target -eq "all") {
    Set-Location $Root
    pnpm --filter @novo/frontend test
}
