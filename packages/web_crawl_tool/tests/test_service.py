"""Tests for the web crawl tool service layer."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from cli_common.errors import ToolException
from web_crawl_tool.service import crawl


def test_invalid_url() -> None:
    """Non-HTTP URL raises INVALID_URL."""
    with pytest.raises(ToolException) as exc_info:
        crawl("ftp://example.com")
    assert exc_info.value.code == "INVALID_URL"


@patch("web_crawl_tool.service.api_request")
def test_crawl4ai_success(
    mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When CRAWL4AI_BASE_URL is set, uses crawl4ai service."""
    monkeypatch.setenv("CRAWL4AI_BASE_URL", "http://crawl4ai:8000")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"markdown": "# Hello World\n\nSome content."}
    mock_request.return_value = mock_response

    result = crawl("https://example.com")

    assert result.url == "https://example.com"
    assert result.content == "# Hello World\n\nSome content."
    assert result.truncated is False

    # Verify crawl4ai endpoint was called
    mock_request.assert_called_once_with(
        "POST",
        "http://crawl4ai:8000/crawl",
        json={"url": "https://example.com"},
        timeout=60.0,
    )


@patch("web_crawl_tool.service._crawl_direct")
def test_fallback_to_direct(
    mock_direct: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When CRAWL4AI_BASE_URL is not set, falls back to direct fetch."""
    monkeypatch.delenv("CRAWL4AI_BASE_URL", raising=False)
    mock_direct.return_value = "Direct content from page"

    result = crawl("https://example.com")

    assert result.url == "https://example.com"
    assert result.content == "Direct content from page"
    mock_direct.assert_called_once_with("https://example.com", 60.0)


@patch("web_crawl_tool.service._crawl_direct")
@patch("web_crawl_tool.service._crawl_via_crawl4ai")
def test_crawl4ai_fails_falls_back(
    mock_crawl4ai: MagicMock,
    mock_direct: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When crawl4ai fails, falls back to direct fetch."""
    monkeypatch.setenv("CRAWL4AI_BASE_URL", "http://crawl4ai:8000")
    mock_crawl4ai.side_effect = ToolException(
        code="HTTP_ERROR", message="Service unavailable"
    )
    mock_direct.return_value = "Fallback content"

    result = crawl("https://example.com")

    assert result.content == "Fallback content"
    mock_direct.assert_called_once()


@patch("web_crawl_tool.service._crawl_direct")
def test_truncation(
    mock_direct: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Content exceeding max_length is truncated with indicator."""
    monkeypatch.delenv("CRAWL4AI_BASE_URL", raising=False)
    mock_direct.return_value = "A" * 500

    result = crawl("https://example.com", max_length=100)

    assert result.truncated is True
    assert result.content.endswith("[Content truncated]")
    assert len(result.content) == 100 + len("\n\n[Content truncated]")


@patch("web_crawl_tool.service.api_request")
def test_timeout_handling(
    mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Timeout from direct fetch raises ToolException."""
    monkeypatch.delenv("CRAWL4AI_BASE_URL", raising=False)
    mock_request.side_effect = ToolException(
        code="TIMEOUT",
        message="Request timed out",
        details={"url": "https://slow.example.com", "timeout": 60},
    )

    with pytest.raises(ToolException) as exc_info:
        crawl("https://slow.example.com")
    assert exc_info.value.code == "TIMEOUT"
