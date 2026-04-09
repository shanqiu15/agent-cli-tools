"""Pydantic models for the vision tool."""

from pydantic import BaseModel, Field


class AnalyzeResult(BaseModel):
    """Result of analyzing an image with a vision model."""

    analysis: str = Field(description="The model's analysis of the image")
    provider: str = Field(description="The provider used for analysis (e.g. gemini, openai)")
    model: str = Field(description="The specific model used for analysis")
