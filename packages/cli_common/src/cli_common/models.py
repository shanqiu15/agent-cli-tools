"""Shared response and error models for CLI tools."""

from typing import Any

from pydantic import BaseModel, Field


class ToolError(BaseModel):
    """Structured error payload for tool failures."""

    code: str = Field(description="Machine-readable error code, e.g. FILE_NOT_FOUND")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context to help the caller recover",
    )


class ToolResponse(BaseModel):
    """Standard JSON envelope for all tool output."""

    ok: bool = Field(description="True if the operation succeeded")
    result: dict[str, Any] | None = Field(
        default=None,
        description="Payload on success",
    )
    error: ToolError | None = Field(
        default=None,
        description="Error details on failure",
    )
