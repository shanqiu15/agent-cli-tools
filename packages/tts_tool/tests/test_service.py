"""Tests for the TTS tool service layer."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tts_tool.errors import TTSError
from tts_tool.service import (
    _validate_text,
    speak_text,
)


# --- Text validation ---


def test_validate_empty_text() -> None:
    """Empty text raises INVALID_INPUT."""
    with pytest.raises(TTSError) as exc_info:
        _validate_text("")
    assert exc_info.value.code == "INVALID_INPUT"


def test_validate_whitespace_only_text() -> None:
    """Whitespace-only text raises INVALID_INPUT."""
    with pytest.raises(TTSError) as exc_info:
        _validate_text("   \n\t  ")
    assert exc_info.value.code == "INVALID_INPUT"


def test_validate_text_too_long() -> None:
    """Text exceeding 4000 characters raises INVALID_INPUT."""
    long_text = "a" * 4001
    with pytest.raises(TTSError) as exc_info:
        _validate_text(long_text)
    assert exc_info.value.code == "INVALID_INPUT"


def test_validate_text_at_limit() -> None:
    """Text exactly at 4000 characters passes validation."""
    text = "a" * 4000
    _validate_text(text)  # Should not raise


# --- Edge TTS generation (mocked) ---


@patch("tts_tool.service.edge.speak")
def test_speak_edge_success(mock_edge: MagicMock) -> None:
    """Text spoken via Edge TTS returns correct result."""
    mock_edge.return_value = "en-US-AriaNeural"

    d = Path(tempfile.mkdtemp())
    output = d / "output.mp3"

    result = speak_text(
        text="Hello, world!",
        output=str(output),
        provider="edge",
    )
    assert result.file_path == str(output)
    assert result.provider == "edge"
    assert result.voice == "en-US-AriaNeural"
    mock_edge.assert_called_once()


# --- OpenAI TTS generation (mocked) ---


@patch("tts_tool.service.openai.speak")
def test_speak_openai_success(mock_openai: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Text spoken via OpenAI TTS returns correct result."""
    from cli_common.config import clear_cache

    clear_cache()

    d = Path(tempfile.mkdtemp())
    output = d / "output.mp3"

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")

    mock_openai.return_value = "alloy"

    result = speak_text(
        text="Hello, world!",
        output=str(output),
        provider="openai",
        config_path="/tmp/nonexistent_config.yaml",
    )
    assert result.file_path == str(output)
    assert result.provider == "openai"
    assert result.voice == "alloy"
    mock_openai.assert_called_once()


# --- Voice override ---


@patch("tts_tool.service.edge.speak")
def test_voice_override(mock_edge: MagicMock) -> None:
    """Explicit --voice overrides the default."""
    mock_edge.return_value = "en-US-GuyNeural"

    d = Path(tempfile.mkdtemp())
    output = d / "output.mp3"

    result = speak_text(
        text="Hello!",
        output=str(output),
        provider="edge",
        voice="en-US-GuyNeural",
    )
    assert result.voice == "en-US-GuyNeural"
    call_args = mock_edge.call_args
    assert call_args[1]["voice"] == "en-US-GuyNeural"


# --- Default output path ---


@patch("tts_tool.service.edge.speak")
def test_default_output_path(mock_edge: MagicMock) -> None:
    """When no --output is given, a temp file path is generated."""
    mock_edge.return_value = "en-US-AriaNeural"

    result = speak_text(
        text="Hello!",
        provider="edge",
    )
    assert result.file_path.endswith(".mp3")
    assert "tts_tool" in result.file_path


# --- Missing credentials for OpenAI ---


def test_speak_openai_missing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing OpenAI API key raises MISSING_CREDENTIALS."""
    from cli_common.config import clear_cache

    clear_cache()

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TTS_PROVIDER", raising=False)

    d = Path(tempfile.mkdtemp())
    output = d / "output.mp3"

    with pytest.raises(TTSError) as exc_info:
        speak_text(
            text="Hello!",
            output=str(output),
            provider="openai",
            config_path="/tmp/nonexistent_config.yaml",
        )
    assert exc_info.value.code == "MISSING_CREDENTIALS"


# --- Provider selection logic ---


@patch("tts_tool.service.edge.speak")
def test_provider_defaults_to_edge(mock_edge: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """When no provider is set, defaults to edge."""
    from cli_common.config import clear_cache

    clear_cache()

    monkeypatch.delenv("TTS_PROVIDER", raising=False)

    mock_edge.return_value = "en-US-AriaNeural"

    d = Path(tempfile.mkdtemp())
    output = d / "output.mp3"

    result = speak_text(
        text="Hello!",
        output=str(output),
        config_path="/tmp/nonexistent_config.yaml",
    )
    assert result.provider == "edge"
    mock_edge.assert_called_once()


@patch("tts_tool.service.openai.speak")
def test_provider_env_var_override(mock_openai: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """TTS_PROVIDER env var overrides default."""
    from cli_common.config import clear_cache

    clear_cache()

    monkeypatch.setenv("TTS_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_openai.return_value = "alloy"

    d = Path(tempfile.mkdtemp())
    output = d / "output.mp3"

    result = speak_text(
        text="Hello!",
        output=str(output),
        config_path="/tmp/nonexistent_config.yaml",
    )
    assert result.provider == "openai"
    mock_openai.assert_called_once()


# --- Invalid provider ---


def test_invalid_provider() -> None:
    """Invalid provider raises INVALID_INPUT."""
    with pytest.raises(TTSError) as exc_info:
        speak_text(
            text="Hello!",
            provider="invalid",
        )
    assert exc_info.value.code == "INVALID_INPUT"


# --- Response fields ---


@patch("tts_tool.service.edge.speak")
def test_response_fields_populated(mock_edge: MagicMock) -> None:
    """Result model has all expected fields populated."""
    mock_edge.return_value = "en-US-AriaNeural"

    d = Path(tempfile.mkdtemp())
    output = d / "output.mp3"

    result = speak_text(
        text="The quick brown fox",
        output=str(output),
        provider="edge",
    )
    dumped = result.model_dump(mode="json")
    assert "file_path" in dumped
    assert "provider" in dumped
    assert "voice" in dumped
    assert dumped["file_path"] == str(output)
