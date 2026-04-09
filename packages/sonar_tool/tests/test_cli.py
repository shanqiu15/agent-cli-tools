"""Tests for the sonar tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from cli_common.errors import ToolException
from sonar_tool.cli import app
from sonar_tool.models import Citation, SonarResponse

runner = CliRunner()


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "search" in result.output.lower()


@patch("sonar_tool.cli.search")
def test_successful_search(mock_search) -> None:  # type: ignore[no-untyped-def]
    """A successful search emits JSON with ok=true and structured result."""
    mock_search.return_value = SonarResponse(
        answer="Python is a programming language.",
        citations=[
            Citation(url="https://python.org", title="Python.org"),
            Citation(url="https://wiki.python.org", title="Python Wiki"),
        ],
        model="sonar",
    )

    result = runner.invoke(app, ["search", "--query", "what is python"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["answer"] == "Python is a programming language."
    assert len(data["result"]["citations"]) == 2
    assert data["result"]["citations"][0]["url"] == "https://python.org"
    assert data["result"]["citations"][0]["title"] == "Python.org"
    assert data["result"]["model"] == "sonar"


@patch(
    "sonar_tool.cli.search",
    side_effect=ToolException(
        code="MISSING_CREDENTIALS",
        message="Environment variable PERPLEXITY_API_KEY is not set",
        details={"env_var": "PERPLEXITY_API_KEY"},
    ),
)
def test_missing_api_key(mock_search) -> None:  # type: ignore[no-untyped-def]
    """Missing PERPLEXITY_API_KEY emits structured error."""
    result = runner.invoke(app, ["search", "--query", "test"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "MISSING_CREDENTIALS"


def test_invalid_model() -> None:
    """Invalid model emits INVALID_INPUT error."""
    result = runner.invoke(
        app, ["search", "--query", "test", "--model", "invalid-model"]
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_INPUT"
    assert "invalid-model" in data["error"]["message"]


def test_valid_model_choices() -> None:
    """All valid model choices are accepted without INVALID_INPUT."""
    valid_models = ["sonar", "sonar-pro", "sonar-reasoning-pro", "sonar-deep-research"]
    for model in valid_models:
        with patch("sonar_tool.cli.search") as mock_search:
            mock_search.return_value = SonarResponse(
                answer="test", citations=[], model=model
            )
            result = runner.invoke(
                app, ["search", "--query", "test", "--model", model]
            )
            assert result.exit_code == 0, f"Model {model} should be accepted"
