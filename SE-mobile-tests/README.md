# SE Mobile Tests

Production-ready smoke suite for **mobile web** checks of Sport-Express.

## Stack
- Python 3.11+
- pytest
- Playwright (sync API)
- allure-pytest
- pytest-rerunfailures
- pytest-timeout

## Project structure

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

## Installation

1. Create and activate virtual environment (Windows example):

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install Playwright browser:

```bash
python -m playwright install chromium
```

## Running tests

### Headless mode (default)

```bash
set HEADLESS=1
pytest --alluredir=allure-results
```

### With visible browser

```bash
set HEADLESS=0
pytest --alluredir=allure-results
```

## Allure report

Generate report:

```bash
allure generate allure-results --clean -o allure-report
```

Open report:

```bash
allure open allure-report
```

## What is validated for each URL
- open page with `page.goto(url, wait_until="domcontentloaded")`
- assert `response` is not `None`
- assert HTTP status is in `[200, 304]`
- collect browser console messages with `type == "error"`
- fail test if any console errors are found
- on failure attach screenshot + console errors to Allure
