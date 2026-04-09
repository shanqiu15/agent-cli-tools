"""Tests for the transcription tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from transcription_tool.cli import app
from transcription_tool.errors import TranscriptionError
from transcription_tool.models import TranscribeResult

runner = CliRunner()


def test_help_exits_zero() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "transcribe" in result.output


def test_transcribe_help() -> None:
    """The transcribe --help flag shows subcommand options."""
    result = runner.invoke(app, ["transcribe", "--help"])
    assert result.exit_code == 0
    assert "--file" in result.output


@patch("transcription_tool.cli.transcribe_audio")
def test_transcribe_success(mock_transcribe: object) -> None:
    """Successful transcription emits JSON with ok=true and expected fields."""
    mock_transcribe.return_value = TranscribeResult(  # type: ignore[attr-defined]
        transcript="Hello, world!",
        provider="groq",
        model="whisper-large-v3",
    )
    result = runner.invoke(app, ["transcribe", "--file", "test.mp3"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["transcript"] == "Hello, world!"
    assert data["result"]["provider"] == "groq"
    assert data["result"]["model"] == "whisper-large-v3"


@patch("transcription_tool.cli.transcribe_audio")
def test_transcribe_error(mock_transcribe: object) -> None:
    """An error from transcribe_audio emits JSON with ok=false."""
    mock_transcribe.side_effect = TranscriptionError(  # type: ignore[attr-defined]
        code="FILE_NOT_FOUND",
        message="Audio file not found: test.mp3",
        details={"path": "test.mp3"},
    )
    result = runner.invoke(app, ["transcribe", "--file", "test.mp3"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "FILE_NOT_FOUND"


@patch("transcription_tool.cli.transcribe_audio")
def test_transcribe_missing_credentials(mock_transcribe: object) -> None:
    """Missing credentials returns ok=false with MISSING_CREDENTIALS code."""
    mock_transcribe.side_effect = TranscriptionError(  # type: ignore[attr-defined]
        code="MISSING_CREDENTIALS",
        message="API key not found",
        details={"provider": "groq"},
    )
    result = runner.invoke(app, ["transcribe", "--file", "test.mp3"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "MISSING_CREDENTIALS"
