"""Shared HTTP client helper for API-calling CLI tools."""

import os
import ssl
from typing import Any

import httpx

from cli_common.errors import ToolException


def api_request(
    method: str,
    url: str,
    *,
    api_key_env: str | None = None,
    headers: dict[str, str] | None = None,
    json: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> httpx.Response:
    """Make an HTTP API request with standard error handling.

    Args:
        method: HTTP method (GET, POST, etc.).
        url: Request URL.
        api_key_env: Environment variable name containing the API key.
            If set, the key is read from the environment and added as
            an ``Authorization: Bearer <key>`` header. Raises
            ``ToolException`` with code ``MISSING_CREDENTIALS`` if the
            variable is not set.
        headers: Additional request headers.
        json: JSON body payload.
        params: Query parameters.
        timeout: Request timeout in seconds.

    Returns:
        The ``httpx.Response`` on success.

    Raises:
        ToolException: On missing credentials, timeout, or HTTP error.
    """
    merged_headers: dict[str, str] = dict(headers) if headers else {}

    if api_key_env is not None:
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ToolException(
                code="MISSING_CREDENTIALS",
                message=f"Environment variable {api_key_env} is not set",
                details={"env_var": api_key_env},
            )
        merged_headers.setdefault("Authorization", f"Bearer {api_key}")

    try:
        response = httpx.request(
            method,
            url,
            headers=merged_headers,
            json=json,
            params=params,
            timeout=timeout,
            verify=ssl.create_default_context(),
        )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise ToolException(
            code="TIMEOUT",
            message=f"Request to {url} timed out after {timeout}s",
            details={"url": url, "timeout": timeout},
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise ToolException(
            code="HTTP_ERROR",
            message=f"HTTP {exc.response.status_code} from {url}",
            details={
                "url": url,
                "status_code": exc.response.status_code,
                "body": exc.response.text[:500],
            },
        ) from exc

    return response
