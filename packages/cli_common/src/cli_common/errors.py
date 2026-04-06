"""Shared exception classes for CLI tools."""

from typing import Any


class ToolException(Exception):
    """Base exception for all tool errors.

    Carries a structured error code and optional details so that
    callers can convert it into a ToolError response.
    """

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}
