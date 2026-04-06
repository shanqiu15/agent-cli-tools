"""Tests for the LLM OCR engine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ocr_tool.engines.llm import extract_text_llm
from ocr_tool.errors import OcrError


def test_missing_api_key_raises_ocr_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Raises OcrError with MISSING_API_KEY when env var is not set."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(OcrError) as exc_info:
        extract_text_llm(tmp_path / "image.png")

    assert exc_info.value.code == "MISSING_API_KEY"


def test_file_not_found_raises_ocr_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises OcrError with IMAGE_NOT_FOUND for a missing file."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    with pytest.raises(OcrError) as exc_info:
        extract_text_llm(Path("/nonexistent/image.png"))

    assert exc_info.value.code == "IMAGE_NOT_FOUND"


def test_invalid_image_raises_ocr_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Raises OcrError with INVALID_IMAGE for a non-image file."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    bad_file = tmp_path / "bad.png"
    bad_file.write_text("this is not an image")

    with pytest.raises(OcrError) as exc_info:
        extract_text_llm(bad_file)

    assert exc_info.value.code == "INVALID_IMAGE"


@patch("ocr_tool.engines.llm.anthropic")
@patch("ocr_tool.engines.llm.Image")
def test_successful_extraction(
    mock_image: MagicMock,
    mock_anthropic: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Returns extracted text from a mocked Anthropic API call."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    image_file = tmp_path / "photo.png"
    image_file.write_bytes(b"fake image data")

    mock_text_block = MagicMock()
    mock_text_block.text = "Hello World"
    mock_message = MagicMock()
    mock_message.content = [mock_text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.Anthropic.return_value = mock_client

    result = extract_text_llm(image_file)

    assert result == "Hello World"
    mock_anthropic.Anthropic.assert_called_once_with(api_key="test-key")
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["model"] == "claude-sonnet-4-20250514"


@patch("ocr_tool.engines.llm.anthropic")
@patch("ocr_tool.engines.llm.Image")
def test_custom_model_override(
    mock_image: MagicMock,
    mock_anthropic: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Uses custom model when provided."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    image_file = tmp_path / "photo.png"
    image_file.write_bytes(b"fake image data")

    mock_text_block = MagicMock()
    mock_text_block.text = "Custom model result"
    mock_message = MagicMock()
    mock_message.content = [mock_text_block]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.Anthropic.return_value = mock_client

    result = extract_text_llm(image_file, model="claude-opus-4-20250514")

    assert result == "Custom model result"
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["model"] == "claude-opus-4-20250514"
