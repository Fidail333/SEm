from __future__ import annotations

from pathlib import Path

import allure
import pytest
from playwright.sync_api import Page, Response

from utils.console_collector import ConsoleCollector

ALLOWED_STATUSES = {200, 304}
ARTIFACTS_DIR = Path("artifacts")


def _safe_name_from_url(url: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in url).strip("_")[:180]


def pytest_generate_tests(metafunc):
    if "url" in metafunc.fixturenames:
        urls = [
            line.strip()
            for line in (Path(__file__).resolve().parents[1] / "config" / "urls_mobile.txt").read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]
        metafunc.parametrize("url", urls)


@pytest.mark.timeout(60)
def test_mobile_urls(url: str, page: Page) -> None:
    allure.dynamic.title(f"Mobile Smoke | {url}")

    collector = ConsoleCollector()
    collector.attach(page)
    response: Response | None = None

    try:
        with allure.step(f"Открываем URL: {url}"):
            response = page.goto(url, wait_until="domcontentloaded")

        with allure.step("Проверяем, что получен HTTP response"):
            assert response is not None, (
                "Не получили response от page.goto(). "
                "Возможна сетевая ошибка, редирект без ответа или блокировка страницы."
            )

        with allure.step("Проверяем HTTP-статус (допустимы только 200 и 304)"):
            assert response.status in ALLOWED_STATUSES, (
                "Некорректный HTTP-статус для страницы. "
                f"URL: {url}. Фактический статус: {response.status}. "
                f"Допустимые статусы: {sorted(ALLOWED_STATUSES)}"
            )

        with allure.step("Проверяем отсутствие ошибок в консоли браузера"):
            assert not collector.has_errors, (
                "В консоли браузера обнаружены ошибки JavaScript. "
                f"URL: {url}\n{collector.as_text()}"
            )

    except Exception:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        safe_url_name = _safe_name_from_url(url)
        screenshot_path = ARTIFACTS_DIR / f"{safe_url_name}.png"
        response_status = str(response.status) if response is not None else "response отсутствует"

        with allure.step("Сохраняем скриншот и прикладываем артефакты падения"):
            page.screenshot(path=str(screenshot_path), full_page=True)
            allure.attach.file(
                str(screenshot_path),
                name=f"Скриншот падения: {safe_url_name}",
                attachment_type=allure.attachment_type.PNG,
            )
            allure.attach(
                (
                    "Диагностическая информация по падению:\n"
                    f"URL: {url}\n"
                    f"HTTP-статус: {response_status}\n\n"
                    "Ошибки консоли:\n"
                    f"{collector.as_text()}"
                ),
                name="Диагностика падения",
                attachment_type=allure.attachment_type.TEXT,
            )

        raise
