"""Local OCR engine using easyocr."""

from pathlib import Path

import easyocr  # type: ignore[import-untyped]
from PIL import Image

from ocr_tool.errors import OcrError


def extract_text_local(image_path: Path, model: str | None = None) -> str:
    """Extract text from an image using easyocr.

    Args:
        image_path: Path to the image file.
        model: Optional model name (reserved for future use).

    Returns:
        Extracted text as a single string with results joined by newlines.

    Raises:
        OcrError: If the image path doesn't exist or the image is invalid.
    """
    if not image_path.exists():
        raise OcrError(
            code="IMAGE_NOT_FOUND",
            message=f"Image file not found: {image_path}",
            details={"image_path": str(image_path)},
        )

    try:
        img = Image.open(image_path)
        img.verify()
    except Exception as exc:
        raise OcrError(
            code="INVALID_IMAGE",
            message=f"Cannot open image: {image_path}",
            details={"image_path": str(image_path), "reason": str(exc)},
        ) from exc

    reader = easyocr.Reader(["en"], verbose=False)
    results = reader.readtext(str(image_path), detail=0)

    return "\n".join(results)
