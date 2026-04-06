"""JSON output helpers for CLI tools."""

import sys
from typing import Any

from cli_common.models import ToolError, ToolResponse


def emit_success(result: dict[str, Any]) -> None:
    """Print a successful ToolResponse as JSON to stdout."""
    response = ToolResponse(ok=True, result=result)
    sys.stdout.write(response.model_dump_json() + "\n")


def emit_error(code: str, message: str, details: dict[str, Any] | None = None) -> None:
    """Print a failed ToolResponse as JSON to stdout and exit with code 1."""
    error = ToolError(code=code, message=message, details=details or {})
    response = ToolResponse(ok=False, error=error)
    sys.stdout.write(response.model_dump_json() + "\n")
    sys.exit(1)
