"""Tests for cli_common.http — api_request helper."""

from unittest.mock import patch

import httpx
import pytest

from cli_common.errors import ToolException
from cli_common.http import api_request


def test_missing_env_var_raises_missing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TEST_API_KEY", raising=False)
    with pytest.raises(ToolException) as exc_info:
        api_request("GET", "https://example.com/api", api_key_env="TEST_API_KEY")
    assert exc_info.value.code == "MISSING_CREDENTIALS"
    assert "TEST_API_KEY" in str(exc_info.value)
    assert exc_info.value.details["env_var"] == "TEST_API_KEY"


def test_timeout_raises_tool_exception() -> None:
    with patch("cli_common.http.httpx.request", side_effect=httpx.ReadTimeout("timed out")):
        with pytest.raises(ToolException) as exc_info:
            api_request("GET", "https://example.com/api")
        assert exc_info.value.code == "TIMEOUT"
        assert "timed out" in exc_info.value.details["url"] or exc_info.value.details["url"] == "https://example.com/api"


def test_http_status_error_raises_tool_exception() -> None:
    mock_response = httpx.Response(
        status_code=403,
        request=httpx.Request("GET", "https://example.com/api"),
        text="Forbidden",
    )
    with patch(
        "cli_common.http.httpx.request",
        side_effect=httpx.HTTPStatusError("forbidden", request=mock_response.request, response=mock_response),
    ):
        with pytest.raises(ToolException) as exc_info:
            api_request("GET", "https://example.com/api")
        assert exc_info.value.code == "HTTP_ERROR"
        assert exc_info.value.details["status_code"] == 403


def test_success_returns_response() -> None:
    mock_response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "https://example.com/api"),
        json={"data": "ok"},
    )
    with patch("cli_common.http.httpx.request", return_value=mock_response):
        response = api_request("GET", "https://example.com/api")
    assert response.status_code == 200
    assert response.json() == {"data": "ok"}


def test_api_key_env_sets_authorization_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_KEY", "secret-123")
    mock_response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "https://example.com/api"),
        json={},
    )
    with patch("cli_common.http.httpx.request", return_value=mock_response) as mock_req:
        api_request("GET", "https://example.com/api", api_key_env="MY_KEY")
    call_kwargs = mock_req.call_args
    assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer secret-123"


def test_no_api_key_env_skips_auth_header() -> None:
    mock_response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "https://example.com/api"),
        json={},
    )
    with patch("cli_common.http.httpx.request", return_value=mock_response) as mock_req:
        api_request("GET", "https://example.com/api")
    call_kwargs = mock_req.call_args
    assert "Authorization" not in call_kwargs.kwargs["headers"]
