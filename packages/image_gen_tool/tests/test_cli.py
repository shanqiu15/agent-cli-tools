"""Tests for the image gen tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from cli_common.errors import ToolException
from image_gen_tool.cli import app
from image_gen_tool.models import ImageGenResponse

runner = CliRunner()


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "generate" in result.output.lower()


@patch("image_gen_tool.cli.generate")
def test_successful_generate(mock_generate, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A successful generation emits JSON with ok=true and structured result."""
    out_file = str(tmp_path / "test.png")
    mock_generate.return_value = ImageGenResponse(
        path=out_file,
        prompt="a cat",
        aspect_ratio="1:1",
    )

    result = runner.invoke(
        app, ["generate", "--prompt", "a cat", "--output-path", out_file]
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["path"] == out_file
    assert data["result"]["prompt"] == "a cat"
    assert data["result"]["aspect_ratio"] == "1:1"


@patch(
    "image_gen_tool.cli.generate",
    side_effect=ToolException(
        code="MISSING_CREDENTIALS",
        message="Environment variable GOOGLE_API_KEY is not set",
        details={"env_var": "GOOGLE_API_KEY"},
    ),
)
def test_missing_api_key(mock_generate) -> None:  # type: ignore[no-untyped-def]
    """Missing GOOGLE_API_KEY emits structured error."""
    result = runner.invoke(
        app, ["generate", "--prompt", "a cat", "--output-path", "/tmp/out.png"]
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "MISSING_CREDENTIALS"


def test_invalid_aspect_ratio() -> None:
    """Invalid aspect ratio emits INVALID_INPUT error."""
    result = runner.invoke(
        app,
        [
            "generate",
            "--prompt",
            "a cat",
            "--output-path",
            "/tmp/out.png",
            "--aspect-ratio",
            "2:1",
        ],
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_INPUT"
    assert "2:1" in data["error"]["message"]
