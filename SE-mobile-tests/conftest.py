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


@pytest.fixture(scope="function")
def playwright_instance() -> Playwright:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="function")
def device_name(request: pytest.FixtureRequest) -> str:
    marker = request.node.get_closest_marker("mobile_device")
    выбранное_устройство = str(marker.args[0]) if marker and marker.args else УСТРОЙСТВА[0]
    if выбранное_устройство not in УСТРОЙСТВА:
        raise pytest.UsageError(
            f"Неизвестное устройство '{выбранное_устройство}'. Допустимые: {УСТРОЙСТВА}"
        )
    return выбранное_устройство


@pytest.fixture(scope="function")
def browser(playwright_instance: Playwright) -> Browser:
    headless = os.getenv("HEADLESS") == "1"
    allow_insecure = os.getenv("ALLOW_INSECURE") == "1"
    base_url = os.getenv("BASE_URL", "").strip().rstrip("/")
    launch_args: list[str] = []
    if allow_insecure and base_url:
        launch_args.extend(
            [
                "--allow-running-insecure-content",
                f"--unsafely-treat-insecure-origin-as-secure={base_url}",
            ]
        )
    браузер = playwright_instance.chromium.launch(headless=headless, args=launch_args)
    yield браузер
    браузер.close()


@pytest.fixture(scope="function")
def context(
    browser: Browser,
    playwright_instance: Playwright,
    device_name: str,
) -> BrowserContext:
    профиль_устройства = playwright_instance.devices[device_name]
    allow_insecure = os.getenv("ALLOW_INSECURE") == "1"
    контекст = browser.new_context(**профиль_устройства, ignore_https_errors=allow_insecure)
    контекст.set_default_navigation_timeout(ТАЙМАУТ_НАВИГАЦИИ_МС)
    контекст.set_default_timeout(ТАЙМАУТ_НАВИГАЦИИ_МС)
    yield контекст
    контекст.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    страница = context.new_page()
    yield страница
    страница.close()
