"""End-to-end tests for cron_tool."""

import json

import pytest
from typer.testing import CliRunner

from cron_tool.cli import app

runner = CliRunner()


class TestCronValidation:
    def test_missing_gateway_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CRON_GATEWAY_URL", raising=False)
        result = runner.invoke(
            app,
            ["create", "--name", "test", "--schedule", "0 9 * * *", "--command", "echo hi"],
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "MISSING_CREDENTIALS"

    def test_invalid_schedule_format(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CRON_GATEWAY_URL", "http://localhost:8080")
        result = runner.invoke(
            app,
            ["create", "--name", "test", "--schedule", "not a schedule", "--command", "echo hi"],
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "INVALID_INPUT"

    def test_valid_cron_expression_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Validate that schedule parsing works for cron expressions.
        This will fail at the HTTP call but proves input validation passes."""
        monkeypatch.setenv("CRON_GATEWAY_URL", "http://localhost:1")
        result = runner.invoke(
            app,
            ["create", "--name", "test", "--schedule", "0 9 * * 1-5", "--command", "echo hi"],
        )
        # Should fail with network error, NOT INVALID_INPUT
        if result.output.strip():
            data = json.loads(result.output)
            assert data["error"]["code"] != "INVALID_INPUT"
        else:
            # Connection error raised before emit_error — still proves validation passed
            assert result.exit_code != 0

    def test_valid_interval_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CRON_GATEWAY_URL", "http://localhost:1")
        result = runner.invoke(
            app,
            ["create", "--name", "test", "--schedule", "every 5m", "--command", "echo hi"],
        )
        if result.output.strip():
            data = json.loads(result.output)
            assert data["error"]["code"] != "INVALID_INPUT"
        else:
            assert result.exit_code != 0
