"""OCR service orchestration layer."""

import os

from ocr_tool.engines.google import extract_text_google
from ocr_tool.engines.local import extract_text_local
from ocr_tool.errors import OcrError
from ocr_tool.models import OcrRequest, OcrResult

_LOCAL_DEFAULT_MODEL = "easyocr"
_GOOGLE_DEFAULT_MODEL = "google-cloud-vision"


def run_ocr(request: OcrRequest) -> OcrResult:
    """Validate inputs, run the appropriate OCR engine, and write results.

    Args:
        request: The OCR request parameters.

    Returns:
        A fully populated OcrResult.

    Raises:
        OcrError: If the image is invalid, missing, or engine fails.
    """
    output_path = request.output_path
    if output_path is None:
        output_path = request.image_path.with_suffix(".txt")

    mode = request.mode

    if mode == "google" and not os.environ.get("GOOGLE_CLOUD_VISION_API_KEY"):
        if request.explicit_mode:
            raise OcrError(
                code="MISSING_CREDENTIALS",
                message=(
                    "GOOGLE_CLOUD_VISION_API_KEY environment variable is not set. "
                    "Set GOOGLE_CLOUD_VISION_API_KEY to use the Google Cloud Vision OCR engine."
                ),
            )
        mode = "local"

    if mode == "local":
        if request.image_path.suffix.lower() == ".pdf":
            raise OcrError(
                code="UNSUPPORTED_FILE_TYPE",
                message=(
                    "Local OCR mode does not support PDF files. "
                    "Use google mode for PDF support."
                ),
                details={"file_path": str(request.image_path)},
            )
        text = extract_text_local(request.image_path, model=request.model)
        model_used = request.model or _LOCAL_DEFAULT_MODEL
    else:
        text = extract_text_google(request.image_path, model=request.model)
        model_used = request.model or _GOOGLE_DEFAULT_MODEL

    output_path.write_text(text, encoding="utf-8")

    return OcrResult(
        text=text,
        source_image=request.image_path,
        output_path=output_path,
        mode=mode,
        model_used=model_used,
    )
