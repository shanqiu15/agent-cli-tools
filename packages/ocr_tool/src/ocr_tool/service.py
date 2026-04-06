"""OCR service orchestration layer."""

from ocr_tool.engines.llm import _DEFAULT_MODEL as _LLM_DEFAULT_MODEL
from ocr_tool.engines.llm import extract_text_llm
from ocr_tool.engines.local import extract_text_local
from ocr_tool.models import OcrRequest, OcrResult

_LOCAL_DEFAULT_MODEL = "easyocr"


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

    if request.mode == "local":
        text = extract_text_local(request.image_path, model=request.model)
        model_used = request.model or _LOCAL_DEFAULT_MODEL
    else:
        text = extract_text_llm(request.image_path, model=request.model)
        model_used = request.model or _LLM_DEFAULT_MODEL

    output_path.write_text(text, encoding="utf-8")

    return OcrResult(
        text=text,
        source_image=request.image_path,
        output_path=output_path,
        mode=request.mode,
        model_used=model_used,
    )
