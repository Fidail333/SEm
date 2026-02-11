$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $Root "venv"
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
$Requirements = Join-Path $Root "requirements.txt"

Write-Host "=== Настройка окружения SE-mobile-tests ===" -ForegroundColor Cyan

if (-not (Test-Path $VenvPath)) {
    Write-Host "[1/6] Создаю виртуальное окружение: $VenvPath" -ForegroundColor Yellow
    python -m venv $VenvPath
} else {
    Write-Host "[1/6] Виртуальное окружение уже существует: $VenvPath" -ForegroundColor Green
}

Write-Host "[2/6] Активирую виртуальное окружение" -ForegroundColor Yellow
. $ActivateScript

Write-Host "[3/6] Обновляю pip" -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host "[4/6] Устанавливаю зависимости из requirements.txt" -ForegroundColor Yellow
pip install -r $Requirements

Write-Host "[5/6] Устанавливаю браузеры Playwright" -ForegroundColor Yellow
python -m playwright install

Write-Host "[6/6] Проверяю наличие Allure" -ForegroundColor Yellow
$allureCmd = Get-Command allure -ErrorAction SilentlyContinue
if ($null -ne $allureCmd) {
    Write-Host "Allure уже установлен: $($allureCmd.Source)" -ForegroundColor Green
} else {
    Write-Host "Allure не найден в PATH." -ForegroundColor Yellow
    $chocoCmd = Get-Command choco -ErrorAction SilentlyContinue
    if ($null -ne $chocoCmd) {
        Write-Host "Пробую установить Allure через Chocolatey..." -ForegroundColor Yellow
        choco install allure -y
    } else {
        Write-Host "Chocolatey не найден. Установите Allure вручную:" -ForegroundColor Red
        Write-Host "1) Скачайте архив с https://github.com/allure-framework/allure2/releases" -ForegroundColor Red
        Write-Host "2) Распакуйте в удобную папку (например, C:\Tools\allure)" -ForegroundColor Red
        Write-Host "3) Добавьте C:\Tools\allure\bin в переменную PATH" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Готово. Полезные команды:" -ForegroundColor Cyan
Write-Host ".\scripts\run.ps1" -ForegroundColor White
Write-Host "`$env:HEADLESS='0'; pytest -q --alluredir=allure-results" -ForegroundColor White
