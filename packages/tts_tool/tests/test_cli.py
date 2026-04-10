"""Tests for the TTS tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from tts_tool.cli import app
from tts_tool.errors import TTSError
from tts_tool.models import SpeakResult

runner = CliRunner()


def test_help_exits_zero() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "speak" in result.output


def test_speak_help() -> None:
    """The speak --help flag shows subcommand options."""
    result = runner.invoke(app, ["speak", "--help"])
    assert result.exit_code == 0
    assert "--text" in result.output
    assert "--output" in result.output


@patch("tts_tool.cli.speak_text")
def test_speak_success(mock_speak: object) -> None:
    """Successful speech generation emits JSON with ok=true and expected fields."""
    mock_speak.return_value = SpeakResult(  # type: ignore[attr-defined]
        file_path="/tmp/output.mp3",
        provider="edge",
        voice="en-US-AriaNeural",
    )
    result = runner.invoke(app, ["speak", "--text", "Hello, world!"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["file_path"] == "/tmp/output.mp3"
    assert data["result"]["provider"] == "edge"
    assert data["result"]["voice"] == "en-US-AriaNeural"


@patch("tts_tool.cli.speak_text")
def test_speak_error(mock_speak: object) -> None:
    """An error from speak_text emits JSON with ok=false."""
    mock_speak.side_effect = TTSError(  # type: ignore[attr-defined]
        code="INVALID_INPUT",
        message="Text must not be empty",
    )
    result = runner.invoke(app, ["speak", "--text", ""])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_INPUT"


@patch("tts_tool.cli.speak_text")
def test_speak_missing_credentials(mock_speak: object) -> None:
    """Missing credentials returns ok=false with MISSING_CREDENTIALS code."""
    mock_speak.side_effect = TTSError(  # type: ignore[attr-defined]
        code="MISSING_CREDENTIALS",
        message="API key not found",
        details={"provider": "openai"},
    )
    result = runner.invoke(app, ["speak", "--text", "Hello"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "MISSING_CREDENTIALS"
