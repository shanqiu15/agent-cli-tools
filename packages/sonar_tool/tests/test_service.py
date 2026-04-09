"""Tests for the sonar tool service layer."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from cli_common.errors import ToolException
from sonar_tool.service import search


def test_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing PERPLEXITY_API_KEY raises MISSING_CREDENTIALS."""
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    with pytest.raises(ToolException) as exc_info:
        search("test query")
    assert exc_info.value.code == "MISSING_CREDENTIALS"
    assert exc_info.value.details["env_var"] == "PERPLEXITY_API_KEY"


@patch("cli_common.http.httpx.request")
def test_successful_search(mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful API call returns parsed SonarResponse."""
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Python is a versatile programming language."
                }
            }
        ],
        "citations": [
            "https://python.org",
            "https://docs.python.org",
        ],
    }
    mock_request.return_value = mock_response

    result = search("what is python", model="sonar-pro")

    assert result.answer == "Python is a versatile programming language."
    assert len(result.citations) == 2
    assert result.citations[0].url == "https://python.org"
    assert result.citations[1].url == "https://docs.python.org"
    assert result.model == "sonar-pro"

    call_kwargs = mock_request.call_args
    assert call_kwargs.kwargs["json"]["model"] == "sonar-pro"
    assert call_kwargs.kwargs["json"]["messages"][0]["content"] == "what is python"
    assert "Bearer test-key" in call_kwargs.kwargs["headers"]["Authorization"]


@pytest.mark.external
def test_real_perplexity_api() -> None:
    """Integration test that hits the real Perplexity API.

    Requires PERPLEXITY_API_KEY to be set. Skipped by default.
    """
    result = search("what is the capital of France", model="sonar")
    assert result.answer
    assert result.model == "sonar"
