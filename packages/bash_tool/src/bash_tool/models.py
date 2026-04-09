"""Pydantic models for bash tool."""

from pydantic import BaseModel, Field


class CommandResult(BaseModel):
    """Result of a shell command execution."""

    stdout: str = Field(description="Standard output from the command")
    stderr: str = Field(description="Standard error from the command")
    exit_code: int = Field(description="Exit code of the command")
    truncated: bool = Field(description="Whether output was truncated to max_output")
