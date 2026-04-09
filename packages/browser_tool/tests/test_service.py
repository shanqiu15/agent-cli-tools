"""Tests for the browser tool service layer."""

import subprocess
from unittest.mock import patch

import pytest

from browser_tool.errors import BrowserError
from browser_tool.service import PlaywrightCLI


@patch("browser_tool.service.shutil.which", return_value=None)
def test_playwright_cli_not_found(mock_which) -> None:  # type: ignore[no-untyped-def]
    """Raises PLAYWRIGHT_CLI_NOT_FOUND when binary is missing."""
    with pytest.raises(BrowserError) as exc_info:
        PlaywrightCLI()
    assert exc_info.value.code == "PLAYWRIGHT_CLI_NOT_FOUND"
    assert "npm install" in str(exc_info.value)


@patch("browser_tool.service.subprocess.run")
@patch("browser_tool.service.shutil.which", return_value="/usr/local/bin/playwright-cli")
def test_start_session(mock_which, mock_run) -> None:  # type: ignore[no-untyped-def]
    """Start launches browser and returns BrowserResult."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="Browser started\n", stderr=""
    )
    cli = PlaywrightCLI()
    result = cli.start()
    assert result.action == "start"
    assert result.session == "default"
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "open" in args
    assert "--headless" in args
    assert "-s=default" in args


@patch("browser_tool.service.subprocess.run")
@patch("browser_tool.service.shutil.which", return_value="/usr/local/bin/playwright-cli")
def test_stop_session(mock_which, mock_run) -> None:  # type: ignore[no-untyped-def]
    """Stop terminates the session."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="Session closed\n", stderr=""
    )
    cli = PlaywrightCLI()
    result = cli.stop()
    assert result.action == "stop"
    args = mock_run.call_args[0][0]
    assert "close" in args


@patch("browser_tool.service.subprocess.run")
@patch("browser_tool.service.shutil.which", return_value="/usr/local/bin/playwright-cli")
def test_navigate(mock_which, mock_run) -> None:  # type: ignore[no-untyped-def]
    """Navigate calls goto with the URL."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="- heading 'Example Domain'\n- link 'More information...'\n",
        stderr="",
    )
    cli = PlaywrightCLI()
    result = cli.navigate("https://example.com")
    assert result.action == "navigate"
    assert "Example Domain" in result.output
    args = mock_run.call_args[0][0]
    assert "goto" in args
    assert "https://example.com" in args


@patch("browser_tool.service.subprocess.run")
@patch("browser_tool.service.shutil.which", return_value="/usr/local/bin/playwright-cli")
def test_snapshot(mock_which, mock_run) -> None:  # type: ignore[no-untyped-def]
    """Snapshot returns accessibility tree output."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="- document\n  - heading 'Test'\n",
        stderr="",
    )
    cli = PlaywrightCLI()
    result = cli.snapshot()
    assert result.action == "snapshot"
    assert "heading" in result.output


@patch("browser_tool.service.subprocess.run")
@patch("browser_tool.service.shutil.which", return_value="/usr/local/bin/playwright-cli")
def test_click(mock_which, mock_run) -> None:  # type: ignore[no-untyped-def]
    """Click calls playwright-cli click with the ref."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="Clicked\n", stderr=""
    )
    cli = PlaywrightCLI()
    result = cli.click("s1e2")
    assert result.action == "click"
    args = mock_run.call_args[0][0]
    assert "click" in args
    assert "s1e2" in args


@patch("browser_tool.service.subprocess.run")
@patch("browser_tool.service.shutil.which", return_value="/usr/local/bin/playwright-cli")
def test_screenshot(mock_which, mock_run) -> None:  # type: ignore[no-untyped-def]
    """Screenshot saves to the given path."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="Screenshot saved\n", stderr=""
    )
    cli = PlaywrightCLI()
    result = cli.screenshot("/tmp/test.png")
    assert result.action == "screenshot"
    assert result.output == "/tmp/test.png"


@patch("browser_tool.service.subprocess.run")
@patch("browser_tool.service.shutil.which", return_value="/usr/local/bin/playwright-cli")
def test_type_text(mock_which, mock_run) -> None:  # type: ignore[no-untyped-def]
    """Type fills text into the given ref."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="Filled\n", stderr=""
    )
    cli = PlaywrightCLI()
    result = cli.type_text("s1e3", "hello world")
    assert result.action == "type"
    args = mock_run.call_args[0][0]
    assert "fill" in args
    assert "s1e3" in args
    assert "hello world" in args


@patch("browser_tool.service.subprocess.run")
@patch("browser_tool.service.shutil.which", return_value="/usr/local/bin/playwright-cli")
def test_press_key(mock_which, mock_run) -> None:  # type: ignore[no-untyped-def]
    """Press sends a key press command."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="Pressed Enter\n", stderr=""
    )
    cli = PlaywrightCLI()
    result = cli.press("Enter")
    assert result.action == "press"
    args = mock_run.call_args[0][0]
    assert "press" in args
    assert "Enter" in args


@patch("browser_tool.service.subprocess.run")
@patch("browser_tool.service.shutil.which", return_value="/usr/local/bin/playwright-cli")
def test_navigation_failure(mock_which, mock_run) -> None:  # type: ignore[no-untyped-def]
    """Non-zero exit from playwright-cli raises BrowserError."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="Navigation failed: timeout\n"
    )
    cli = PlaywrightCLI()
    with pytest.raises(BrowserError) as exc_info:
        cli.navigate("https://unreachable.invalid")
    assert exc_info.value.code == "NAVIGATION_FAILED"


@pytest.mark.external
def test_real_playwright_cli() -> None:
    """Integration test that invokes the real playwright-cli binary."""
    cli = PlaywrightCLI()
    result = cli.start()
    assert result.action == "start"
    assert result.session == "default"
    cli.stop()
