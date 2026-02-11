# Автотесты MOBILE WEB для Sport-Express

Production-ready проект автотестов для проверки мобильной версии сайта Sport-Express.

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
 ├── conftest.py
 ├── pytest.ini
 ├── requirements.txt
 └── README.md
```

## Команды

### 1) Установка

```bash
pip install -r requirements.txt
playwright install
```

### 2) Запуск headless

```bash
pytest -q --alluredir=allure-results
```

### 3) Запуск с открытым браузером (PowerShell)

```powershell
$env:HEADLESS="0"; pytest -q --alluredir=allure-results
```

### 4) Allure

```bash
allure serve allure-results
```

## Что проверяет каждый тест
- открытие страницы через `page.goto(url, wait_until="domcontentloaded")`;
- наличие объекта `response`;
- HTTP-статус только `200` или `304`;
- отсутствие ошибок браузерной консоли (`type == "error"`);
- при падении: скриншот, URL, статус ответа и ошибки консоли прикладываются в Allure.

## Параметры запуска
- Эмуляция устройства: **iPhone 13** (`playwright.devices`).
- Браузер: **Chromium**.
- `HEADLESS=1` по умолчанию.
- Если `HEADLESS=0`, тесты запускаются в видимом режиме.
- Таймаут навигации: `30000 ms`.
- Таймаут теста: `60000 ms`.
- Повторы упавшего теста: `2` (задержка `2` секунды).
