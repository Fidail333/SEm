from __future__ import annotations

from pathlib import Path

import allure
import pytest
from playwright.sync_api import Page, Response, TimeoutError as PlaywrightTimeoutError

from utils.сборщик_консоли import СборщикКонсоли

НЕГАТИВНЫЙ_URL = "https://m.sport-express.ru/asdasdasd/"
РАЗРЕШЕННЫЕ_СТАТУСЫ = {200, 301, 302, 304}
ПАПКА_АРТЕФАКТОВ = Path("artifacts")


def _безопасное_имя(текст: str) -> str:
    return "".join(символ if символ.isalnum() else "_" for символ in текст).strip("_")[:180]


def _получить_параметры_эмуляции(page: Page) -> str:
    user_agent = page.evaluate("() => navigator.userAgent")
    viewport = page.viewport_size
    ширина = viewport.get("width") if viewport else "N/A"
    высота = viewport.get("height") if viewport else "N/A"
    return f"user-agent: {user_agent}\nviewport: {ширина}x{высота}\n"


def _проверить_http_статус(url: str, response: Response) -> None:
    if url == НЕГАТИВНЫЙ_URL:
        assert response.status == 404, (
            f"Для негативного URL ожидается статус 404, фактический статус: {response.status}"
        )
        return

    assert response.status in РАЗРЕШЕННЫЕ_СТАТУСЫ, (
        f"Недопустимый HTTP статус: {response.status}. Допустимые статусы: {sorted(РАЗРЕШЕННЫЕ_СТАТУСЫ)}"
    )


@pytest.mark.timeout(90)
def test_mobile_smoke_urls(url: str, device_name: str, page: Page) -> None:
    allure.dynamic.title(f"Мобайл смоук | {device_name} | {url}")

    сборщик_консоли = СборщикКонсоли()
    сборщик_консоли.подключить(page)
    response: Response | None = None

    try:
        with allure.step("Сохраняю параметры эмуляции устройства"):
            allure.attach(
                _получить_параметры_эмуляции(page),
                name="Параметры_эмуляции",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Открываю страницу через page.goto(wait_until='domcontentloaded')"):
            response = page.goto(url, wait_until="domcontentloaded")

        with allure.step("Ожидаю networkidle до 20 секунд (без падения при таймауте)"):
            try:
                page.wait_for_load_state("networkidle", timeout=20_000)
            except PlaywrightTimeoutError:
                allure.attach(
                    "Состояние networkidle не достигнуто за 20 секунд. Продолжаю тест без падения.",
                    name="Networkidle_предупреждение",
                    attachment_type=allure.attachment_type.TEXT,
                )

        with allure.step("Выдерживаю стабилизационную паузу 800 мс"):
            page.wait_for_timeout(800)

        with allure.step("Жду полной готовности документа (document.readyState === 'complete')"):
            page.wait_for_function("() => document.readyState === 'complete'")

        with allure.step("Проверяю, что страница реально отрисована"):
            страница_отрисована = page.evaluate(
                """
                () => {
                    const body = document.body;
                    if (!body) {
                        return false;
                    }
                    return body.innerText && body.innerText.trim().length > 0;
                }
                """
            )
            assert страница_отрисована, "Страница не отрисована: body отсутствует или не содержит текста."

        with allure.step("Проверяю, что ответ сервера получен"):
            assert response is not None, (
                "page.goto вернул response=None. Невозможно проверить HTTP-статус. "
                "См. диагностику и скриншот во вложениях Allure."
            )

        with allure.step("Проверяю HTTP-статус согласно правилам"):
            _проверить_http_статус(url, response)

        with allure.step("Прикладываю ошибки консоли (не блокируют)"):
            allure.attach(
                f"Количество ошибок консоли: {сборщик_консоли.количество_ошибок}\n\n"
                f"{сборщик_консоли.как_текст()}",
                name="Ошибки консоли (не блокируют)",
                attachment_type=allure.attachment_type.TEXT,
            )

    except Exception:
        ПАПКА_АРТЕФАКТОВ.mkdir(parents=True, exist_ok=True)
        имя_файла = _безопасное_имя(f"{device_name}_{url}")
        путь_к_скриншоту = ПАПКА_АРТЕФАКТОВ / f"{имя_файла}.png"

        page.screenshot(path=str(путь_к_скриншоту), full_page=True)
        allure.attach.file(
            str(путь_к_скриншоту),
            name=f"Скриншот_{имя_файла}",
            attachment_type=allure.attachment_type.PNG,
        )

        статус = response.status if response is not None else "response=None"
        диагностический_текст = (
            f"Устройство: {device_name}\n"
            f"URL: {url}\n"
            f"Статус документа: {статус}\n"
            f"Количество ошибок консоли: {сборщик_консоли.количество_ошибок}\n"
            f"Ошибки консоли:\n{сборщик_консоли.как_текст()}\n"
        )
        allure.attach(
            диагностический_текст,
            name="Диагностика_при_падении",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise
