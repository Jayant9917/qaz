param(
    [ValidateSet("backend", "frontend", "infra", "all")]
    [string]$Target = "all",
    [string]$WslDistro = "Ubuntu"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$WslFrontendPath = "/mnt/d/NOVO/frontend"

function Start-DevProcess {
    param(
        [string]$FilePath,
        [string]$WorkingDirectory,
        [string[]]$Arguments
    )

    Start-Process -FilePath $FilePath -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -NoNewWindow -PassThru
}

function Invoke-WslFrontend {
    param(
        [string]$Distro
    )

    Write-Host "Starting frontend in WSL distro '$Distro'..." -ForegroundColor Cyan
    & wsl.exe -d $Distro -- bash -lc "cd $WslFrontendPath && export NEXT_TELEMETRY_DISABLED=1 && pnpm dev"
}

function Stop-DevProcessTree {
    param(
        [System.Diagnostics.Process[]]$Processes
    )

    foreach ($process in $Processes) {
        if ($null -ne $process -and -not $process.HasExited) {
            try {
                & taskkill /PID $process.Id /T /F | Out-Null
            } catch {
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

function Wait-DevProcesses {
    param(
        [System.Diagnostics.Process[]]$Processes
    )

    while ($true) {
        $alive = @($Processes | Where-Object { -not $_.HasExited })
        if ($alive.Count -eq 0) {
            return
        }

        $exited = @($Processes | Where-Object { $_.HasExited })
        if ($exited.Count -gt 0) {
            $first = $exited | Select-Object -First 1
            Write-Host "Process $($first.Id) exited with code $($first.ExitCode). Stopping the remaining dev processes..." -ForegroundColor Yellow
            return
        }

        Start-Sleep -Seconds 1
    }
}

$processes = @()

try {
    switch ($Target) {
        "infra" {
            Set-Location $Root
            docker compose --env-file .env -f infra/compose/docker-compose.core.yml up -d
        }
        "backend" {
            $backend = Start-DevProcess -FilePath "python.exe" -WorkingDirectory (Join-Path $Root "backend") -Arguments @(
                "-m", "uvicorn", "novo.main:app",
                "--reload",
                "--app-dir", "src",
                "--host", "127.0.0.1",
                "--port", "8000"
            )
            $processes = @($backend)
            Write-Host "Backend listening on http://127.0.0.1:8000"
            Wait-DevProcesses -Processes $processes
        }
        "frontend" {
            Write-Host "Frontend listening on http://127.0.0.1:3000 (WSL: $WslDistro)"
            Invoke-WslFrontend -Distro $WslDistro
        }
        "all" {
            Set-Location $Root
            docker compose --env-file .env -f infra/compose/docker-compose.core.yml up -d
            Start-Sleep -Seconds 2

            $backend = Start-DevProcess -FilePath "python.exe" -WorkingDirectory (Join-Path $Root "backend") -Arguments @(
                "-m", "uvicorn", "novo.main:app",
                "--reload",
                "--app-dir", "src",
                "--host", "127.0.0.1",
                "--port", "8000"
            )

            $processes = @($backend)
            Write-Host "NOVO dev environment is running in the current terminal." -ForegroundColor Green
            Write-Host "Frontend: http://127.0.0.1:3000 (WSL: $WslDistro)"
            Write-Host "Backend:  http://127.0.0.1:8000"
            Write-Host "Press Ctrl+C to stop the backend and frontend processes."

            try {
                Invoke-WslFrontend -Distro $WslDistro
            } finally {
                Stop-DevProcessTree -Processes $processes
            }
        }
    }
}
finally {
    if ($processes.Count -gt 0) {
        Stop-DevProcessTree -Processes $processes
    }
}
