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
        with allure.step(f"Open URL: {url}"):
            response = page.goto(url, wait_until="domcontentloaded")

        with allure.step("Verify response exists"):
            assert response is not None, "page.goto() returned None response"

        with allure.step("Verify response status is 200 or 304"):
            assert response.status in ALLOWED_STATUSES, (
                f"Unexpected status code {response.status}. Allowed: {sorted(ALLOWED_STATUSES)}"
            )

        with allure.step("Verify there are no console errors"):
            assert not collector.has_errors, f"Console errors found:\n{collector.as_text()}"

    except Exception:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = ARTIFACTS_DIR / f"{_safe_name_from_url(url)}.png"

        with allure.step("Capture screenshot and attach failure artifacts"):
            page.screenshot(path=str(screenshot_path), full_page=True)
            allure.attach.file(
                str(screenshot_path),
                name=f"screenshot_{_safe_name_from_url(url)}",
                attachment_type=allure.attachment_type.PNG,
            )
            allure.attach(
                collector.as_text(),
                name="console_errors",
                attachment_type=allure.attachment_type.TEXT,
            )

        raise
