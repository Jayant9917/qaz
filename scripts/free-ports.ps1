param(
    [int[]]$Ports = @(3000, 8000)
)

$ErrorActionPreference = "Stop"

function Stop-PortListeners {
    param(
        [int[]]$PortsToFree
    )

    foreach ($port in $PortsToFree) {
        $processIds = @(
            Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
                Select-Object -ExpandProperty OwningProcess -Unique
        )

        if ($processIds.Count -eq 0) {
            Write-Host "Port $port is already free." -ForegroundColor DarkGray
            continue
        }

        foreach ($pid in $processIds) {
            if ($null -eq $pid -or $pid -le 0) {
                continue
            }

            try {
                $process = Get-Process -Id $pid -ErrorAction Stop
                Write-Host "Stopping $($process.ProcessName) (PID $pid) on port $port..." -ForegroundColor Yellow
                Stop-Process -Id $pid -Force -ErrorAction Stop
            } catch {
                Write-Host "Stopping PID $pid on port $port..." -ForegroundColor Yellow
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

Stop-PortListeners -PortsToFree $Ports
