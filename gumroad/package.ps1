# package.ps1
# Builds a clean Gumroad release zip for reAlIty.
#
# Usage (from project root):
#   powershell -ExecutionPolicy Bypass -File gumroad\package.ps1
#
# Output:
#   gumroad\reAlIty-v1.0.zip

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$StagingDir  = Join-Path $ProjectRoot "gumroad\_staging\reAlIty"
$OutputZip   = Join-Path $ProjectRoot "gumroad\reAlIty-v1.0.zip"
$Version     = "1.0"

# Files to ship
$AppFiles = @(
    "main.py",
    "gui.py",
    "detector.py",
    "media_utils.py",
    "video_utils.py",
    "requirements.txt",
    "LICENSE"
)

$GumroadFiles = @(
    "QUICKSTART.txt",
    "CREDITS.txt"
)

Write-Host "=== reAlIty Gumroad Packager ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"

# --- Preflight checks ---
$ModelDir = Join-Path $ProjectRoot "reality-finetuned\final"
if (-not (Test-Path $ModelDir)) {
    Write-Error "Model not found at $ModelDir — download/unzip the trained model first."
}

$RequiredModelFiles = @(
    "config.json",
    "model.safetensors",
    "preprocessor_config.json"
)
foreach ($f in $RequiredModelFiles) {
    if (-not (Test-Path (Join-Path $ModelDir $f))) {
        Write-Error "Missing model file: $f"
    }
}

foreach ($f in $AppFiles) {
    if (-not (Test-Path (Join-Path $ProjectRoot $f))) {
        Write-Error "Missing app file: $f"
    }
}

# --- Clean staging ---
if (Test-Path $StagingDir) {
    Remove-Item $StagingDir -Recurse -Force
}
New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $StagingDir "reality-finetuned\final") -Force | Out-Null

# --- Copy app files ---
foreach ($f in $AppFiles) {
    Copy-Item (Join-Path $ProjectRoot $f) (Join-Path $StagingDir $f)
    Write-Host "  + $f"
}

foreach ($f in $GumroadFiles) {
    Copy-Item (Join-Path $ProjectRoot "gumroad\$f") (Join-Path $StagingDir $f)
    Write-Host "  + $f"
}

# --- Copy model ---
Write-Host "  + reality-finetuned/final/ (model, ~354 MB — this takes a moment)"
Copy-Item "$ModelDir\*" (Join-Path $StagingDir "reality-finetuned\final") -Recurse

# --- Build zip ---
if (Test-Path $OutputZip) {
    Remove-Item $OutputZip -Force
}

Write-Host ""
Write-Host "Creating zip..." -ForegroundColor Yellow
Compress-Archive -Path $StagingDir -DestinationPath $OutputZip -CompressionLevel Optimal

# --- Cleanup staging ---
Remove-Item (Join-Path $ProjectRoot "gumroad\_staging") -Recurse -Force

# --- Report ---
$ZipSizeMB = [math]::Round((Get-Item $OutputZip).Length / 1MB, 1)
Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host "  Output:  $OutputZip"
Write-Host "  Size:    $ZipSizeMB MB"
Write-Host ""
Write-Host "Next: upload this zip to Gumroad (see gumroad/UPLOAD_GUIDE.md)"
