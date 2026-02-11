# Автотесты MOBILE WEB для Sport-Express

Production-ready проект автотестов для smoke-проверки мобильной версии Sport-Express на двух устройствах одновременно:
- iPhone 13 (iOS)
- Pixel 7 (Android)

## Технологии
- Python 3.11+
- pytest
- Playwright (sync API)
- allure-pytest
- pytest-rerunfailures
- pytest-timeout

## Структура проекта

```text
SE-mobile-tests/
 ├── tests/
 │    └── test_mobile_smoke_urls.py
 ├── config/
 │    └── urls_mobile.txt
 ├── utils/
 │    ├── загрузчик_url.py
 │    └── сборщик_консоли.py
 ├── scripts/
 │    ├── setup.ps1
 │    └── run.ps1
 ├── conftest.py
 ├── pytest.ini
 ├── requirements.txt
 └── README.md
```

## Быстрый старт (Windows PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

## Запуск

```powershell
.\scripts\run.ps1
```

## Ручной запуск

```powershell
pip install -r requirements.txt
python -m playwright install
pytest -q --alluredir=allure-results
allure serve allure-results
```

## Запуск с открытым браузером

```powershell
$env:HEADLESS="0"; pytest -q --alluredir=allure-results
```

## Что именно проверяют тесты
- Каждый URL из `config/urls_mobile.txt` прогоняется 2 раза:
  - на `devices["iPhone 13"]`
  - на `devices["Pixel 7"]`
- Название теста в Allure: `Мобайл смоук | {device_name} | {url}`.
- Навигация: `page.goto(url, wait_until="domcontentloaded")`.
- Стабилизация после открытия:
  1. попытка дождаться `networkidle` (до 20 сек, без падения);
  2. пауза 800 мс;
  3. ожидание `document.readyState === "complete"`;
  4. проверка, что `document.body` существует и содержит текст.
- Проверка HTTP-статусов:
  - для `https://m.sport-express.ru/asdasdasd/` ожидается `404`;
  - для всех остальных URL допустимы: `200`, `301`, `302`, `304`;
  - `response == None` всегда приводит к падению.
- Ошибки консоли (`console.type == "error"`) собираются и прикладываются в Allure как
  `Ошибки консоли (не блокируют)`, но не валят тест.
- Скриншот прикладывается **только при падении**.

## Повторы упавших тестов
Настроено через `pytest-rerunfailures`:
- `--reruns 2`
- `--reruns-delay 2`

## Формат файла URL
Файл `config/urls_mobile.txt` поддерживает:
- пустые строки (игнорируются);
- строки, начинающиеся с `#` (игнорируются);
- пробелы в начале/конце (удаляются через `strip()`).
