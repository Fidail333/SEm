from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import allure
import pytest
from playwright.sync_api import Page, Response, TimeoutError as PlaywrightTimeoutError

from utils.сборщик_консоли import СборщикКонсоли

NEGATIVE_PATH = "/asdasdasd/"
ALLOWED_STATUS_CODES = {200, 301, 302, 304}
ARTIFACTS_DIR = Path("artifacts")


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _safe_name(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")[:180]


def _stable_allure_id(target: str, url: str) -> str:
    digest = hashlib.sha1(f"{target}|{url}".encode("utf-8")).hexdigest()
    return str(int(digest[:12], 16))


def _get_playwright_emulation_params(page: Page) -> str:
    user_agent = page.evaluate("() => navigator.userAgent")
    viewport = page.viewport_size
    width = viewport.get("width") if viewport else "N/A"
    height = viewport.get("height") if viewport else "N/A"
    return f"User-Agent: {user_agent}\nViewport: {width}x{height}\n"


def _get_real_iphone_params(driver: Any) -> str:
    user_agent = driver.execute_script("return navigator.userAgent")
    width = driver.execute_script("return window.innerWidth")
    height = driver.execute_script("return window.innerHeight")
    return f"User-Agent: {user_agent}\nViewport: {width}x{height}\n"


def _probe_http_status_without_redirects(url: str) -> int | None:
    opener = build_opener(_NoRedirectHandler())
    request = Request(url, method="GET", headers={"User-Agent": "SE-mobile-status-probe"})
    try:
        with opener.open(request, timeout=30) as response:
            return int(response.getcode())
    except HTTPError as exc:
        return int(exc.code)
    except URLError:
        return None


def _assert_expected_status(url: str, status_code: int) -> None:
    if urlparse(url).path.rstrip("/") == NEGATIVE_PATH.rstrip("/"):
        assert status_code == 404, (
            f"Для негативного URL ожидается статус 404, фактический статус: {status_code}"
        )
        return

    assert status_code in ALLOWED_STATUS_CODES, (
        "Недопустимый HTTP статус: "
        f"{status_code}. Допустимые: {sorted(ALLOWED_STATUS_CODES)}"
    )


def _attach_console_state(collector: СборщикКонсоли | None) -> None:
    if collector is None:
        allure.attach(
            "Сбор ошибок консоли недоступен для real_iphone (Safari/Appium).",
            name="Console state",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    if collector.количество_ошибок > 0:
        allure.dynamic.severity(allure.severity_level.MINOR)
        allure.dynamic.tag("console-warning")
        allure.attach(
            f"Количество ошибок консоли: {collector.количество_ошибок}\n\n{collector.как_текст()}",
            name="Console errors (non-blocking)",
            attachment_type=allure.attachment_type.TEXT,
        )
    else:
        allure.dynamic.severity(allure.severity_level.TRIVIAL)
        allure.attach(
            "Ошибок консоли не обнаружено",
            name="No console errors",
            attachment_type=allure.attachment_type.TEXT,
        )


def _run_playwright_smoke(url: str, device_name: str, runtime: dict[str, Any]) -> None:
    page: Page = runtime["page"]
    collector: СборщикКонсоли = runtime["console_collector"]
    response: Response | None = None

    try:
        with allure.step("Сохраняю параметры эмуляции"):
            allure.attach(
                _get_playwright_emulation_params(page),
                name="Device emulation",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Открываю страницу"):
            response = page.goto(url, wait_until="domcontentloaded")

        with allure.step("Жду networkidle (непадающе)"):
            try:
                page.wait_for_load_state("networkidle", timeout=20_000)
            except PlaywrightTimeoutError:
                allure.attach(
                    "networkidle не достигнут за 20 сек. Продолжаю тест.",
                    name="Network idle warning",
                    attachment_type=allure.attachment_type.TEXT,
                )

        with allure.step("Стабилизационная пауза"):
            page.wait_for_timeout(800)

        with allure.step("Жду readyState=complete"):
            page.wait_for_function("document.readyState === 'complete'", timeout=20_000)

        with allure.step("Проверяю текстовый контент"):
            page.wait_for_function(
                "document.body && document.body.innerText && document.body.innerText.length > 0",
                timeout=20_000,
            )

        with allure.step("Проверяю HTTP-статус"):
            assert response is not None, "Переход не вернул объект ответа"
            _assert_expected_status(url, response.status)

    except Exception:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        file_name = _safe_name(f"{device_name}_{url}")
        screenshot_path = ARTIFACTS_DIR / f"{file_name}.png"

        page.screenshot(path=str(screenshot_path), full_page=True)
        allure.attach.file(
            str(screenshot_path),
            name=f"Screenshot_{file_name}",
            attachment_type=allure.attachment_type.PNG,
        )

        status_text = response.status if response is not None else "response is None"
        allure.attach(
            (
                f"Device: {device_name}\n"
                f"URL: {url}\n"
                f"Status: {status_text}\n"
                f"Console errors: {collector.количество_ошибок}\n"
                f"Console details:\n{collector.как_текст()}\n"
            ),
            name="Failure diagnostics",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise
    finally:
        with allure.step("Фиксирую состояние консоли"):
            _attach_console_state(collector)


def _run_real_iphone_smoke(url: str, device_name: str, runtime: dict[str, Any]) -> None:
    driver = runtime["driver"]
    status_code: int | None = None

    try:
        from selenium.webdriver.support.ui import WebDriverWait
    except Exception as exc:  # pragma: no cover - зависит от локальной среды
        raise RuntimeError("Selenium не установлен. Установи requirements-ios.txt") from exc

    try:
        with allure.step("Сохраняю параметры реального iPhone"):
            allure.attach(
                _get_real_iphone_params(driver),
                name="Real iPhone capabilities",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Пробую получить HTTP-статус (без редиректов)"):
            status_code = _probe_http_status_without_redirects(url)
            allure.attach(
                f"Пробный статус: {status_code}",
                name="HTTP status probe",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Открываю страницу в Safari на iPhone"):
            driver.get(url)

        with allure.step("Жду readyState=complete"):
            WebDriverWait(driver, 20).until(
                lambda drv: drv.execute_script("return document.readyState") == "complete"
            )

        with allure.step("Проверяю, что на странице есть текст"):
            WebDriverWait(driver, 20).until(
                lambda drv: int(
                    drv.execute_script(
                        "return document.body && document.body.innerText ? document.body.innerText.length : 0"
                    )
                    or 0
                )
                > 0
            )

        with allure.step("Проверяю HTTP-статус"):
            if status_code is None:
                allure.dynamic.severity(allure.severity_level.MINOR)
                allure.dynamic.tag("status-probe-unavailable")
                allure.attach(
                    "Не удалось определить HTTP-статус probe-запросом с хоста. "
                    "Проверка статуса для real_iphone пропущена.",
                    name="HTTP status probe warning",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                _assert_expected_status(url, status_code)

    except Exception:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        file_name = _safe_name(f"{device_name}_{url}")
        screenshot_path = ARTIFACTS_DIR / f"{file_name}.png"

        png_data = driver.get_screenshot_as_png()
        screenshot_path.write_bytes(png_data)
        allure.attach(
            png_data,
            name=f"Screenshot_{file_name}",
            attachment_type=allure.attachment_type.PNG,
        )

        allure.attach(
            (
                f"Device: {device_name}\n"
                f"URL: {url}\n"
                f"Status probe: {status_code}\n"
            ),
            name="Failure diagnostics",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise
    finally:
        with allure.step("Фиксирую состояние консоли"):
            _attach_console_state(None)


def _run_playwright_interaction_smoke(url: str, device_name: str, runtime: dict[str, Any]) -> None:
    page: Page = runtime["page"]
    collector: СборщикКонсоли = runtime["console_collector"]
    clicked_href: str | None = None

    try:
        with allure.step("Открываю страницу для интерактивной проверки"):
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_function("document.readyState === 'complete'", timeout=20_000)

        with allure.step("Кликаю по первой валидной ссылке"):
            clicked_href = page.evaluate(
                """
                () => {
                    const links = Array.from(document.querySelectorAll("a[href]"));
                    const candidate = links.find((link) => {
                        const href = (link.getAttribute("href") || "").trim().toLowerCase();
                        const target = (link.getAttribute("target") || "").trim().toLowerCase();
                        if (!href || href.startsWith("#") || href.startsWith("javascript:")) return false;
                        if (href.startsWith("mailto:") || href.startsWith("tel:")) return false;
                        if (target === "_blank") return false;
                        return true;
                    });
                    if (!candidate) return null;
                    candidate.scrollIntoView({block: "center"});
                    const resolvedHref = candidate.href || candidate.getAttribute("href") || "";
                    candidate.click();
                    return resolvedHref || null;
                }
                """
            )
            assert clicked_href, "На странице не найдена кликабельная ссылка для интерактивного smoke."
            allure.attach(
                f"Clicked href: {clicked_href}",
                name="Clicked link",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Проверяю состояние после клика"):
            try:
                page.wait_for_load_state("domcontentloaded", timeout=20_000)
            except PlaywrightTimeoutError:
                pass

            page.wait_for_timeout(700)
            after_url = page.url
            body_len = int(
                page.evaluate(
                    "(() => document.body && document.body.innerText ? document.body.innerText.length : 0)()"
                )
                or 0
            )
            allure.attach(
                f"URL after click: {after_url}\nBody text length: {body_len}",
                name="Interaction result",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert after_url and after_url != "about:blank", "После клика получен некорректный URL."
            assert body_len > 0, "После клика страница не содержит текста."

    except Exception:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        file_name = _safe_name(f"{device_name}_interaction_{url}")
        screenshot_path = ARTIFACTS_DIR / f"{file_name}.png"

        page.screenshot(path=str(screenshot_path), full_page=True)
        allure.attach.file(
            str(screenshot_path),
            name=f"Interaction_screenshot_{file_name}",
            attachment_type=allure.attachment_type.PNG,
        )

        allure.attach(
            f"Device: {device_name}\nURL: {url}\nClicked href: {clicked_href}\nCurrent URL: {page.url}\n",
            name="Interaction diagnostics",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise
    finally:
        with allure.step("Фиксирую состояние консоли"):
            _attach_console_state(collector)


def _run_real_iphone_interaction_smoke(url: str, device_name: str, runtime: dict[str, Any]) -> None:
    driver = runtime["driver"]
    clicked_href: str | None = None

    try:
        from selenium.webdriver.support.ui import WebDriverWait
    except Exception as exc:  # pragma: no cover - зависит от локальной среды
        raise RuntimeError("Selenium не установлен. Установи requirements-ios.txt") from exc

    try:
        with allure.step("Открываю страницу для интерактивной проверки"):
            driver.get(url)
            WebDriverWait(driver, 25).until(
                lambda drv: drv.execute_script("return document.readyState") == "complete"
            )

        with allure.step("Кликаю по первой валидной ссылке"):
            clicked_href = driver.execute_script(
                """
                const links = Array.from(document.querySelectorAll("a[href]"));
                const candidate = links.find((link) => {
                    const href = (link.getAttribute("href") || "").trim().toLowerCase();
                    const target = (link.getAttribute("target") || "").trim().toLowerCase();
                    if (!href || href.startsWith("#") || href.startsWith("javascript:")) return false;
                    if (href.startsWith("mailto:") || href.startsWith("tel:")) return false;
                    if (target === "_blank") return false;
                    return true;
                });
                if (!candidate) return null;
                candidate.scrollIntoView({block: "center"});
                const resolvedHref = candidate.href || candidate.getAttribute("href") || "";
                candidate.click();
                return resolvedHref || null;
                """
            )
            assert clicked_href, "На странице не найдена кликабельная ссылка для интерактивного smoke."
            allure.attach(
                f"Clicked href: {clicked_href}",
                name="Clicked link",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Проверяю состояние после клика"):
            WebDriverWait(driver, 25).until(
                lambda drv: drv.execute_script("return document.readyState") == "complete"
            )
            body_len = int(
                driver.execute_script(
                    "return document.body && document.body.innerText ? document.body.innerText.length : 0"
                )
                or 0
            )
            after_url = str(driver.current_url)
            allure.attach(
                f"URL after click: {after_url}\nBody text length: {body_len}",
                name="Interaction result",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert after_url and after_url != "about:blank", "После клика получен некорректный URL."
            assert body_len > 0, "После клика страница не содержит текста."

    except Exception:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        file_name = _safe_name(f"{device_name}_interaction_{url}")
        screenshot_path = ARTIFACTS_DIR / f"{file_name}.png"

        png_data = driver.get_screenshot_as_png()
        screenshot_path.write_bytes(png_data)
        allure.attach(
            png_data,
            name=f"Interaction_screenshot_{file_name}",
            attachment_type=allure.attachment_type.PNG,
        )

        allure.attach(
            (
                f"Device: {device_name}\n"
                f"URL: {url}\n"
                f"Clicked href: {clicked_href}\n"
                f"Current URL: {driver.current_url}\n"
            ),
            name="Interaction diagnostics",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise
    finally:
        with allure.step("Фиксирую состояние консоли"):
            _attach_console_state(None)


@pytest.mark.timeout(90)
def test_mobile_smoke_urls(url: str, target: str, session_runtime: dict[str, Any]) -> None:
    device_name = str(session_runtime["device_name"])
    unique_id = _stable_allure_id(target, url)

    allure.dynamic.id(unique_id)
    allure.dynamic.label("ALLURE_ID", unique_id)
    allure.dynamic.label("AS_ID", unique_id)
    allure.dynamic.parent_suite("SE Mobile")
    allure.dynamic.suite(device_name)
    allure.dynamic.sub_suite("Smoke URLs")
    allure.dynamic.title(f"Smoke | {device_name} | {url}")
    allure.dynamic.tag(target)

    if target == "real_iphone":
        allure.dynamic.tag("real-device")
        _run_real_iphone_smoke(url, device_name, session_runtime)
        return

    _run_playwright_smoke(url, device_name, session_runtime)


@pytest.mark.timeout(120)
def test_mobile_interaction_urls(url: str, target: str, session_runtime: dict[str, Any]) -> None:
    device_name = str(session_runtime["device_name"])
    unique_id = _stable_allure_id(f"{target}:interaction", url)

    allure.dynamic.id(unique_id)
    allure.dynamic.label("ALLURE_ID", unique_id)
    allure.dynamic.label("AS_ID", unique_id)
    allure.dynamic.parent_suite("SE Mobile")
    allure.dynamic.suite(device_name)
    allure.dynamic.sub_suite("Interaction URLs")
    allure.dynamic.title(f"Interaction | {device_name} | {url}")
    allure.dynamic.tag(target)
    allure.dynamic.tag("interaction")

    if target == "real_iphone":
        allure.dynamic.tag("real-device")
        _run_real_iphone_interaction_smoke(url, device_name, session_runtime)
        return

    _run_playwright_interaction_smoke(url, device_name, session_runtime)
