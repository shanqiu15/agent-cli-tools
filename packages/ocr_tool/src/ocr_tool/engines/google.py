"""Google Cloud Vision OCR engine."""

import os
from pathlib import Path

from google.cloud import vision  # type: ignore[import-untyped]

from ocr_tool.errors import OcrError

_SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
}

_MAX_PDF_PAGES = 5


def extract_text_google(file_path: Path, model: str | None = None) -> str:
    """Extract text from an image or PDF using Google Cloud Vision API.

    Args:
        file_path: Path to the image or PDF file.
        model: Optional model name (reserved for future use).

    Returns:
        Extracted text as a string.

    Raises:
        OcrError: If credentials are missing, the file doesn't exist,
            the file type is unsupported, or the API call fails.
    """
    api_key = os.environ.get("GOOGLE_CLOUD_VISION_API_KEY")
    if not api_key:
        raise OcrError(
            code="MISSING_CREDENTIALS",
            message=(
                "GOOGLE_CLOUD_VISION_API_KEY environment variable is not set. "
                "Set GOOGLE_CLOUD_VISION_API_KEY to use the Google Cloud Vision OCR engine."
            ),
        )

    if not file_path.exists():
        raise OcrError(
            code="IMAGE_NOT_FOUND",
            message=f"Image file not found: {file_path}",
            details={"image_path": str(file_path)},
        )

    suffix = file_path.suffix.lower()
    is_pdf = suffix == ".pdf"

    if not is_pdf and suffix not in _SUPPORTED_IMAGE_EXTENSIONS:
        raise OcrError(
            code="INVALID_FILE",
            message=(
                f"Unsupported file type '{suffix}'. "
                f"Supported formats: PDF, "
                f"{', '.join(sorted(_SUPPORTED_IMAGE_EXTENSIONS))}."
            ),
            details={"file_path": str(file_path), "extension": suffix},
        )

    content = file_path.read_bytes()
    client = vision.ImageAnnotatorClient(client_options={"api_key": api_key})

    if is_pdf:
        return _extract_text_from_pdf(client, content)

    return _extract_text_from_image(client, content)


def _extract_text_from_image(
    client: vision.ImageAnnotatorClient,  # type: ignore[type-arg]
    content: bytes,
) -> str:
    """Extract text from image bytes using document_text_detection."""
    image = vision.Image(content=content)
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


def _extract_text_from_pdf(
    client: vision.ImageAnnotatorClient,  # type: ignore[type-arg]
    content: bytes,
) -> str:
    """Extract text from PDF bytes using batch_annotate_files."""
    input_config = vision.InputConfig(
        mime_type="application/pdf",
        content=content,
    )
    feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
    request = vision.AnnotateFileRequest(
        input_config=input_config,
        features=[feature],
        pages=list(range(1, _MAX_PDF_PAGES + 1)),
    )

    response = client.batch_annotate_files(requests=[request])

    if not response.responses:
        return ""

    file_response = response.responses[0]

    if file_response.error.message:
        raise OcrError(
            code="API_ERROR",
            message=f"Google Cloud Vision API error: {file_response.error.message}",
            details={"error": file_response.error.message},
        )

    total_pages = file_response.total_pages
    if total_pages > _MAX_PDF_PAGES:
        raise OcrError(
            code="PDF_TOO_LARGE",
            message=(
                f"PDF has {total_pages} pages, but the maximum supported is "
                f"{_MAX_PDF_PAGES}. Please split the PDF into smaller files."
            ),
            details={"total_pages": total_pages, "max_pages": _MAX_PDF_PAGES},
        )

    parts: list[str] = []
    for page_response in file_response.responses:
        if page_response.full_text_annotation.text:
            parts.append(page_response.full_text_annotation.text)

    return "\n".join(parts)
