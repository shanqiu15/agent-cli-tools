"""Tests for the browser tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from browser_tool.cli import app
from browser_tool.errors import BrowserError
from browser_tool.models import BrowserResult

runner = CliRunner()


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "start" in result.output.lower()
    assert "navigate" in result.output.lower()


@patch("browser_tool.cli._get_cli")
def test_start_session(mock_get_cli) -> None:  # type: ignore[no-untyped-def]
    """Start command emits JSON with ok=true."""
    mock_cli = mock_get_cli.return_value
    mock_cli.start.return_value = BrowserResult(
        action="start",
        output="Browser started",
        session="default",
    )

    result = runner.invoke(app, ["start"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["action"] == "start"
    assert data["result"]["session"] == "default"


@patch("browser_tool.cli._get_cli")
def test_stop_session(mock_get_cli) -> None:  # type: ignore[no-untyped-def]
    """Stop command emits JSON with ok=true."""
    mock_cli = mock_get_cli.return_value
    mock_cli.stop.return_value = BrowserResult(
        action="stop",
        output="Browser stopped",
        session="default",
    )

    result = runner.invoke(app, ["stop"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["action"] == "stop"


@patch("browser_tool.cli._get_cli")
def test_navigate(mock_get_cli) -> None:  # type: ignore[no-untyped-def]
    """Navigate command emits page snapshot output."""
    mock_cli = mock_get_cli.return_value
    mock_cli.navigate.return_value = BrowserResult(
        action="navigate",
        output="- heading 'Example Domain'\n- link 'More information...'",
        session="default",
    )

    result = runner.invoke(app, ["navigate", "--url", "https://example.com"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["action"] == "navigate"
    assert "Example Domain" in data["result"]["output"]


@patch("browser_tool.cli._get_cli")
def test_snapshot(mock_get_cli) -> None:  # type: ignore[no-untyped-def]
    """Snapshot command returns accessibility tree."""
    mock_cli = mock_get_cli.return_value
    mock_cli.snapshot.return_value = BrowserResult(
        action="snapshot",
        output="- document\n  - heading 'Test Page'",
        session="default",
    )

    result = runner.invoke(app, ["snapshot"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["action"] == "snapshot"


@patch("browser_tool.cli._get_cli")
def test_click(mock_get_cli) -> None:  # type: ignore[no-untyped-def]
    """Click command emits ok=true on success."""
    mock_cli = mock_get_cli.return_value
    mock_cli.click.return_value = BrowserResult(
        action="click",
        output="Clicked element ref=s1e2",
        session="default",
    )

    result = runner.invoke(app, ["click", "--ref", "s1e2"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["action"] == "click"


@patch(
    "browser_tool.cli._get_cli",
    side_effect=BrowserError(
        code="PLAYWRIGHT_CLI_NOT_FOUND",
        message="playwright-cli not found in PATH. Install it with: npm install -g @playwright/cli@latest",
    ),
)
def test_playwright_not_found(mock_get_cli) -> None:  # type: ignore[no-untyped-def]
    """Missing playwright-cli emits structured error."""
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "PLAYWRIGHT_CLI_NOT_FOUND"
    assert "npm install" in data["error"]["message"]
