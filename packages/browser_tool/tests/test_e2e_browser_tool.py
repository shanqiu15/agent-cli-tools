"""End-to-end tests for browser_tool.

These tests validate CLI argument handling and error paths.
Full browser automation tests require playwright-cli and are marked external.
"""

import json

import pytest
from typer.testing import CliRunner

from browser_tool.cli import app

runner = CliRunner()


class TestBrowserCLIArgs:
    def test_status_default_session(self) -> None:
        """Status command should work even if no browser is running."""
        result = runner.invoke(app, ["status"])
        # May succeed (returning running=false) or fail (playwright-cli not found)
        data = json.loads(result.output)
        if data["ok"]:
            assert data["result"]["running"] is False
        else:
            assert data["error"]["code"] in ("PLAYWRIGHT_CLI_NOT_FOUND", "BROWSER_STATUS_FAILED")

    def test_custom_session_name(self) -> None:
        result = runner.invoke(app, ["status", "--session", "my-session"])
        data = json.loads(result.output)
        # Verify the session name is passed through
        if data["ok"]:
            assert data["result"]["session"] == "my-session"


@pytest.mark.external
class TestBrowserE2E:
    def test_start_navigate_snapshot_stop(self) -> None:
        """Full lifecycle: start, navigate, snapshot, stop."""
        # Start
        result = runner.invoke(app, ["start"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True

        try:
            # Navigate
            result = runner.invoke(app, ["navigate", "--url", "https://example.com"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["ok"] is True

            # Snapshot
            result = runner.invoke(app, ["snapshot"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["ok"] is True
            assert len(data["result"]["output"]) > 0
        finally:
            # Always stop
            runner.invoke(app, ["stop"])
