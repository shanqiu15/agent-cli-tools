"""Tests for the bash tool service layer."""

import pytest

from bash_tool.errors import BashError
from bash_tool.service import run_command


def test_successful_command() -> None:
    """A simple echo command returns expected stdout."""
    result = run_command("echo hello")
    assert result.stdout.strip() == "hello"
    assert result.stderr == ""
    assert result.exit_code == 0
    assert result.truncated is False


def test_command_failure() -> None:
    """A failing command returns non-zero exit code."""
    result = run_command("exit 42")
    assert result.exit_code == 42
    assert result.truncated is False


def test_timeout() -> None:
    """A long-running command raises TIMEOUT error."""
    with pytest.raises(BashError) as exc_info:
        run_command("sleep 60", timeout=1)
    assert exc_info.value.code == "TIMEOUT"
    assert exc_info.value.details["timeout"] == 1


def test_output_truncation() -> None:
    """Output exceeding max_output is truncated with indicator."""
    result = run_command("python3 -c \"print('x' * 500)\"", max_output=100)
    assert result.truncated is True
    assert "[Truncated" in result.stdout
    assert len(result.stdout.split("\n[Truncated")[0]) == 100


def test_empty_command() -> None:
    """An empty command raises INVALID_INPUT error."""
    with pytest.raises(BashError) as exc_info:
        run_command("   ")
    assert exc_info.value.code == "INVALID_INPUT"
