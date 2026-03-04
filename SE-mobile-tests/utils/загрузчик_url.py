from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse


def загрузить_url_из_файла(путь_к_файлу: Path) -> list[str]:
    """Читает URL из текстового файла с фильтрацией комментариев и пустых строк."""
    строки = путь_к_файлу.read_text(encoding="utf-8").splitlines()
    url_список: list[str] = []
    базовый_url = os.getenv("BASE_URL", "").strip().rstrip("/")
    домен_для_подмены = urlparse(базовый_url).netloc if базовый_url else ""

    for строка in строки:
        очищенная = строка.strip()
        if not очищенная or очищенная.startswith("#"):
            continue
        if домен_для_подмены:
            разобранный = urlparse(очищенная)
            if разобранный.scheme and разобранный.netloc:
                очищенная = очищенная.replace(разобранный.netloc, домен_для_подмены, 1)
        url_список.append(очищенная)

    return url_список
