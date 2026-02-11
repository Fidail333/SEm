from __future__ import annotations

import random
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Page, Response

from utils.сборщик_консоли import СборщикКонсоли

РАЗРЕШЕННЫЕ_СТАТУСЫ = {200, 304}
ПАПКА_АРТЕФАКТОВ = Path("artifacts")


def _безопасное_имя(текст: str) -> str:
    return "".join(символ if символ.isalnum() else "_" for символ in текст).strip("_")[:180]


def _получить_параметры_эмуляции(page: Page) -> str:
    user_agent = page.evaluate("() => navigator.userAgent")
    viewport = page.viewport_size
    return (
        f"user-agent: {user_agent}\n"
        f"viewport: {viewport['width']}x{viewport['height']}\n"
    )


def pytest_generate_tests(metafunc):
    if "url" in metafunc.fixturenames:
        urls = metafunc.config._inicache.get("mobile_urls_cache")
        if urls is None:
            from utils.загрузчик_url import загрузить_url_из_файла

            файл = Path(__file__).resolve().parents[1] / "config" / "urls_mobile.txt"
            urls = загрузить_url_из_файла(файл)
            metafunc.config._inicache["mobile_urls_cache"] = urls
        metafunc.parametrize("url", urls)


@pytest.mark.timeout(60)
def test_mobile_smoke_urls(url: str, page: Page) -> None:
    allure.dynamic.title(f"Мобайл смоук | {url}")

    сборщик_консоли = СборщикКонсоли()
    сборщик_консоли.подключить(page)
    response: Response | None = None

    with allure.step("Сохраняю параметры эмуляции устройства"):
        allure.attach(
            _получить_параметры_эмуляции(page),
            name="Параметры_эмуляции",
            attachment_type=allure.attachment_type.TEXT,
        )

    try:
        with allure.step("Открываю страницу"):
            response = page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(random.randint(200, 400))

        with allure.step("Проверяю статус ответа документа"):
            assert response is not None, "page.goto вернул response=None"
            assert response.status in РАЗРЕШЕННЫЕ_СТАТУСЫ, (
                f"Недопустимый HTTP статус: {response.status}. Допустимо: {sorted(РАЗРЕШЕННЫЕ_СТАТУСЫ)}"
            )

        with allure.step("Собираю ошибки консоли"):
            allure.attach(
                сборщик_консоли.как_текст(),
                name="Ошибки_консоли",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Проверяю отсутствие ошибок консоли"):
            assert not сборщик_консоли.есть_ошибки, (
                "Найдены ошибки в консоли браузера:\n" f"{сборщик_консоли.как_текст()}"
            )

    except Exception:
        ПАПКА_АРТЕФАКТОВ.mkdir(parents=True, exist_ok=True)
        имя_файла = _безопасное_имя(url)
        путь_к_скриншоту = ПАПКА_АРТЕФАКТОВ / f"{имя_файла}.png"

        page.screenshot(path=str(путь_к_скриншоту), full_page=True)
        allure.attach.file(
            str(путь_к_скриншоту),
            name=f"Скриншот_{имя_файла}",
            attachment_type=allure.attachment_type.PNG,
        )

        статус = response.status if response is not None else "N/A"
        диагностический_текст = (
            f"URL: {url}\n"
            f"Статус документа: {статус}\n"
            f"Ошибки консоли:\n{сборщик_консоли.как_текст()}\n"
        )
        allure.attach(
            диагностический_текст,
            name="Диагностика_при_падении",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise
