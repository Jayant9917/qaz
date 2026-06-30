param(
    [ValidateSet("backend", "frontend", "infra", "all")]
    [string]$Target = "all",
    [string]$WslDistro = "Ubuntu",
    [switch]$ResetPorts
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

function Get-WslIp {
    param(
        [string]$Distro
    )

    $ip = & wsl.exe -d $Distro -- bash -lc "hostname -I | tr -s ' ' | cut -d' ' -f1"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to detect the WSL IP for distro '$Distro'."
    }

    $ip = ($ip | Select-Object -First 1).Trim()
    if ([string]::IsNullOrWhiteSpace($ip)) {
        throw "WSL IP lookup returned an empty value for distro '$Distro'."
    }

    return $ip
}

function Start-WslLocalhostProxy {
    param(
        [string]$Distro,
        [int]$ListenPort = 3000,
        [int]$TargetPort = 3000
    )

    $targetHost = Get-WslIp -Distro $Distro
    Write-Host "Proxying http://127.0.0.1:$ListenPort -> $targetHost`:$TargetPort" -ForegroundColor Cyan

    return Start-DevProcess -FilePath "node.exe" -WorkingDirectory $Root -Arguments @(
        "scripts/wsl-localhost-proxy.mjs",
        "--listen-host", "127.0.0.1",
        "--listen-port", "$ListenPort",
        "--target-host", $targetHost,
        "--target-port", "$TargetPort"
    )
}

function Stop-WslFrontendProcess {
    param(
        [string]$Distro
    )

    Write-Host "Stopping any existing WSL frontend process on port 3000..." -ForegroundColor Yellow
    & wsl.exe -d $Distro -- bash -lc "cd $WslFrontendPath && (pkill -f 'next dev' || true)"
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

function Stop-PortListeners {
    param(
        [int[]]$Ports
    )

    foreach ($port in $Ports) {
        $processIds = @(
            Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
                Select-Object -ExpandProperty OwningProcess -Unique
        )

        if ($processIds.Count -eq 0) {
            Write-Host "Port $port is free." -ForegroundColor DarkGray
            continue
        }

        foreach ($processId in $processIds) {
            if ($null -eq $processId -or $processId -le 0) {
                continue
            }

            try {
                $process = Get-Process -Id $processId -ErrorAction Stop
                Write-Host "Stopping $($process.ProcessName) (PID $processId) on port $port..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force -ErrorAction Stop
            } catch {
                Write-Host "Stopping PID $processId on port $port..." -ForegroundColor Yellow
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
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
    if ($ResetPorts.IsPresent) {
        switch ($Target) {
            "backend" { Stop-PortListeners -Ports @(8000) }
            "frontend" { Stop-PortListeners -Ports @(3000) }
            "all" { Stop-PortListeners -Ports @(3000, 8000) }
        }
    }

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
            $proxy = Start-WslLocalhostProxy -Distro $WslDistro
            $processes = @($proxy)
            Stop-WslFrontendProcess -Distro $WslDistro
            Write-Host "Frontend listening on http://127.0.0.1:3000 (via WSL distro: $WslDistro)"
            Write-Host "If localhost does not open immediately, give the proxy a second to settle."
            try {
                Invoke-WslFrontend -Distro $WslDistro
            } finally {
                Stop-DevProcessTree -Processes $processes
            }
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

            $proxy = Start-WslLocalhostProxy -Distro $WslDistro
            $processes = @($backend, $proxy)

            Write-Host "NOVO dev environment is running in the current terminal." -ForegroundColor Green
            Write-Host "Frontend: http://127.0.0.1:3000 (proxied to WSL: $WslDistro)"
            Write-Host "Backend:  http://127.0.0.1:8000"
            Write-Host "Press Ctrl+C to stop the backend, proxy, and frontend processes."

            try {
                Stop-WslFrontendProcess -Distro $WslDistro
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
