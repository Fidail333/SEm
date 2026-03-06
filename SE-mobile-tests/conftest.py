from __future__ import annotations

import os
from typing import Any

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from utils.загрузчик_кейсов_страниц import загрузить_кейсы_страниц
from utils.сборщик_консоли import СборщикКонсоли

NAVIGATION_TIMEOUT_MS = 30_000

EMULATED_TARGETS: dict[str, str] = {
    "iphone13": "iPhone 13",
    "pixel7": "Pixel 7",
}
REAL_IPHONE_TARGET = "real_iphone"
DEFAULT_TARGETS = ["iphone13", "pixel7"]


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--targets",
        action="store",
        default=",".join(DEFAULT_TARGETS),
        help="Список целей через запятую: iphone13,pixel7,real_iphone",
    )
    parser.addoption(
        "--appium-url",
        action="store",
        default=os.getenv("APPIUM_URL", "http://127.0.0.1:4723"),
        help="URL Appium сервера для реального iPhone",
    )
    parser.addoption(
        "--ios-udid",
        action="store",
        default=os.getenv("IOS_UDID", ""),
        help="UDID подключенного iPhone",
    )
    parser.addoption(
        "--ios-device-name",
        action="store",
        default=os.getenv("IOS_DEVICE_NAME", ""),
        help="Имя iPhone (например, iPhone 15)",
    )
    parser.addoption(
        "--ios-platform-version",
        action="store",
        default=os.getenv("IOS_PLATFORM_VERSION", ""),
        help="Версия iOS (например, 18.3)",
    )
    parser.addoption(
        "--ios-xcode-org-id",
        action="store",
        default=os.getenv("IOS_XCODE_ORG_ID", ""),
        help="Apple Team ID для подписи WebDriverAgent",
    )
    parser.addoption(
        "--ios-xcode-signing-id",
        action="store",
        default=os.getenv("IOS_XCODE_SIGNING_ID", "iPhone Developer"),
        help="Signing ID для подписи WebDriverAgent",
    )
    parser.addoption(
        "--ios-wda-bundle-id",
        action="store",
        default=os.getenv("IOS_WDA_BUNDLE_ID", ""),
        help="Кастомный bundle id для WebDriverAgentRunner",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "real_iphone: тест для физического iPhone через Appium")
    targets = _read_targets(config)
    if REAL_IPHONE_TARGET not in targets:
        return

    numprocesses = config.getoption("numprocesses", default=0)
    if numprocesses in (None, 0, "0", "1", 1):
        return

    raise pytest.UsageError(
        "Для --targets real_iphone запускай pytest без xdist (укажи -n 1)."
    )


def _validate_and_parse_targets(raw_targets: str) -> list[str]:
    allowed = set(EMULATED_TARGETS) | {REAL_IPHONE_TARGET}
    parsed = [item.strip().lower() for item in raw_targets.split(",") if item.strip()]
    if not parsed:
        raise pytest.UsageError("Пустой список --targets. Пример: --targets iphone13,pixel7")

    unknown = [item for item in parsed if item not in allowed]
    if unknown:
        raise pytest.UsageError(
            f"Неизвестные targets: {unknown}. Допустимые: {sorted(allowed)}"
        )

    # Preserve order, remove duplicates.
    return list(dict.fromkeys(parsed))


def _read_targets(config: pytest.Config) -> list[str]:
    return _validate_and_parse_targets(str(config.getoption("--targets")))


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "кейс_страницы" in metafunc.fixturenames or "url" in metafunc.fixturenames:
        кейсы = загрузить_кейсы_страниц()
        if not кейсы:
            raise pytest.UsageError("Список кейсов страниц пуст: config/кейсы_страниц.py")

        if "кейс_страницы" in metafunc.fixturenames:
            ids = [f"{кейс['id']}|{кейс['название']}" for кейс in кейсы]
            metafunc.parametrize("кейс_страницы", кейсы, ids=ids)

        if "url" in metafunc.fixturenames:
            urls = [str(кейс["url"]) for кейс in кейсы]
            metafunc.parametrize("url", urls, ids=urls)

    if "target" in metafunc.fixturenames:
        targets = _read_targets(metafunc.config)
        metafunc.parametrize("target", targets, ids=targets)


@pytest.fixture(scope="session")
def playwright_instance() -> Playwright:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Browser:
    headless = os.getenv("HEADLESS", "0") == "1"
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

    chromium = playwright_instance.chromium.launch(headless=headless, args=launch_args)
    yield chromium
    chromium.close()


