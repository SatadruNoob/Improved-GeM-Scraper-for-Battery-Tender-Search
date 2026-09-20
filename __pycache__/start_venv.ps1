# -------------------------------
# Start GeM Portal Scraper venv
# -------------------------------

# Project directory
$projectPath = "E:\GeM Portal Scraper"

# Virtual environment activation script
$venvActivate = "$projectPath\.venv\Scripts\Activate.ps1"

# Navigate to project folder
Set-Location $projectPath

# Activate virtual environment
if (Test-Path $venvActivate) {
    & $venvActivate
    Write-Host "Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "ERROR: Virtual environment not found at $venvActivate" -ForegroundColor Red
}
