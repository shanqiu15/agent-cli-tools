"""Pydantic models for the sonar tool."""

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A single citation from the Sonar response."""

    url: str = Field(description="URL of the cited source")
    title: str = Field(description="Title of the cited source")


class SonarResponse(BaseModel):
    """Response from the Perplexity Sonar API."""

    answer: str = Field(description="Synthesized answer text")
    citations: list[Citation] = Field(description="List of source citations")
    model: str = Field(description="Model used for the query")
