from __future__ import annotations

import os
from urllib.parse import urlparse, urlunparse

from config.кейсы_страниц import КЕЙСЫ_СТРАНИЦ


def _подменить_домен(url: str, новый_домен: str) -> str:
    parsed = urlparse(url)
    if not (parsed.scheme and parsed.netloc):
        return url
    return urlunparse(parsed._replace(netloc=новый_домен))


def _нормализовать_кейс(исходный: dict[str, object], номер: int) -> dict[str, object]:
    url = str(исходный.get("url", "")).strip()
    название = str(исходный.get("название", f"Страница {номер:02d}")).strip()
    минимум_ссылок = int(исходный.get("минимум_ссылок", 5))
    минимум_текста = int(исходный.get("минимум_текста", 120))

    if not url:
        raise ValueError(f"Кейс №{номер} не содержит URL")

    return {
        "id": f"страница_{номер:02d}",
        "название": название,
        "url": url,
        "минимум_ссылок": max(1, минимум_ссылок),
        "минимум_текста": max(20, минимум_текста),
    }


def загрузить_кейсы_страниц() -> list[dict[str, object]]:
    """Возвращает список кейсов страниц с учетом BASE_URL."""
    базовый_url = os.getenv("BASE_URL", "").strip().rstrip("/")
    домен_для_подмены = urlparse(базовый_url).netloc if базовый_url else ""

    кейсы: list[dict[str, object]] = []
    for номер, исходный in enumerate(КЕЙСЫ_СТРАНИЦ, start=1):
        кейс = _нормализовать_кейс(исходный, номер)
        if домен_для_подмены:
            кейс["url"] = _подменить_домен(str(кейс["url"]), домен_для_подмены)
        кейсы.append(кейс)

    return кейсы
