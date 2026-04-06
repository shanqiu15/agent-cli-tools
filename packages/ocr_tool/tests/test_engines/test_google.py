"""Tests for the Google Cloud Vision OCR engine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ocr_tool.engines.google import extract_text_google
from ocr_tool.errors import OcrError


def test_missing_api_key_raises_ocr_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raises OcrError with MISSING_CREDENTIALS when GOOGLE_CLOUD_VISION_API_KEY is not set."""
    monkeypatch.delenv("GOOGLE_CLOUD_VISION_API_KEY", raising=False)

    with pytest.raises(OcrError) as exc_info:
        extract_text_google(Path("/some/image.png"))

    assert exc_info.value.code == "MISSING_CREDENTIALS"


def test_file_not_found_raises_ocr_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raises OcrError with IMAGE_NOT_FOUND for a missing file."""
    monkeypatch.setenv("GOOGLE_CLOUD_VISION_API_KEY", "test-api-key")

    with pytest.raises(OcrError) as exc_info:
        extract_text_google(Path("/nonexistent/image.png"))

    assert exc_info.value.code == "IMAGE_NOT_FOUND"


@patch("ocr_tool.engines.google.vision")
def test_successful_extraction_with_api_key(
    mock_vision: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Returns extracted text using API key authentication."""
    monkeypatch.setenv("GOOGLE_CLOUD_VISION_API_KEY", "test-api-key")
    image_file = tmp_path / "photo.png"
    image_file.write_bytes(b"fake image data")

    mock_annotation = MagicMock()
    mock_annotation.text = "Hello World"

    mock_error = MagicMock()
    mock_error.message = ""

    mock_response = MagicMock()
    mock_response.error = mock_error
    mock_response.full_text_annotation = mock_annotation

    mock_client = MagicMock()
    mock_client.document_text_detection.return_value = mock_response
    mock_vision.ImageAnnotatorClient.return_value = mock_client

    result = extract_text_google(image_file)

    assert result == "Hello World"
    mock_vision.ImageAnnotatorClient.assert_called_once_with(
        client_options={"api_key": "test-api-key"}
    )
    mock_vision.Image.assert_called_once_with(content=b"fake image data")
    mock_client.document_text_detection.assert_called_once()


@patch("ocr_tool.engines.google.vision")
def test_empty_result_returns_empty_string(
    mock_vision: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Returns empty string when Vision API finds no text."""
    monkeypatch.setenv("GOOGLE_CLOUD_VISION_API_KEY", "test-api-key")
    image_file = tmp_path / "blank.png"
    image_file.write_bytes(b"fake image data")

    mock_annotation = MagicMock()
    mock_annotation.text = ""

    mock_error = MagicMock()
    mock_error.message = ""

    mock_response = MagicMock()
    mock_response.error = mock_error
    mock_response.full_text_annotation = mock_annotation

    mock_client = MagicMock()
    mock_client.document_text_detection.return_value = mock_response
    mock_vision.ImageAnnotatorClient.return_value = mock_client

    result = extract_text_google(image_file)

    assert result == ""


@patch("ocr_tool.engines.google.vision")
def test_pdf_extraction_uses_batch_annotate_files(
    mock_vision: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """PDF files are processed via batch_annotate_files with correct InputConfig."""
    monkeypatch.setenv("GOOGLE_CLOUD_VISION_API_KEY", "test-api-key")
    pdf_file = tmp_path / "document.pdf"
    pdf_file.write_bytes(b"fake pdf data")

    # Set up page responses with text
    mock_page1 = MagicMock()
    mock_page1.full_text_annotation.text = "Page 1 text"
    mock_page2 = MagicMock()
    mock_page2.full_text_annotation.text = "Page 2 text"

    mock_file_response = MagicMock()
    mock_file_response.error.message = ""
    mock_file_response.total_pages = 2
    mock_file_response.responses = [mock_page1, mock_page2]

    mock_batch_response = MagicMock()
    mock_batch_response.responses = [mock_file_response]

    mock_client = MagicMock()
    mock_client.batch_annotate_files.return_value = mock_batch_response
    mock_vision.ImageAnnotatorClient.return_value = mock_client

    result = extract_text_google(pdf_file)

    assert result == "Page 1 text\nPage 2 text"
    mock_vision.InputConfig.assert_called_once_with(
        mime_type="application/pdf",
        content=b"fake pdf data",
    )
    mock_client.batch_annotate_files.assert_called_once()


@patch("ocr_tool.engines.google.vision")
def test_pdf_exceeding_page_limit_raises_error(
    mock_vision: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Raises OcrError with PDF_TOO_LARGE when PDF exceeds 5 pages."""
    monkeypatch.setenv("GOOGLE_CLOUD_VISION_API_KEY", "test-api-key")
    pdf_file = tmp_path / "big.pdf"
    pdf_file.write_bytes(b"fake pdf data")

    mock_file_response = MagicMock()
    mock_file_response.error.message = ""
    mock_file_response.total_pages = 10
    mock_file_response.responses = []

    mock_batch_response = MagicMock()
    mock_batch_response.responses = [mock_file_response]

    mock_client = MagicMock()
    mock_client.batch_annotate_files.return_value = mock_batch_response
    mock_vision.ImageAnnotatorClient.return_value = mock_client

    with pytest.raises(OcrError) as exc_info:
        extract_text_google(pdf_file)

    assert exc_info.value.code == "PDF_TOO_LARGE"
    assert "10 pages" in str(exc_info.value)
    assert "5" in str(exc_info.value)


def test_unsupported_file_type_raises_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Raises OcrError with INVALID_FILE for unsupported file extensions."""
    monkeypatch.setenv("GOOGLE_CLOUD_VISION_API_KEY", "test-api-key")
    txt_file = tmp_path / "notes.txt"
    txt_file.write_bytes(b"not an image")

    with pytest.raises(OcrError) as exc_info:
        extract_text_google(txt_file)

    assert exc_info.value.code == "INVALID_FILE"
    assert ".txt" in str(exc_info.value)
