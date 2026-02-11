from __future__ import annotations

import os
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Playwright, sync_playwright

from utils.загрузчик_url import загрузить_url_из_файла

КОРЕНЬ_ПРОЕКТА = Path(__file__).resolve().parent
ФАЙЛ_URL = КОРЕНЬ_ПРОЕКТА / "config" / "urls_mobile.txt"
ИМЯ_УСТРОЙСТВА = "iPhone 13"
ТАЙМАУТ_НАВИГАЦИИ_МС = 30_000


def _это_истина(значение: str) -> bool:
    return str(значение).strip().lower() in {"1", "true", "yes", "y", "on"}


@pytest.fixture(scope="session")
def mobile_urls() -> list[str]:
    url_список = загрузить_url_из_файла(ФАЙЛ_URL)
    if not url_список:
        pytest.fail(f"Файл со ссылками пуст: {ФАЙЛ_URL}")
    return url_список


@pytest.fixture(scope="session")
def playwright_instance() -> Playwright:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Browser:
    headless = _это_истина(os.getenv("HEADLESS", "1"))
    браузер = playwright_instance.chromium.launch(headless=headless)
    yield браузер
    браузер.close()


@pytest.fixture
def context(browser: Browser, playwright_instance: Playwright) -> BrowserContext:
    профиль_устройства = playwright_instance.devices[ИМЯ_УСТРОЙСТВА]
    контекст = browser.new_context(**профиль_устройства)
    контекст.set_default_navigation_timeout(ТАЙМАУТ_НАВИГАЦИИ_МС)
    контекст.set_default_timeout(ТАЙМАУТ_НАВИГАЦИИ_МС)
    yield контекст
    контекст.close()


@pytest.fixture
def page(context: BrowserContext):
    страница = context.new_page()
    yield страница
    страница.close()
