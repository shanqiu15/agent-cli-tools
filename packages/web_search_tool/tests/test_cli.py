"""Tests for the web search tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from cli_common.errors import ToolException
from web_search_tool.cli import app
from web_search_tool.models import SearchResponse, SearchResult

runner = CliRunner()


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "search" in result.output.lower()


@patch("web_search_tool.cli.search")
def test_successful_search(mock_search) -> None:  # type: ignore[no-untyped-def]
    """A successful search emits JSON with ok=true and result list."""
    mock_search.return_value = SearchResponse(
        query="python typer",
        results=[
            SearchResult(
                title="Typer",
                url="https://typer.tiangolo.com",
                snippet="Typer is a library for building CLI applications.",
            ),
            SearchResult(
                title="Typer GitHub",
                url="https://github.com/tiangolo/typer",
                snippet="Build great CLIs.",
            ),
        ],
    )

    result = runner.invoke(app, ["search", "--query", "python typer"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["query"] == "python typer"
    assert len(data["result"]["results"]) == 2
    assert data["result"]["results"][0]["title"] == "Typer"
    assert data["result"]["results"][0]["url"] == "https://typer.tiangolo.com"
    assert "library" in data["result"]["results"][0]["snippet"]


@patch(
    "web_search_tool.cli.search",
    side_effect=ToolException(
        code="MISSING_CREDENTIALS",
        message="Environment variable SERPER_API_KEY is not set",
        details={"env_var": "SERPER_API_KEY"},
    ),
)
def test_missing_api_key(mock_search) -> None:  # type: ignore[no-untyped-def]
    """Missing SERPER_API_KEY emits structured error with MISSING_CREDENTIALS."""
    result = runner.invoke(app, ["search", "--query", "test"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "MISSING_CREDENTIALS"


def test_invalid_num_results_too_high() -> None:
    """num-results > 10 emits INVALID_INPUT error."""
    result = runner.invoke(
        app, ["search", "--query", "test", "--num-results", "20"]
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_INPUT"


def test_invalid_num_results_too_low() -> None:
    """num-results < 1 emits INVALID_INPUT error."""
    result = runner.invoke(
        app, ["search", "--query", "test", "--num-results", "0"]
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_INPUT"
