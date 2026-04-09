"""Pydantic models for the image gen tool."""

from pydantic import BaseModel, Field


class ImageGenResponse(BaseModel):
    """Response from a successful image generation."""

    path: str = Field(description="File path where the generated image was saved")
    prompt: str = Field(description="The prompt used for generation")
    aspect_ratio: str = Field(description="Aspect ratio of the generated image")
