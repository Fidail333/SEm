# SE Mobile Tests

Набор **smoke-автотестов** для мобильной web-версии Sport-Express.
Проект ориентирован на стабильный запуск и понятную диагностику падений (скриншоты + ошибки консоли в Allure).

## Стек
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
 │    └── test_mobile_urls.py
 ├── config/
 │    └── urls_mobile.txt
 ├── utils/
 │    └── console_collector.py
 ├── conftest.py
 ├── pytest.ini
 ├── requirements.txt
 └── README.md
```

## Установка (Windows)

1. Создать и активировать виртуальное окружение:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Установить зависимости:

```bash
pip install -r requirements.txt
```

3. Установить браузер Chromium для Playwright:

```bash
python -m playwright install chromium
```

## Запуск тестов

### Headless-режим (по умолчанию)

```bash
set HEADLESS=1
pytest --alluredir=allure-results
```

### Запуск с видимым браузером

```bash
set HEADLESS=0
pytest --alluredir=allure-results
```

## Allure-отчёт

Сгенерировать отчёт:

```bash
allure generate allure-results --clean -o allure-report
```

Открыть отчёт:

```bash
allure open allure-report
```

## Что проверяется для каждого URL
- открытие страницы через `page.goto(url, wait_until="domcontentloaded")`
- проверка, что `response` не `None`
- проверка, что HTTP-статус в `[200, 304]`
- сбор ошибок консоли браузера (`type == "error"`)
- падение теста при наличии ошибок консоли
- при падении: скриншот страницы + диагностическая информация (URL, статус, ошибки консоли) в Allure
