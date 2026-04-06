"""Tests for the Google Cloud Vision OCR engine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ocr_tool.engines.google import extract_text_google
from ocr_tool.errors import OcrError


def test_missing_credentials_raises_ocr_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raises OcrError with MISSING_CREDENTIALS when no credentials are available."""
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

    with patch("google.auth.default", side_effect=Exception("No credentials")):
        with pytest.raises(OcrError) as exc_info:
            extract_text_google(Path("/some/image.png"))

        assert exc_info.value.code == "MISSING_CREDENTIALS"


def test_file_not_found_raises_ocr_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raises OcrError with IMAGE_NOT_FOUND for a missing file."""
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/path/to/creds.json")

    with pytest.raises(OcrError) as exc_info:
        extract_text_google(Path("/nonexistent/image.png"))

    assert exc_info.value.code == "IMAGE_NOT_FOUND"


@patch("ocr_tool.engines.google.vision")
def test_successful_extraction(
    mock_vision: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Returns extracted text from a mocked Vision API call."""
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/path/to/creds.json")
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
    mock_vision.Image.assert_called_once_with(content=b"fake image data")
    mock_client.document_text_detection.assert_called_once()


@patch("ocr_tool.engines.google.vision")
def test_empty_result_returns_empty_string(
    mock_vision: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Returns empty string when Vision API finds no text."""
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/path/to/creds.json")
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
