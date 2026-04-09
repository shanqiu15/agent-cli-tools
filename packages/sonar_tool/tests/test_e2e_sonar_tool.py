"""End-to-end tests for sonar_tool."""

import json

import pytest
from typer.testing import CliRunner

from sonar_tool.cli import app

runner = CliRunner()


class TestSonarValidation:
    def test_invalid_model_rejected(self) -> None:
        result = runner.invoke(app, ["search", "--query", "test", "--model", "gpt-4"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "INVALID_INPUT"

    def test_missing_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        result = runner.invoke(app, ["search", "--query", "test"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "MISSING_CREDENTIALS"


@pytest.mark.external
class TestSonarE2E:
    def test_search_returns_answer(self) -> None:
        result = runner.invoke(app, ["search", "--query", "What is Python?"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert len(data["result"]["answer"]) > 0
        assert data["result"]["model"] == "sonar"
