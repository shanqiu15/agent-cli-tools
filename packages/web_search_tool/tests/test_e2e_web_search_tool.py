"""End-to-end tests for web_search_tool."""

import json

import pytest
from typer.testing import CliRunner

from web_search_tool.cli import app

runner = CliRunner()


class TestWebSearchValidation:
    def test_num_results_below_range(self) -> None:
        result = runner.invoke(app, ["search", "--query", "test", "--num-results", "0"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "INVALID_INPUT"

    def test_num_results_above_range(self) -> None:
        result = runner.invoke(app, ["search", "--query", "test", "--num-results", "11"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "INVALID_INPUT"

    def test_missing_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SERPER_API_KEY", raising=False)
        result = runner.invoke(app, ["search", "--query", "test"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "MISSING_CREDENTIALS"


@pytest.mark.external
class TestWebSearchE2E:
    def test_search_returns_results(self) -> None:
        result = runner.invoke(app, ["search", "--query", "Python programming", "--num-results", "3"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert len(data["result"]["results"]) > 0
        first = data["result"]["results"][0]
        assert "title" in first
        assert "url" in first
