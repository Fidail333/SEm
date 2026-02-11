from __future__ import annotations

import os
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from utils.загрузчик_url import загрузить_url_из_файла

КОРЕНЬ_ПРОЕКТА = Path(__file__).resolve().parent
ФАЙЛ_URL = КОРЕНЬ_ПРОЕКТА / "config" / "urls_mobile.txt"
УСТРОЙСТВА = ["iPhone 13", "Pixel 7"]
ТАЙМАУТ_НАВИГАЦИИ_МС = 30_000


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "url" in metafunc.fixturenames:
        url_список = загрузить_url_из_файла(ФАЙЛ_URL)
        if not url_список:
            raise pytest.UsageError(f"Файл со ссылками пуст: {ФАЙЛ_URL}")
        metafunc.parametrize("url", url_список, ids=url_список)

    if "device_name" in metafunc.fixturenames:
        metafunc.parametrize("device_name", УСТРОЙСТВА, ids=УСТРОЙСТВА)


@pytest.fixture(scope="function")
def playwright_instance() -> Playwright:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="function")
def browser(playwright_instance: Playwright) -> Browser:
    headless = os.getenv("HEADLESS") == "1"
    браузер = playwright_instance.chromium.launch(headless=headless)
    yield браузер
    браузер.close()


@pytest.fixture(scope="function")
def context(
    browser: Browser,
    playwright_instance: Playwright,
    device_name: str,
) -> BrowserContext:
    профиль_устройства = playwright_instance.devices[device_name]
    контекст = browser.new_context(**профиль_устройства)
    контекст.set_default_navigation_timeout(ТАЙМАУТ_НАВИГАЦИИ_МС)
    контекст.set_default_timeout(ТАЙМАУТ_НАВИГАЦИИ_МС)
    yield контекст
    контекст.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    страница = context.new_page()
    yield страница
    страница.close()
