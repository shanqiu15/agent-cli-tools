"""Todo tool-specific exceptions."""

from typing import Any

from cli_common.errors import ToolException


class TodoError(ToolException):
    """Base exception for todo tool errors."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details)
