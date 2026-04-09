"""Tests for the web crawl tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from cli_common.errors import ToolException
from web_crawl_tool.cli import app
from web_crawl_tool.models import CrawlResult

runner = CliRunner()


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "crawl" in result.output.lower()


@patch("web_crawl_tool.cli.crawl")
def test_successful_crawl(mock_crawl) -> None:  # type: ignore[no-untyped-def]
    """A successful crawl emits JSON with ok=true and result."""
    mock_crawl.return_value = CrawlResult(
        url="https://example.com",
        content="Hello world content",
        content_length=19,
        truncated=False,
    )

    result = runner.invoke(app, ["crawl", "--url", "https://example.com"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["url"] == "https://example.com"
    assert data["result"]["content"] == "Hello world content"
    assert data["result"]["content_length"] == 19
    assert data["result"]["truncated"] is False


@patch(
    "web_crawl_tool.cli.crawl",
    side_effect=ToolException(
        code="INVALID_URL",
        message="URL must start with http:// or https://",
        details={"url": "not-a-url"},
    ),
)
def test_invalid_url(mock_crawl) -> None:  # type: ignore[no-untyped-def]
    """Invalid URL emits structured error."""
    result = runner.invoke(app, ["crawl", "--url", "not-a-url"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_URL"


@patch(
    "web_crawl_tool.cli.crawl",
    side_effect=ToolException(
        code="TIMEOUT",
        message="Request timed out",
        details={"url": "https://slow.example.com", "timeout": 60},
    ),
)
def test_timeout_error(mock_crawl) -> None:  # type: ignore[no-untyped-def]
    """Timeout emits structured error."""
    result = runner.invoke(app, ["crawl", "--url", "https://slow.example.com"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "TIMEOUT"
