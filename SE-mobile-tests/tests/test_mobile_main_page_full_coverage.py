from __future__ import annotations

import hashlib
from collections.abc import Iterable
from urllib.parse import urlparse

import allure
import pytest
from playwright.sync_api import Page

ДОПУСТИМЫЕ_HTTP_СТАТУСЫ = {200, 301, 302, 304}
ШАБЛОНЫ_АНТИБОТА = (
    "access denied",
    "verify you are human",
    "checking your browser",
    "captcha",
    "cloudflare",
    "ddos-guard",
    "подтвердите, что вы не робот",
    "проверка браузера",
    "доступ ограничен",
)


def _получить_playwright_страницу(session_runtime: dict[str, object]) -> Page:
    if session_runtime["kind"] != "playwright":
        pytest.skip("Расширенный набор кейсов выполняется только на Playwright-таргетах.")
    return session_runtime["page"]


def _применить_метки_allure(
    target: str,
    session_runtime: dict[str, object],
    кейс_страницы: dict[str, object],
    поднабор: str,
) -> None:
    уникальная_строка = f"{target}|{кейс_страницы['id']}|{поднабор}"
    digest = hashlib.sha1(уникальная_строка.encode("utf-8")).hexdigest()
    allure_id = str(int(digest[:12], 16))

    allure.dynamic.id(allure_id)
    allure.dynamic.label("ALLURE_ID", allure_id)
    allure.dynamic.label("AS_ID", allure_id)
    allure.dynamic.suite(str(session_runtime["device_name"]))
    allure.dynamic.sub_suite(f"Кейсы страниц: {поднабор}")
    allure.dynamic.tag(target)
    allure.dynamic.tag("кейс-страницы")
    allure.dynamic.tag(str(кейс_страницы["id"]))
    allure.dynamic.title(
        f"{поднабор} | {session_runtime['device_name']} | {кейс_страницы['название']}"
    )


def _открыть_страницу(page: Page, url: str) -> None:
    response = page.goto(url, wait_until="domcontentloaded")
    assert response is not None, f"Страница {url} не вернула HTTP response."
    assert response.status in ДОПУСТИМЫЕ_HTTP_СТАТУСЫ, (
        f"Недопустимый HTTP-статус для {url}: {response.status}. "
        f"Ожидались: {sorted(ДОПУСТИМЫЕ_HTTP_СТАТУСЫ)}"
    )

    try:
        page.wait_for_load_state("networkidle", timeout=20_000)
    except Exception:
        # Некоторые страницы с длинными рекламными запросами не доходят до networkidle.
        pass

    page.wait_for_function("document.readyState === 'complete'", timeout=30_000)
    page.wait_for_timeout(700)


def _проверить_что_не_антибот(page: Page) -> None:
    полный_текст = (page.inner_text("body") or "").lower()
    текущий_url = page.url.lower()
    for шаблон in ШАБЛОНЫ_АНТИБОТА:
        assert шаблон not in полный_текст, (
            "Обнаружена антибот-страница, функциональная проверка невозможна. "
            f"Паттерн: {шаблон}. URL: {текущий_url}"
        )


def _проверить_валидность_href(ссылки: Iterable[str]) -> None:
    невалидные: list[str] = []

    for href in ссылки:
        значение = (href or "").strip()
        if not значение:
            невалидные.append("<empty>")
            continue

        lower = значение.lower()
        if lower.startswith(("javascript:", "vbscript:")):
            невалидные.append(значение)
            continue
        if lower.startswith(("#", "mailto:", "tel:")):
            continue
        if lower.startswith("/"):
            continue

        parsed = urlparse(значение)
        if parsed.scheme not in ("http", "https"):
            невалидные.append(значение)

    assert not невалидные, f"Найдены невалидные href: {невалидные[:10]}"


def _минимум_ссылок(кейс_страницы: dict[str, object]) -> int:
    return max(1, int(кейс_страницы.get("минимум_ссылок", 5)))


def _минимум_текста(кейс_страницы: dict[str, object]) -> int:
    return max(20, int(кейс_страницы.get("минимум_текста", 120)))