@pytest.fixture(scope="function")
def device_name(target: str) -> str:
    if target in EMULATED_TARGETS:
        return EMULATED_TARGETS[target]
    return "Real iPhone (Safari)"


@pytest.fixture(scope="function")
def context(
    browser: Browser,
    playwright_instance: Playwright,
    target: str,
) -> BrowserContext:
    if target not in EMULATED_TARGETS:
        raise RuntimeError("Фикстура context поддерживает только эмулированные девайсы")

    profile_name = EMULATED_TARGETS[target]
    profile = playwright_instance.devices[profile_name]
    allow_insecure = os.getenv("ALLOW_INSECURE") == "1"

    ctx = browser.new_context(**profile, ignore_https_errors=allow_insecure)
    ctx.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
    ctx.set_default_timeout(NAVIGATION_TIMEOUT_MS)
    yield ctx
    ctx.close()


@pytest.fixture(scope="function")
def page(target: str, context: BrowserContext) -> Page:
    if target not in EMULATED_TARGETS:
        raise RuntimeError("Фикстура page поддерживает только эмулированные девайсы")
    tab = context.new_page()
    yield tab
    tab.close()


@pytest.fixture(scope="function")
def console_collector(page: Page) -> СборщикКонсоли:
    collector = СборщикКонсоли()
    collector.подключить(page)
    return collector


def _build_ios_capabilities(config: pytest.Config) -> dict[str, Any]:
    ios_udid = str(config.getoption("--ios-udid")).strip()
    ios_device_name = str(config.getoption("--ios-device-name")).strip()
    ios_platform_version = str(config.getoption("--ios-platform-version")).strip()
    ios_xcode_org_id = str(config.getoption("--ios-xcode-org-id")).strip()
    ios_xcode_signing_id = str(config.getoption("--ios-xcode-signing-id")).strip()
    ios_wda_bundle_id = str(config.getoption("--ios-wda-bundle-id")).strip()

    missing = []
    if not ios_udid:
        missing.append("--ios-udid / IOS_UDID")
    if not ios_device_name:
        missing.append("--ios-device-name / IOS_DEVICE_NAME")
    if not ios_platform_version:
        missing.append("--ios-platform-version / IOS_PLATFORM_VERSION")
    if missing:
        raise pytest.UsageError(
            "Для real_iphone нужно заполнить: " + ", ".join(missing)
        )

    return {
        "platformName": "iOS",
        "browserName": "Safari",
        "appium:automationName": "XCUITest",
        "appium:udid": ios_udid,
        "appium:deviceName": ios_device_name,
        "appium:platformVersion": ios_platform_version,
        "appium:newCommandTimeout": 240,
        "appium:webviewConnectTimeout": 30000,
        "appium:showXcodeLog": True,
        **({"appium:xcodeOrgId": ios_xcode_org_id} if ios_xcode_org_id else {}),
        **({"appium:xcodeSigningId": ios_xcode_signing_id} if ios_xcode_org_id else {}),
        **({"appium:updatedWDABundleId": ios_wda_bundle_id} if ios_wda_bundle_id else {}),
    }


@pytest.fixture(scope="function")
def real_iphone_driver(target: str, request: pytest.FixtureRequest):
    if target != REAL_IPHONE_TARGET:
        pytest.skip("real_iphone_driver вызывается только для target=real_iphone")

    try:
        from appium import webdriver as appium_webdriver
        from appium.options.ios import XCUITestOptions
    except ImportError:  # pragma: no cover - зависит от локальной среды
        pytest.skip(
            "Для real_iphone установи зависимости: pip install -r requirements-ios.txt"
        )

    appium_url = str(request.config.getoption("--appium-url")).strip()
    capabilities = _build_ios_capabilities(request.config)

    options = XCUITestOptions()
    options.load_capabilities(capabilities)

    driver = appium_webdriver.Remote(command_executor=appium_url, options=options)
    driver.set_page_load_timeout(30)
    yield driver
    driver.quit()


@pytest.fixture(scope="function")
def session_runtime(
    request: pytest.FixtureRequest,
    target: str,
    device_name: str,
) -> dict[str, Any]:
    if target == REAL_IPHONE_TARGET:
        ios_driver = request.getfixturevalue("real_iphone_driver")
        return {
            "kind": REAL_IPHONE_TARGET,
            "device_name": device_name,
            "driver": ios_driver,
            "console_collector": None,
        }

    playwright_page = request.getfixturevalue("page")
    collector = request.getfixturevalue("console_collector")
    return {
        "kind": "playwright",
        "device_name": device_name,
        "page": playwright_page,
        "console_collector": collector,
    }
