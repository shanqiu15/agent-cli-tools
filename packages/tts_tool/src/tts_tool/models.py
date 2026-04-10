"""Pydantic models for the TTS tool."""

from pydantic import BaseModel, Field


class SpeakResult(BaseModel):
    """Result of generating speech from text."""

    file_path: str = Field(description="Path to the generated audio file")
    provider: str = Field(description="The provider used for synthesis (e.g. edge, openai)")
    voice: str = Field(description="The voice used for synthesis")
