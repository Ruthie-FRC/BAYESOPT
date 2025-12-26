# Terminal initialization script for BayesOpt (PowerShell)
# This script is automatically run when opening a PowerShell terminal in VS Code
# It activates the Python virtual environment if it exists

$bayesoptRoot = $PSScriptRoot | Split-Path -Parent
$venvPath = Join-Path $bayesoptRoot ".venv"

# Check for Windows-style activation script first, then Unix-style
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    $venvActivate = Join-Path $venvPath "bin/Activate.ps1"
}

# Check if virtual environment exists
if (Test-Path $venvActivate) {
    # Activate the virtual environment
    & $venvActivate
    Write-Host "✓ Virtual environment activated (.venv)" -ForegroundColor Green
} else {
    Write-Host "ℹ Virtual environment not found. Run START.bat to create it." -ForegroundColor Yellow
}
