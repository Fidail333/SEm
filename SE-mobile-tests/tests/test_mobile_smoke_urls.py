from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import allure
import pytest
from playwright.sync_api import Page, Response, TimeoutError as PlaywrightTimeoutError

from utils.сборщик_консоли import СборщикКонсоли

НЕГАТИВНЫЙ_ПУТЬ = "/asdasdasd/"
РАЗРЕШЕННЫЕ_СТАТУСЫ = {200, 301, 302, 304}
ПАПКА_АРТЕФАКТОВ = Path("artifacts")


def _безопасное_имя(текст: str) -> str:
    return "".join(символ if символ.isalnum() else "_" for символ in текст).strip("_")[:180]


def _получить_параметры_эмуляции(page: Page) -> str:
    user_agent = page.evaluate("() => navigator.userAgent")
    viewport = page.viewport_size
    ширина = viewport.get("width") if viewport else "N/A"
    высота = viewport.get("height") if viewport else "N/A"
    return f"Пользовательский агент: {user_agent}\nРазмер экрана: {ширина}x{высота}\n"


def _стабильный_allure_id(device_name: str, url: str) -> str:
    исходная_строка = f"{device_name}|{url}"
    digest = hashlib.sha1(исходная_строка.encode("utf-8")).hexdigest()
    return str(int(digest[:12], 16))


def _проверить_http_статус(url: str, response: Response) -> None:
    if urlparse(url).path.rstrip("/") == НЕГАТИВНЫЙ_ПУТЬ.rstrip("/"):
        assert response.status == 404, (
            f"Для негативного URL ожидается статус 404, фактический статус: {response.status}"
        )
        return

    assert response.status in РАЗРЕШЕННЫЕ_СТАТУСЫ, (
        f"Недопустимый HTTP статус: {response.status}. Допустимые статусы: {sorted(РАЗРЕШЕННЫЕ_СТАТУСЫ)}"
    )


def _приложить_состояние_консоли(сборщик_консоли: СборщикКонсоли) -> None:
    if сборщик_консоли.количество_ошибок > 0:
        allure.dynamic.severity(allure.severity_level.MINOR)
        allure.dynamic.tag("предупреждение-консоли")
        allure.dynamic.label("предупреждение-консоли", "да")
        allure.attach(
            f"Количество ошибок консоли: {сборщик_консоли.количество_ошибок}\n\n"
            f"{сборщик_консоли.как_текст()}",
            name="⚠ Ошибки консоли (не блокируют)",
            attachment_type=allure.attachment_type.TEXT,
        )
    else:
        allure.dynamic.severity(allure.severity_level.TRIVIAL)
        allure.attach(
            "Ошибок консоли не обнаружено",
            name="Ошибок консоли не обнаружено",
            attachment_type=allure.attachment_type.TEXT,
        )


@pytest.mark.timeout(90)
def test_mobile_smoke_urls(url: str, device_name: str, page: Page) -> None:
    allure.dynamic.id(_стабильный_allure_id(device_name, url))
    allure.dynamic.parent_suite("SE Мобильная версия")
    allure.dynamic.suite(device_name)
    allure.dynamic.sub_suite("Смоук-проверка URL")
    allure.dynamic.title(f"Смоук-проверка | {device_name} | {url}")

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

        with allure.step("Открываю страницу и жду построения DOM"):
            response = page.goto(url, wait_until="domcontentloaded")

        with allure.step("Ожидаю состояние загрузки сети до 20 секунд (без падения при таймауте)"):
            try:
                page.wait_for_load_state("networkidle", timeout=20_000)
            except PlaywrightTimeoutError:
                allure.attach(
                    "Состояние покоя сети не достигнуто за 20 секунд. Продолжаю тест без падения.",
                    name="Предупреждение_по_загрузке_сети",
                    attachment_type=allure.attachment_type.TEXT,
                )

        with allure.step("Выдерживаю стабилизационную паузу 800 мс"):
            page.wait_for_timeout(800)

        with allure.step("Ожидаю полной готовности страницы"):
            page.wait_for_function("document.readyState === 'complete'", timeout=20_000)

        with allure.step("Проверяю, что на странице есть текстовый контент"):
            page.wait_for_function(
                "document.body && document.body.innerText && document.body.innerText.length > 0",
                timeout=20_000,
            )

        with allure.step("Проверяю, что получен ответ сервера"):
            assert response is not None, (
                "Переход на страницу не вернул объект ответа. Невозможно проверить HTTP-статус. "
                "См. диагностику и скриншот во вложениях Allure."
            )

        with allure.step("Проверяю код ответа сервера согласно правилам"):
            _проверить_http_статус(url, response)

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

        статус = response.status if response is not None else "ответ не получен"
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
    finally:
        with allure.step("Фиксирую результат проверки консоли (неблокирующий)"):
            _приложить_состояние_консоли(сборщик_консоли)
