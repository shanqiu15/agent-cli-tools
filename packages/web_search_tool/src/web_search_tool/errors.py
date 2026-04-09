"""Web search tool-specific exceptions."""

from typing import Any

from cli_common.errors import ToolException


class WebSearchError(ToolException):
    """Base exception for web search tool errors."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details)
