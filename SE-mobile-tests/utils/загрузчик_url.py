from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse


def _replace_netloc(url: str, new_netloc: str) -> str:
    parsed = urlparse(url)
    if not (parsed.scheme and parsed.netloc):
        return url

    updated = parsed._replace(netloc=new_netloc)
    return urlunparse(updated)


def загрузить_url_из_файла(путь_к_файлу: Path) -> list[str]:
    """Читает URL из файла, игнорируя пустые строки и комментарии."""
    строки = путь_к_файлу.read_text(encoding="utf-8").splitlines()
    url_список: list[str] = []

    базовый_url = os.getenv("BASE_URL", "").strip().rstrip("/")
    домен_для_подмены = urlparse(базовый_url).netloc if базовый_url else ""

    for строка in строки:
        очищенная = строка.strip()
        if not очищенная or очищенная.startswith("#"):
            continue

        if домен_для_подмены:
            очищенная = _replace_netloc(очищенная, домен_для_подмены)

        url_список.append(очищенная)

    return url_список
