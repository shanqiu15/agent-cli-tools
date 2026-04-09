"""End-to-end tests for bash_tool using real shell execution."""

import json

from typer.testing import CliRunner

from bash_tool.cli import app

runner = CliRunner()


class TestBashE2E:
    def test_echo_command(self) -> None:
        result = runner.invoke(app, ["run", "--command", "echo hello world"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "hello world" in data["result"]["stdout"]
        assert data["result"]["exit_code"] == 0
        assert data["result"]["truncated"] is False

    def test_nonzero_exit_code_is_not_tool_error(self) -> None:
        result = runner.invoke(app, ["run", "--command", "exit 42"])
        assert result.exit_code == 0  # tool succeeds even if command fails
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["result"]["exit_code"] == 42

    def test_stderr_captured(self) -> None:
        result = runner.invoke(app, ["run", "--command", "echo error >&2"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "error" in data["result"]["stderr"]

    def test_timeout(self) -> None:
        result = runner.invoke(app, ["run", "--command", "sleep 10", "--timeout", "1"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "TIMEOUT"

    def test_empty_command_rejected(self) -> None:
        result = runner.invoke(app, ["run", "--command", "   "])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "INVALID_INPUT"

    def test_output_truncation(self) -> None:
        result = runner.invoke(
            app,
            ["run", "--command", "python3 -c \"print('x' * 500)\"", "--max-output", "100"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["result"]["truncated"] is True
        assert "Truncated" in data["result"]["stdout"]

    def test_multiline_output(self) -> None:
        result = runner.invoke(app, ["run", "--command", "printf 'line1\\nline2\\nline3'"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "line1" in data["result"]["stdout"]
        assert "line3" in data["result"]["stdout"]
