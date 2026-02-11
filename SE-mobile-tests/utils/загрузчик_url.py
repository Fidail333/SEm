from __future__ import annotations

from pathlib import Path


def загрузить_url_из_файла(путь_к_файлу: Path) -> list[str]:
    """Читает URL из текстового файла с фильтрацией комментариев и пустых строк."""
    строки = путь_к_файлу.read_text(encoding="utf-8").splitlines()
    url_список: list[str] = []

    for строка in строки:
        очищенная = строка.strip()
        if not очищенная or очищенная.startswith("#"):
            continue
        url_список.append(очищенная)

    return url_список
