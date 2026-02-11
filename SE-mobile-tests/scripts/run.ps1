$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $Root "venv"
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
$AllureResults = Join-Path $Root "allure-results"

Write-Host "[1/4] Check virtual environment..."
if (-not (Test-Path $ActivateScript)) {
    Write-Host "Virtual environment not found. Run .\scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "[2/4] Activate virtual environment..."
. $ActivateScript

Write-Host "[3/4] Run pytest with Allure results..."
Set-Location $Root
pytest --alluredir=$AllureResults

Write-Host "[4/4] Open Allure report if Allure CLI exists..."
if (Get-Command allure -ErrorAction SilentlyContinue) {
    allure serve $AllureResults
}
else {
    Write-Host "Allure CLI is not installed or not in PATH."
}
