"""Tests for the local OCR engine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ocr_tool.engines.local import extract_text_local
from ocr_tool.errors import OcrError


def test_file_not_found_raises_ocr_error() -> None:
    """Raises OcrError with IMAGE_NOT_FOUND for a missing file."""
    with pytest.raises(OcrError) as exc_info:
        extract_text_local(Path("/nonexistent/image.png"))

    assert exc_info.value.code == "IMAGE_NOT_FOUND"


def test_invalid_image_raises_ocr_error(tmp_path: Path) -> None:
    """Raises OcrError with INVALID_IMAGE for a non-image file."""
    bad_file = tmp_path / "bad.png"
    bad_file.write_text("this is not an image")

    with pytest.raises(OcrError) as exc_info:
        extract_text_local(bad_file)

    assert exc_info.value.code == "INVALID_IMAGE"


@patch("ocr_tool.engines.local.easyocr")
@patch("ocr_tool.engines.local.Image")
def test_successful_extraction(
    mock_image: MagicMock, mock_easyocr: MagicMock, tmp_path: Path
) -> None:
    """Returns extracted text from a mocked easyocr reader."""
    image_file = tmp_path / "photo.png"
    image_file.write_bytes(b"fake image data")

    mock_reader = MagicMock()
    mock_reader.readtext.return_value = ["Hello", "World"]
    mock_easyocr.Reader.return_value = mock_reader

    result = extract_text_local(image_file)

    assert result == "Hello\nWorld"
    mock_easyocr.Reader.assert_called_once_with(["en"], verbose=False)
    mock_reader.readtext.assert_called_once_with(str(image_file), detail=0)


@patch("ocr_tool.engines.local.easyocr")
@patch("ocr_tool.engines.local.Image")
def test_text_joining_multiple_lines(
    mock_image: MagicMock, mock_easyocr: MagicMock, tmp_path: Path
) -> None:
    """Joins multiple text fragments with newlines."""
    image_file = tmp_path / "doc.png"
    image_file.write_bytes(b"fake image data")

    mock_reader = MagicMock()
    mock_reader.readtext.return_value = ["Line 1", "Line 2", "Line 3"]
    mock_easyocr.Reader.return_value = mock_reader

    result = extract_text_local(image_file)

    assert result == "Line 1\nLine 2\nLine 3"
    assert result.count("\n") == 2


@patch("ocr_tool.engines.local.easyocr")
@patch("ocr_tool.engines.local.Image")
def test_empty_extraction_returns_empty_string(
    mock_image: MagicMock, mock_easyocr: MagicMock, tmp_path: Path
) -> None:
    """Returns empty string when easyocr finds no text."""
    image_file = tmp_path / "blank.png"
    image_file.write_bytes(b"fake image data")

    mock_reader = MagicMock()
    mock_reader.readtext.return_value = []
    mock_easyocr.Reader.return_value = mock_reader

    result = extract_text_local(image_file)

    assert result == ""
