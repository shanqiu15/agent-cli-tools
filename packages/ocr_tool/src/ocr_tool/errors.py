"""OCR tool-specific exceptions."""

from typing import Any

from cli_common.errors import ToolException


class OcrError(ToolException):
    """Base exception for OCR tool errors."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details)
