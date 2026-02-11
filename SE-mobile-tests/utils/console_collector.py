from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from playwright.sync_api import ConsoleMessage, Page


@dataclass
class ConsoleCollector:
    """Собирает ошибки консоли браузера (console.error) на странице Playwright."""

    errors: List[str] = field(default_factory=list)

    def attach(self, page: Page) -> None:
        page.on("console", self._handle_console_message)

    def _handle_console_message(self, msg: ConsoleMessage) -> None:
        if msg.type == "error":
            self.errors.append(msg.text)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def as_text(self) -> str:
        if not self.errors:
            return "Ошибок в консоли не обнаружено."
        return "\n".join(f"{index}. {message}" for index, message in enumerate(self.errors, start=1))
