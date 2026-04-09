"""Tests for the vision tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from vision_tool.cli import app
from vision_tool.errors import VisionError
from vision_tool.models import AnalyzeResult

runner = CliRunner()


def test_help_exits_zero() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "analyze" in result.output


def test_analyze_help() -> None:
    """The analyze --help flag shows subcommand options."""
    result = runner.invoke(app, ["analyze", "--help"])
    assert result.exit_code == 0
    assert "--image" in result.output
    assert "--prompt" in result.output


@patch("vision_tool.cli.analyze_image")
def test_analyze_success(mock_analyze: object) -> None:
    """Successful analyze emits JSON with ok=true and expected fields."""
    mock_analyze.return_value = AnalyzeResult(  # type: ignore[attr-defined]
        analysis="A photo of a cat",
        provider="gemini",
        model="gemini-2.0-flash",
    )
    result = runner.invoke(app, ["analyze", "--image", "test.png", "--prompt", "describe"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["analysis"] == "A photo of a cat"
    assert data["result"]["provider"] == "gemini"
    assert data["result"]["model"] == "gemini-2.0-flash"


@patch("vision_tool.cli.analyze_image")
def test_analyze_error(mock_analyze: object) -> None:
    """An error from analyze_image emits JSON with ok=false."""
    mock_analyze.side_effect = VisionError(  # type: ignore[attr-defined]
        code="FILE_NOT_FOUND",
        message="Image file not found: test.png",
        details={"path": "test.png"},
    )
    result = runner.invoke(app, ["analyze", "--image", "test.png", "--prompt", "describe"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "FILE_NOT_FOUND"


@patch("vision_tool.cli.analyze_image")
def test_analyze_missing_credentials(mock_analyze: object) -> None:
    """Missing credentials returns ok=false with MISSING_CREDENTIALS code."""
    mock_analyze.side_effect = VisionError(  # type: ignore[attr-defined]
        code="MISSING_CREDENTIALS",
        message="API key not found",
        details={"provider": "gemini"},
    )
    result = runner.invoke(app, ["analyze", "--image", "test.png", "--prompt", "describe"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "MISSING_CREDENTIALS"
