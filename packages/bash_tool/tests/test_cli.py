"""Tests for the bash tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from bash_tool.cli import app
from bash_tool.errors import BashError
from bash_tool.models import CommandResult

runner = CliRunner()


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.output.lower()


@patch("bash_tool.cli.run_command")
def test_successful_command(mock_run) -> None:  # type: ignore[no-untyped-def]
    """A successful command emits JSON with ok=true and result."""
    mock_run.return_value = CommandResult(
        stdout="hello world\n",
        stderr="",
        exit_code=0,
        truncated=False,
    )

    result = runner.invoke(app, ["run", "--command", "echo hello world"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["stdout"] == "hello world\n"
    assert data["result"]["stderr"] == ""
    assert data["result"]["exit_code"] == 0
    assert data["result"]["truncated"] is False


@patch("bash_tool.cli.run_command")
def test_command_failure(mock_run) -> None:  # type: ignore[no-untyped-def]
    """A command with non-zero exit still returns ok=true with the exit code."""
    mock_run.return_value = CommandResult(
        stdout="",
        stderr="ls: no such file\n",
        exit_code=2,
        truncated=False,
    )

    result = runner.invoke(app, ["run", "--command", "ls /nonexistent"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["exit_code"] == 2
    assert "no such file" in data["result"]["stderr"]


@patch(
    "bash_tool.cli.run_command",
    side_effect=BashError(
        code="TIMEOUT",
        message="Command timed out after 5 seconds",
        details={"timeout": 5, "partial_stdout": "", "partial_stderr": ""},
    ),
)
def test_timeout_error(mock_run) -> None:  # type: ignore[no-untyped-def]
    """Timeout emits structured error with TIMEOUT code."""
    result = runner.invoke(app, ["run", "--command", "sleep 100", "--timeout", "5"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "TIMEOUT"


@patch(
    "bash_tool.cli.run_command",
    side_effect=BashError(
        code="INVALID_INPUT",
        message="Command must not be empty",
    ),
)
def test_empty_command(mock_run) -> None:  # type: ignore[no-untyped-def]
    """Empty command emits INVALID_INPUT error."""
    result = runner.invoke(app, ["run", "--command", "   "])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_INPUT"
