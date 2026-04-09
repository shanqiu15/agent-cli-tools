"""Tests for the transcription tool service layer."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from transcription_tool.errors import TranscriptionError
from transcription_tool.service import (
    _validate_audio_file,
    transcribe_audio,
)


def _make_audio_file(directory: Path, name: str = "test.mp3", size: int = 100) -> Path:
    """Create a dummy audio file for testing."""
    path = directory / name
    path.write_bytes(b"\x00" * size)
    return path


# --- File validation ---


def test_validate_file_not_found() -> None:
    """Non-existent file raises FILE_NOT_FOUND."""
    with pytest.raises(TranscriptionError) as exc_info:
        _validate_audio_file(Path("/tmp/nonexistent_audio_abc123.mp3"))
    assert exc_info.value.code == "FILE_NOT_FOUND"


def test_validate_not_a_file(tmp_path: Path) -> None:
    """Directory path raises INVALID_INPUT."""
    with pytest.raises(TranscriptionError) as exc_info:
        _validate_audio_file(tmp_path)
    assert exc_info.value.code == "INVALID_INPUT"


def test_validate_wrong_extension(tmp_path: Path) -> None:
    """Unsupported extension raises INVALID_INPUT."""
    bad_file = tmp_path / "test.txt"
    bad_file.write_bytes(b"\x00" * 100)
    with pytest.raises(TranscriptionError) as exc_info:
        _validate_audio_file(bad_file)
    assert exc_info.value.code == "INVALID_INPUT"


def test_validate_file_too_large(tmp_path: Path) -> None:
    """Oversized file raises FILE_TOO_LARGE."""
    big_file = tmp_path / "big.mp3"
    # Create a file that reports > 25MB via stat
    big_file.write_bytes(b"\x00" * (25 * 1024 * 1024 + 1))
    with pytest.raises(TranscriptionError) as exc_info:
        _validate_audio_file(big_file)
    assert exc_info.value.code == "FILE_TOO_LARGE"


def test_validate_valid_extensions(tmp_path: Path) -> None:
    """All valid extensions pass validation."""
    for ext in ("mp3", "wav", "ogg", "m4a", "webm", "flac"):
        audio = _make_audio_file(tmp_path, f"test.{ext}")
        _validate_audio_file(audio)  # Should not raise


# --- Transcription: file not found ---


def test_transcribe_file_not_found() -> None:
    """Transcribing a non-existent file raises FILE_NOT_FOUND."""
    with pytest.raises(TranscriptionError) as exc_info:
        transcribe_audio(file="/tmp/nonexistent_audio_abc123.mp3")
    assert exc_info.value.code == "FILE_NOT_FOUND"


# --- Missing credentials ---


def test_transcribe_missing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing API key raises MISSING_CREDENTIALS."""
    d = Path(tempfile.mkdtemp())
    audio = _make_audio_file(d, "test.mp3")

    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TRANSCRIPTION_PROVIDER", raising=False)

    from cli_common.config import clear_cache

    clear_cache()

    with pytest.raises(TranscriptionError) as exc_info:
        transcribe_audio(
            file=str(audio),
            provider="groq",
            config_path="/tmp/nonexistent_config.yaml",
        )
    assert exc_info.value.code == "MISSING_CREDENTIALS"


# --- Successful transcription with mocked API ---


@patch("transcription_tool.service.groq.transcribe")
def test_transcribe_groq_success(mock_groq: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Audio transcribed via Groq engine returns correct result."""
    from cli_common.config import clear_cache

    clear_cache()

    d = Path(tempfile.mkdtemp())
    audio = _make_audio_file(d, "test.mp3")

    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.delenv("TRANSCRIPTION_PROVIDER", raising=False)

    mock_groq.return_value = ("Hello from Groq Whisper", "whisper-large-v3")

    result = transcribe_audio(
        file=str(audio),
        provider="groq",
        config_path="/tmp/nonexistent_config.yaml",
    )
    assert result.transcript == "Hello from Groq Whisper"
    assert result.provider == "groq"
    assert result.model == "whisper-large-v3"

    mock_groq.assert_called_once()
    call_args = mock_groq.call_args
    assert call_args[0][1] == "test-groq-key"


@patch("transcription_tool.service.openai.transcribe")
def test_transcribe_openai_success(mock_openai: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Audio transcribed via OpenAI engine returns correct result."""
    from cli_common.config import clear_cache

    clear_cache()

    d = Path(tempfile.mkdtemp())
    audio = _make_audio_file(d, "test.mp3")

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")

    mock_openai.return_value = ("Hello from OpenAI Whisper", "whisper-1")

    result = transcribe_audio(
        file=str(audio),
        provider="openai",
        config_path="/tmp/nonexistent_config.yaml",
    )
    assert result.transcript == "Hello from OpenAI Whisper"
    assert result.provider == "openai"
    assert result.model == "whisper-1"

    mock_openai.assert_called_once()


# --- Provider selection logic ---


@patch("transcription_tool.service.groq.transcribe")
def test_provider_defaults_to_groq(mock_groq: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """When no provider is set, defaults to groq."""
    from cli_common.config import clear_cache

    clear_cache()

    d = Path(tempfile.mkdtemp())
    audio = _make_audio_file(d, "test.mp3")

    monkeypatch.delenv("TRANSCRIPTION_PROVIDER", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    mock_groq.return_value = ("result", "whisper-large-v3")

    result = transcribe_audio(
        file=str(audio),
        config_path="/tmp/nonexistent_config.yaml",
    )
    assert result.provider == "groq"
    mock_groq.assert_called_once()


@patch("transcription_tool.service.openai.transcribe")
def test_provider_env_var_override(mock_openai: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """TRANSCRIPTION_PROVIDER env var overrides default."""
    from cli_common.config import clear_cache

    clear_cache()

    d = Path(tempfile.mkdtemp())
    audio = _make_audio_file(d, "test.mp3")

    monkeypatch.setenv("TRANSCRIPTION_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_openai.return_value = ("result", "whisper-1")

    result = transcribe_audio(
        file=str(audio),
        config_path="/tmp/nonexistent_config.yaml",
    )
    assert result.provider == "openai"
    mock_openai.assert_called_once()


# --- Response parsing ---


@patch("transcription_tool.service.groq.transcribe")
def test_response_fields_populated(mock_groq: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Result model has all expected fields populated."""
    from cli_common.config import clear_cache

    clear_cache()

    d = Path(tempfile.mkdtemp())
    audio = _make_audio_file(d, "test.wav")

    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    mock_groq.return_value = ("The quick brown fox", "whisper-large-v3")

    result = transcribe_audio(
        file=str(audio),
        provider="groq",
        config_path="/tmp/nonexistent_config.yaml",
    )
    dumped = result.model_dump(mode="json")
    assert "transcript" in dumped
    assert "provider" in dumped
    assert "model" in dumped
    assert dumped["transcript"] == "The quick brown fox"
