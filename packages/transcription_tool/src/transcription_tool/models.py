"""Pydantic models for the transcription tool."""

from pydantic import BaseModel, Field


class TranscribeResult(BaseModel):
    """Result of transcribing an audio file."""

    transcript: str = Field(description="The transcribed text from the audio file")
    provider: str = Field(description="The provider used for transcription (e.g. groq, openai)")
    model: str = Field(description="The specific model used for transcription")
