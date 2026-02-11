from __future__ import annotations

from dataclasses import dataclass, field

from playwright.sync_api import ConsoleMessage, Page


@dataclass
class СборщикКонсоли:
    """Собирает сообщения браузерной консоли уровня error."""

    ошибки: list[str] = field(default_factory=list)

    def подключить(self, страница: Page) -> None:
        страница.on("console", self._обработать_сообщение)

    def _обработать_сообщение(self, сообщение: ConsoleMessage) -> None:
        if сообщение.type == "error":
            self.ошибки.append(сообщение.text)

    @property
    def есть_ошибки(self) -> bool:
        return bool(self.ошибки)

    def как_текст(self) -> str:
        if not self.ошибки:
            return "Ошибок консоли не найдено."
        return "\n".join(f"{индекс}. {текст}" for индекс, текст in enumerate(self.ошибки, start=1))
