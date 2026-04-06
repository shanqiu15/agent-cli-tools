"""Tests for the OCR service orchestration layer."""

from pathlib import Path
from unittest.mock import patch

import pytest

from ocr_tool.errors import OcrError
from ocr_tool.models import OcrRequest, OcrResult
from ocr_tool.service import run_ocr


@patch("ocr_tool.service.extract_text_local", return_value="Hello from local")
def test_local_mode_dispatches_to_local_engine(mock_local, tmp_path: Path) -> None:
    """Dispatches to extract_text_local when mode is 'local'."""
    image = tmp_path / "photo.png"
    image.write_bytes(b"fake")
    request = OcrRequest(image_path=image, mode="local", explicit_mode=True)

    result = run_ocr(request)

    mock_local.assert_called_once_with(image, model=None)
    assert result.mode == "local"
    assert result.text == "Hello from local"
    assert result.model_used == "easyocr"


@patch("ocr_tool.service.extract_text_google", return_value="Hello from google")
def test_google_mode_dispatches_to_google_engine(
    mock_google, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Dispatches to extract_text_google when mode is 'google' and API key is set."""
    monkeypatch.setenv("GOOGLE_CLOUD_VISION_API_KEY", "test-key")
    image = tmp_path / "photo.png"
    image.write_bytes(b"fake")
    request = OcrRequest(image_path=image, mode="google", explicit_mode=True)

    result = run_ocr(request)

    mock_google.assert_called_once_with(image, model=None)
    assert result.mode == "google"
    assert result.text == "Hello from google"
    assert result.model_used == "google-cloud-vision"


@patch("ocr_tool.service.extract_text_local", return_value="Fallback text")
def test_auto_fallback_to_local_when_no_api_key(
    mock_local, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Falls back to local mode when google is default and GOOGLE_CLOUD_VISION_API_KEY is not set."""
    monkeypatch.delenv("GOOGLE_CLOUD_VISION_API_KEY", raising=False)
    image = tmp_path / "photo.png"
    image.write_bytes(b"fake")
    request = OcrRequest(image_path=image)  # default mode='google', explicit_mode=False

    result = run_ocr(request)

    mock_local.assert_called_once_with(image, model=None)
    assert result.mode == "local"
    assert result.model_used == "easyocr"
    assert result.text == "Fallback text"


def test_explicit_google_mode_fails_without_api_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Raises OcrError when google mode is explicitly chosen and GOOGLE_CLOUD_VISION_API_KEY is missing."""
    monkeypatch.delenv("GOOGLE_CLOUD_VISION_API_KEY", raising=False)
    image = tmp_path / "photo.png"
    image.write_bytes(b"fake")
    request = OcrRequest(image_path=image, mode="google", explicit_mode=True)

    with pytest.raises(OcrError) as exc_info:
        run_ocr(request)

    assert exc_info.value.code == "MISSING_CREDENTIALS"


def test_pdf_with_local_mode_raises_unsupported(tmp_path: Path) -> None:
    """Raises UNSUPPORTED_FILE_TYPE when PDF is used with local mode."""
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"fake-pdf")
    request = OcrRequest(image_path=pdf, mode="local", explicit_mode=True)

    with pytest.raises(OcrError) as exc_info:
        run_ocr(request)

    assert exc_info.value.code == "UNSUPPORTED_FILE_TYPE"


@patch("ocr_tool.service.extract_text_local", return_value="text")
def test_default_output_path_generation(mock_local, tmp_path: Path) -> None:
    """Defaults output_path to <image_stem>.txt in the same directory."""
    image = tmp_path / "document.png"
    image.write_bytes(b"fake")
    request = OcrRequest(image_path=image, mode="local", explicit_mode=True)

    result = run_ocr(request)

    assert result.output_path == tmp_path / "document.txt"


@patch("ocr_tool.service.extract_text_local", return_value="extracted content")
def test_output_file_is_written(mock_local, tmp_path: Path) -> None:
    """Writes the extracted text to the output file."""
    image = tmp_path / "photo.png"
    image.write_bytes(b"fake")
    output = tmp_path / "result.txt"
    request = OcrRequest(
        image_path=image, output_path=output, mode="local", explicit_mode=True
    )

    run_ocr(request)

    assert output.read_text(encoding="utf-8") == "extracted content"


@patch(
    "ocr_tool.service.extract_text_local",
    side_effect=OcrError(code="IMAGE_NOT_FOUND", message="not found"),
)
def test_engine_errors_propagate_as_ocr_error(mock_local, tmp_path: Path) -> None:
    """Engine OcrError exceptions propagate without wrapping."""
    image = tmp_path / "missing.png"
    request = OcrRequest(image_path=image, mode="local", explicit_mode=True)

    with pytest.raises(OcrError) as exc_info:
        run_ocr(request)

    assert exc_info.value.code == "IMAGE_NOT_FOUND"


@patch("ocr_tool.service.extract_text_local", return_value="text")
def test_returns_fully_populated_ocr_result(mock_local, tmp_path: Path) -> None:
    """Returns an OcrResult with all fields populated."""
    image = tmp_path / "scan.jpg"
    image.write_bytes(b"fake")
    output = tmp_path / "scan.txt"
    request = OcrRequest(
        image_path=image, output_path=output, mode="local", explicit_mode=True
    )

    result = run_ocr(request)

    assert isinstance(result, OcrResult)
    assert result.text == "text"
    assert result.source_image == image
    assert result.output_path == output
    assert result.mode == "local"
    assert result.model_used == "easyocr"
