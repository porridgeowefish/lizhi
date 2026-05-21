$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path (Join-Path $Root ".run") "dev-stack-pids.json"

if (-not (Test-Path $PidFile)) {
    Write-Host "No PID file found, nothing to stop."
    exit 0
}

$entries = Get-Content $PidFile | ConvertFrom-Json
foreach ($entry in $entries) {
    if ($entry.reused) {
        Write-Host "Skipping reused process for $($entry.name) on port $($entry.port)."
        continue
    }
    try {
        Stop-Process -Id $entry.pid -Force -ErrorAction Stop
        Write-Host "Stopped $($entry.name) (PID $($entry.pid))."
    } catch {
        Write-Warning "Could not stop $($entry.name) (PID $($entry.pid))."
    }
}

Remove-Item $PidFile -Force
