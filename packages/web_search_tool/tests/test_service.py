"""Tests for the web search tool service layer."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from cli_common.errors import ToolException
from web_search_tool.service import search


def test_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing SERPER_API_KEY raises MISSING_CREDENTIALS."""
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    with pytest.raises(ToolException) as exc_info:
        search("test query")
    assert exc_info.value.code == "MISSING_CREDENTIALS"
    assert exc_info.value.details["env_var"] == "SERPER_API_KEY"


@patch("cli_common.http.httpx.request")
def test_successful_search(mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful API call returns parsed SearchResponse."""
    monkeypatch.setenv("SERPER_API_KEY", "test-key")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "organic": [
            {
                "title": "Result 1",
                "link": "https://example.com/1",
                "snippet": "First result snippet",
            },
            {
                "title": "Result 2",
                "link": "https://example.com/2",
                "snippet": "Second result snippet",
            },
        ]
    }
    mock_request.return_value = mock_response

    result = search("test query", num_results=2)

    assert result.query == "test query"
    assert len(result.results) == 2
    assert result.results[0].title == "Result 1"
    assert result.results[0].url == "https://example.com/1"
    assert result.results[1].snippet == "Second result snippet"

    # Verify API was called with correct params
    call_kwargs = mock_request.call_args
    assert call_kwargs.kwargs["json"] == {"q": "test query", "num": 2}
    headers = call_kwargs.kwargs["headers"]
    assert headers["X-API-KEY"] == "test-key"


@pytest.mark.external
def test_real_serper_api() -> None:
    """Integration test that hits the real Serper API.

    Requires SERPER_API_KEY to be set. Skipped by default.
    """
    result = search("python programming language", num_results=3)
    assert result.query == "python programming language"
    assert len(result.results) > 0
    assert result.results[0].title
    assert result.results[0].url
