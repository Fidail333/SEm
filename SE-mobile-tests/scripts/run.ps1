$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $Root "venv"
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"

if (-not (Test-Path $ActivateScript)) {
    Write-Host "Виртуальное окружение не найдено. Сначала выполните .\scripts\setup.ps1" -ForegroundColor Red
    exit 1
}

. $ActivateScript

pytest -q --alluredir=allure-results
allure serve allure-results
