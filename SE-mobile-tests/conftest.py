from __future__ import annotations

import os
from pathlib import Path
from typing import List

import pytest
from playwright.sync_api import Browser, BrowserContext, Playwright, sync_playwright

BASE_DIR = Path(__file__).resolve().parent
URLS_FILE = BASE_DIR / "config" / "urls_mobile.txt"
DEVICE_NAME = "iPhone 13"
NAVIGATION_TIMEOUT_MS = 30_000


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


@pytest.fixture(scope="session")
def mobile_urls() -> List[str]:
    urls = [line.strip() for line in URLS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not urls:
        pytest.fail(f"В файле со списком URL нет данных: {URLS_FILE}")
    return urls


@pytest.fixture(scope="session")
def playwright_instance() -> Playwright:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Browser:
    headless = _to_bool(os.getenv("HEADLESS", "1"))
    browser_instance = playwright_instance.chromium.launch(headless=headless)
    yield browser_instance
    browser_instance.close()


@pytest.fixture
def context(browser: Browser, playwright_instance: Playwright) -> BrowserContext:
    device = playwright_instance.devices[DEVICE_NAME]
    context_instance = browser.new_context(**device)
    context_instance.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
    context_instance.set_default_timeout(NAVIGATION_TIMEOUT_MS)
    yield context_instance
    context_instance.close()


@pytest.fixture
def page(context: BrowserContext):
    page_instance = context.new_page()
    yield page_instance
    page_instance.close()
