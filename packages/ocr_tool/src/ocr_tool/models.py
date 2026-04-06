"""Pydantic models for OCR tool requests and responses."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class OcrRequest(BaseModel):
    """Input parameters for an OCR extraction."""

    image_path: Path = Field(description="Path to the input image file")
    output_path: Path | None = Field(
        default=None,
        description="Path for the output text file; defaults to <image_stem>.txt",
    )
    mode: Literal["local", "llm"] = Field(
        default="local",
        description="OCR engine mode: 'local' for offline or 'llm' for vision API",
    )
    model: str | None = Field(
        default=None,
        description="Optional model name override for the selected engine",
    )


class OcrResult(BaseModel):
    """Output of a successful OCR extraction."""

    text: str = Field(description="Extracted text content")
    source_image: Path = Field(
        description="Path to the source image that was processed"
    )
    output_path: Path = Field(description="Path where extracted text was written")
    mode: Literal["local", "llm"] = Field(description="Engine mode that was used")
    model_used: str = Field(
        description="Name of the model that performed the extraction"
    )
