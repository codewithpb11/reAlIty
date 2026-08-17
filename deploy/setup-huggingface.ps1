# reAlIty — Hugging Face Deployment Script (Windows PowerShell)
# Run this from the project root folder (App-reAlIty)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  reAlIty Deployment to Hugging Face" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check for huggingface-cli
Write-Host "[Step 1/5] Checking huggingface-cli..." -ForegroundColor Yellow
try {
    $hfVersion = huggingface-cli --version 2>$null
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "  Found: $hfVersion" -ForegroundColor Green
} catch {
    Write-Host "  huggingface-cli not found. Installing..." -ForegroundColor Red
    pip install huggingface-hub
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install huggingface-hub. Run: pip install huggingface-hub" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Login check
Write-Host ""
Write-Host "[Step 2/5] Checking Hugging Face login..." -ForegroundColor Yellow
$huggingfaceTokenDir = "$env:USERPROFILE\.cache\huggingface"
if (-not (Test-Path $huggingfaceTokenDir)) {
    Write-Host "  You need to log in to Hugging Face first." -ForegroundColor Red
    Write-Host "  Run this command and follow prompts:" -ForegroundColor White
    Write-Host "    huggingface-cli login" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Get your token from: https://huggingface.co/settings/tokens" -ForegroundColor White
    exit 1
}
Write-Host "  Logged in." -ForegroundColor Green

# Step 3: Get username
Write-Host ""
Write-Host "[Step 3/5] Getting your Hugging Face username..." -ForegroundColor Yellow
$whoamiOutput = huggingface-cli whoami 2>$null
if ($LASTEXITCODE -ne 0 -or -not $whoamiOutput) {
    Write-Host "  Could not determine username. Please log in: huggingface-cli login" -ForegroundColor Red
    exit 1
}
# Extract username from whoami output
$HF_USERNAME = ($whoamiOutput | Select-String "^Organization:\s*(.+)$").Matches.Groups[1].Value.Trim()
if (-not $HF_USERNAME) {
    $HF_USERNAME = ($whoamiOutput | Select-String "^User:\s*(.+)$").Matches.Groups[1].Value.Trim()
}
if (-not $HF_USERNAME) {
    $HF_USERNAME = Read-Host "Enter your Hugging Face username"
}
Write-Host "  Username: $HF_USERNAME" -ForegroundColor Green

# Step 4: Upload model
Write-Host ""
Write-Host "[Step 4/5] Uploading model to Hugging Face Hub..." -ForegroundColor Yellow
$MODEL_DIR = "reality-finetuned/final"
if (-not (Test-Path $MODEL_DIR)) {
    Write-Host "  ERROR: Model directory not found: $MODEL_DIR" -ForegroundColor Red
    Write-Host "  Make sure you're running this from the project root." -ForegroundColor Red
    exit 1
}

$REPO_ID = "$HF_USERNAME/reality-detector-model"
Write-Host "  Target repo: $REPO_ID" -ForegroundColor White

# Create repo if not exists
huggingface-cli repo create reality-detector-model --type model --yes 2>$null

# Upload files
$modelFiles = Get-ChildItem -Path $MODEL_DIR -File
foreach ($file in $modelFiles) {
    Write-Host "  Uploading: $($file.Name) ($([math]::Round($file.Length/1MB, 1)) MB)..." -ForegroundColor White
    huggingface-cli upload $REPO_ID "$($file.FullName)" $file.Name
}

Write-Host "  Model uploaded!" -ForegroundColor Green
Write-Host "  URL: https://huggingface.co/$REPO_ID" -ForegroundColor Cyan

# Step 5: Update detector.py
Write-Host ""
Write-Host "[Step 5/5] Updating detector.py to use Hugging Face model..." -ForegroundColor Yellow
$detectorPath = "detector.py"
$detectorContent = Get-Content $detectorPath -Raw
$newModelLine = "MODEL_ID = `"$REPO_ID`"   # loaded from Hugging Face Hub"

if ($detectorContent -match 'MODEL_ID\s*=\s*"[^"]+"') {
    $detectorContent = $detectorContent -replace 'MODEL_ID\s*=\s*"[^"]+"', $newModelLine
    Set-Content -Path $detectorPath -Value $detectorContent -NoNewline
    Write-Host "  Updated detector.py" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Could not auto-update detector.py. Please change MODEL_ID manually to:" -ForegroundColor Yellow
    Write-Host "    $newModelLine" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT READY!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Commit and push your code to GitHub" -ForegroundColor White
Write-Host "  2. Create a Hugging Face Space at: https://huggingface.co/spaces" -ForegroundColor White
Write-Host "     - Name it: reality-detector" -ForegroundColor White
Write-Host "     - SDK: Docker" -ForegroundColor White
Write-Host "  3. Connect your GitHub repo to the Space" -ForegroundColor White
Write-Host "  4. Your API will be live at: https://$HF_USERNAME-reality-detector.hf.space" -ForegroundColor Cyan
Write-Host ""
Write-Host "Then update mobile-app/App.js:" -ForegroundColor White
Write-Host "  const API_URL = 'https://$HF_USERNAME-reality-detector.hf.space';" -ForegroundColor Cyan
Write-Host ""
