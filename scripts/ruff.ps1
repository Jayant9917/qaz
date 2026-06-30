param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RuffArgs
)

$ErrorActionPreference = 'Stop'
$cacheDir = Join-Path $PSScriptRoot '..\.cache\ruff'
New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
$env:RUFF_CACHE_DIR = $cacheDir
Set-Location (Join-Path $PSScriptRoot '..\backend')
if ($RuffArgs.Count -eq 0) {
    python -m ruff --help
    exit $LASTEXITCODE
}
$command = $RuffArgs[0]
$remaining = @()
if ($RuffArgs.Count -gt 1) {
    $remaining = $RuffArgs[1..($RuffArgs.Count - 1)]
}
python -m ruff $command --no-cache @remaining