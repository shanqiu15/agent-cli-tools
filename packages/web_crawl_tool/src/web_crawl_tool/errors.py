"""Web crawl tool-specific exceptions."""

from typing import Any

from cli_common.errors import ToolException


class WebCrawlError(ToolException):
    """Base exception for web crawl tool errors."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details)