@pytest.mark.timeout(120)
def test_страница_открывается_и_содержит_контент(
    кейс_страницы: dict[str, object], target: str, session_runtime: dict[str, object]
) -> None:
    page = _получить_playwright_страницу(session_runtime)
    url = str(кейс_страницы["url"])

    _применить_метки_allure(target, session_runtime, кейс_страницы, "Открытие")
    _открыть_страницу(page, url)
    _проверить_что_не_антибот(page)

    длина_текста = int(
        page.evaluate(
            "document.body && document.body.innerText ? document.body.innerText.length : 0"
        )
        or 0
    )
    assert длина_текста >= _минимум_текста(кейс_страницы), (
        f"Текстового контента мало: {длина_текста}. "
        f"Ожидалось минимум {_минимум_текста(кейс_страницы)}"
    )


@pytest.mark.timeout(120)
def test_страница_имеет_базовые_seo_метатеги(
    кейс_страницы: dict[str, object], target: str, session_runtime: dict[str, object]
) -> None:
    page = _получить_playwright_страницу(session_runtime)
    url = str(кейс_страницы["url"])

    _применить_метки_allure(target, session_runtime, кейс_страницы, "SEO")
    _открыть_страницу(page, url)
    _проверить_что_не_антибот(page)

    title = page.title().strip()
    assert len(title) >= 5, f"Слишком короткий title: {title!r}"

    assert page.locator('meta[name="description"]').count() >= 1, (
        "На странице отсутствует meta description"
    )
    assert page.locator('meta[name="viewport"]').count() >= 1, (
        "На странице отсутствует meta viewport"
    )
    assert page.locator('link[rel="canonical"]').count() >= 1, (
        "На странице отсутствует canonical"
    )

    og_title = page.locator('meta[property="og:title"]').count()
    twitter_title = page.locator('meta[name="twitter:title"]').count()
    assert (og_title + twitter_title) >= 1, (
        "Нет ни одного из обязательных соц-метатегов: og:title/twitter:title"
    )


@pytest.mark.timeout(120)
def test_страница_содержит_структурные_блоки(
    кейс_страницы: dict[str, object], target: str, session_runtime: dict[str, object]
) -> None:
    page = _получить_playwright_страницу(session_runtime)
    url = str(кейс_страницы["url"])

    _применить_метки_allure(target, session_runtime, кейс_страницы, "Структура")
    _открыть_страницу(page, url)
    _проверить_что_не_антибот(page)

    структура = page.evaluate(
        """
        () => ({
            header: document.querySelectorAll("header").length,
            main: document.querySelectorAll("main").length,
            article: document.querySelectorAll("article").length,
            footer: document.querySelectorAll("footer").length,
            links: document.querySelectorAll("a[href]").length
        })
        """
    )

    assert int(структура["header"]) >= 1, "На странице не найден блок header"
    assert int(структура["main"]) + int(структура["article"]) >= 1, (
        "На странице не найдено ни одного блока main/article"
    )

    минимум_ссылок = _минимум_ссылок(кейс_страницы)
    assert int(структура["links"]) >= минимум_ссылок, (
        f"На странице слишком мало ссылок: {структура['links']} < {минимум_ссылок}"
    )

    есть_футер_или_служебная_навигация = int(структура["footer"]) >= 1 or (
        page.locator(".se-footer, [data-main-menu], nav").count() >= 1
    )
    assert есть_футер_или_служебная_навигация, (
        "Не найден ни footer, ни служебная навигация (nav/data-main-menu)"
    )


@pytest.mark.timeout(120)
def test_все_href_на_странице_имеют_валидный_формат(
    кейс_страницы: dict[str, object], target: str, session_runtime: dict[str, object]
) -> None:
    page = _получить_playwright_страницу(session_runtime)
    url = str(кейс_страницы["url"])

    _применить_метки_allure(target, session_runtime, кейс_страницы, "Ссылки")
    _открыть_страницу(page, url)
    _проверить_что_не_антибот(page)

    hrefs = page.locator("a[href]").evaluate_all(
        "els => els.slice(0, 400).map(el => (el.getAttribute('href') || '').trim())"
    )
    assert hrefs, "На странице не найдено ссылок для проверки href"
    _проверить_валидность_href(hrefs)


