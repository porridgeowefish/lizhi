param(
    [switch]$ForceRestart
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$RunDir = Join-Path $Root ".run"
$LogDir = Join-Path $RunDir "logs"
$PidFile = Join-Path $RunDir "dev-stack-pids.json"

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Get-PortProcessId($Port) {
    $connection = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $connection) { return $connection.OwningProcess }
    return $null
}

function Stop-ExistingProcess($Port, $Name) {
    $existingPid = Get-PortProcessId -Port $Port
    if ($null -ne $existingPid) {
        if (-not $ForceRestart) {
            Write-Host "$Name already listening on $Port with PID $existingPid, skipping."
            return $false
        }
        Write-Host "Stopping existing $Name on port $Port (PID $existingPid)..."
        Stop-Process -Id $existingPid -Force
        Start-Sleep -Seconds 1
    }
    return $true
}

function Start-ManagedProcess($Name, $FilePath, $Arguments, $WorkingDirectory, $Port) {
    $stdout = Join-Path $LogDir "$Name.out.log"
    $stderr = Join-Path $LogDir "$Name.err.log"

    if (-not (Stop-ExistingProcess -Port $Port -Name $Name)) {
        return @{ name = $Name; port = $Port; pid = (Get-PortProcessId -Port $Port); reused = $true }
    }

    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -WindowStyle Hidden `
        -PassThru

    return @{ name = $Name; port = $Port; pid = $process.Id; reused = $false }
}

function Wait-ForHttp($Url, $Label) {
    $attempts = 0
    while ($attempts -lt 40) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "$Label is ready at $Url"
                return
            }
        } catch {
        }
        Start-Sleep -Milliseconds 750
        $attempts++
    }
    Write-Warning "$Label did not become ready in time: $Url"
}

$backend = Start-ManagedProcess `
    -Name "backend" `
    -FilePath "python" `
    -Arguments @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8002") `
    -WorkingDirectory (Join-Path $Root "backend") `
    -Port 8002

$frontend = Start-ManagedProcess `
    -Name "frontend" `
    -FilePath "npm.cmd" `
    -Arguments @("run", "dev", "--", "--host", "127.0.0.1", "--port", "3000") `
    -WorkingDirectory (Join-Path $Root "frontend") `
    -Port 3000

$meta = @($backend, $frontend)
$meta | ConvertTo-Json | Set-Content -Encoding UTF8 $PidFile

Wait-ForHttp -Url "http://127.0.0.1:8002/api/health" -Label "Backend"
Wait-ForHttp -Url "http://127.0.0.1:3000" -Label "Frontend"

Write-Host ""
Write-Host "Dev stack started:"
Write-Host "  Backend:         http://127.0.0.1:8002/api/health"
Write-Host "  Frontend:        http://127.0.0.1:3000"
Write-Host ""
Write-Host "Logs:"
Write-Host "  $LogDir"
