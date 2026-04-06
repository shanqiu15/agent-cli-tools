"""Google Cloud Vision OCR engine."""

import os
from pathlib import Path

from google.cloud import vision  # type: ignore[import-untyped]

from ocr_tool.errors import OcrError


def extract_text_google(file_path: Path, model: str | None = None) -> str:
    """Extract text from an image using Google Cloud Vision API.

    Args:
        file_path: Path to the image file.
        model: Optional model name (reserved for future use).

    Returns:
        Extracted text as a string.

    Raises:
        OcrError: If credentials are missing, the file doesn't exist,
            or the API call fails.
    """
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            import google.auth  # type: ignore[import-untyped]

            google.auth.default()
        except Exception:
            raise OcrError(
                code="MISSING_CREDENTIALS",
                message=(
                    "Google Cloud credentials not found. "
                    "Set GOOGLE_APPLICATION_CREDENTIALS or configure "
                    "application default credentials."
                ),
            )

    if not file_path.exists():
        raise OcrError(
            code="IMAGE_NOT_FOUND",
            message=f"Image file not found: {file_path}",
            details={"image_path": str(file_path)},
        )

    content = file_path.read_bytes()
    image = vision.Image(content=content)

    client = vision.ImageAnnotatorClient()
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise OcrError(
            code="API_ERROR",
            message=f"Google Cloud Vision API error: {response.error.message}",
            details={"error": response.error.message},
        )

    if not response.full_text_annotation.text:
        return ""

    return response.full_text_annotation.text