@pytest.mark.timeout(120)
def test_страница_содержит_осмысленные_заголовки(
    кейс_страницы: dict[str, object], target: str, session_runtime: dict[str, object]
) -> None:
    page = _получить_playwright_страницу(session_runtime)
    url = str(кейс_страницы["url"])

    _применить_метки_allure(target, session_runtime, кейс_страницы, "Заголовки")
    _открыть_страницу(page, url)
    _проверить_что_не_антибот(page)

    заголовки = [
        text.strip()
        for text in page.locator("h1, h2, h3").all_inner_texts()
        if text and text.strip()
    ]
    assert заголовки, "На странице отсутствуют непустые заголовки h1/h2/h3"
    assert max(len(item) for item in заголовки) >= 6, "Заголовки выглядят слишком короткими"


@pytest.mark.timeout(120)
def test_изображения_имеют_источник_загрузки(
    кейс_страницы: dict[str, object], target: str, session_runtime: dict[str, object]
) -> None:
    page = _получить_playwright_страницу(session_runtime)
    url = str(кейс_страницы["url"])

    _применить_метки_allure(target, session_runtime, кейс_страницы, "Изображения")
    _открыть_страницу(page, url)
    _проверить_что_не_антибот(page)

    изображения = page.evaluate(
        """
        () => Array.from(document.querySelectorAll("img")).slice(0, 150).map((img) => ({
            src: (img.getAttribute("src") || "").trim(),
            dataSrc: (img.getAttribute("data-src") || "").trim(),
            srcset: (img.getAttribute("srcset") || "").trim()
        }))
        """
    )

    if not изображения:
        pytest.skip("На странице нет изображений: проверка источников пропущена")

    без_источника = [
        index
        for index, img in enumerate(изображения)
        if not (img["src"] or img["dataSrc"] or img["srcset"])
    ]
    assert not без_источника, (
        "Найдены изображения без src/data-src/srcset. "
        f"Индексы: {без_источника[:10]}"
    )


@pytest.mark.timeout(120)
def test_первая_внутренняя_ссылка_переходит_на_контентную_страницу(
    кейс_страницы: dict[str, object], target: str, session_runtime: dict[str, object]
) -> None:
    page = _получить_playwright_страницу(session_runtime)
    url = str(кейс_страницы["url"])

    _применить_метки_allure(target, session_runtime, кейс_страницы, "Переходы")
    _открыть_страницу(page, url)
    _проверить_что_не_антибот(page)

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
    assert clicked_href, "Для проверки перехода не найдена кликабельная ссылка"

    try:
        page.wait_for_load_state("domcontentloaded", timeout=20_000)
    except Exception:
        pass

    page.wait_for_timeout(800)
    текущий_url = page.url
    длина_текста = int(
        page.evaluate(
            "document.body && document.body.innerText ? document.body.innerText.length : 0"
        )
        or 0
    )

    assert текущий_url and текущий_url != "about:blank", "После клика получен некорректный URL"
    assert длина_текста > 0, "После перехода страница не содержит текста"


@pytest.mark.timeout(120)
def test_страница_имеет_структурированные_данные_или_open_graph(
    кейс_страницы: dict[str, object], target: str, session_runtime: dict[str, object]
) -> None:
    page = _получить_playwright_страницу(session_runtime)
    url = str(кейс_страницы["url"])

    _применить_метки_allure(target, session_runtime, кейс_страницы, "Разметка")
    _открыть_страницу(page, url)
    _проверить_что_не_антибот(page)

    json_ld = page.locator('script[type="application/ld+json"]').count()
    open_graph = page.locator('meta[property^="og:"]').count()

    assert (json_ld + open_graph) >= 1, (
        "На странице нет ни JSON-LD разметки, ни Open Graph метатегов"
    )
