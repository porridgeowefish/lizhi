param(
    [Parameter(Mandatory = $true)]
    [string]$Host,
    [string]$User = "root",
    [int]$Port = 22,
    [string]$TargetDir = "/opt/campus-opportunity",
    [string]$RemoteEnvPath = "/etc/campus-opportunity/backend.env",
    [string]$Domain = "_",
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$DeployDir = Join-Path $Root ".run\deploy"
$BundlePath = Join-Path $DeployDir "campus-opportunity-deploy.tar.gz"
$RemoteBundle = "/tmp/campus-opportunity-deploy.tar.gz"
$RemoteScript = "/tmp/campus-opportunity-remote-deploy.sh"

New-Item -ItemType Directory -Force -Path $DeployDir | Out-Null

if (-not $SkipFrontendBuild) {
    Write-Host "Building frontend production bundle..."
    Push-Location (Join-Path $Root "frontend")
    try {
        & npm.cmd run build
    } finally {
        Pop-Location
    }
}

if (Test-Path $BundlePath) {
    Remove-Item $BundlePath -Force
}

Write-Host "Packaging deploy bundle..."
& tar.exe `
    --exclude "__pycache__" `
    --exclude "*.pyc" `
    --exclude "*.pyo" `
    --exclude "*.db" `
    --exclude "*.sqlite" `
    --exclude "backend/data" `
    --exclude "data" `
    -czf $BundlePath -C $Root `
    backend/app `
    backend/requirements.txt `
    backend/README.md `
    frontend/dist `
    scripts/cloud

Write-Host "Uploading bundle to $User@$Host ..."
& scp.exe -P $Port $BundlePath "${User}@${Host}:${RemoteBundle}"
& scp.exe -P $Port (Join-Path $Root "scripts\cloud\remote-deploy.sh") "${User}@${Host}:${RemoteScript}"

$RemoteCommand = @"
export TARGET_DIR='$TargetDir'
export REMOTE_ENV_PATH='$RemoteEnvPath'
export DOMAIN='$Domain'
bash '$RemoteScript' '$RemoteBundle'
"@

Write-Host "Running remote deploy..."
& ssh.exe -p $Port "${User}@${Host}" $RemoteCommand

Write-Host ""
Write-Host "Deploy finished."
Write-Host "Backend health should be available at: http://$Host/api/health"
