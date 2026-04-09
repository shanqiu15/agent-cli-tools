"""Pydantic models for browser tool."""

from pydantic import BaseModel, Field


class BrowserResult(BaseModel):
    """Result of a browser action."""

    action: str = Field(description="The action that was performed")
    output: str = Field(description="Output from playwright-cli")
    session: str = Field(description="Session name used")


class BrowserStatus(BaseModel):
    """Status of the browser session."""

    running: bool = Field(description="Whether a browser session is active")
    session: str = Field(description="Session name")
    output: str = Field(description="Raw status output from playwright-cli")
