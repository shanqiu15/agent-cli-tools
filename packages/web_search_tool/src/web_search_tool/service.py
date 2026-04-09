"""Business logic for web search via Serper API."""

import os

from cli_common.errors import ToolException
from cli_common.http import api_request

from web_search_tool.models import SearchResponse, SearchResult

SERPER_API_URL = "https://google.serper.dev/search"
SERPER_API_KEY_ENV = "SERPER_API_KEY"


def search(query: str, num_results: int = 5) -> SearchResponse:
    """Perform a Google search via the Serper API.

    Args:
        query: The search query string.
        num_results: Number of results to return (1-10).

    Returns:
        SearchResponse with the query and list of results.

    Raises:
        ToolException: On missing credentials or API errors.
    """
    api_key = os.environ.get(SERPER_API_KEY_ENV)
    if not api_key:
        raise ToolException(
            code="MISSING_CREDENTIALS",
            message=f"Environment variable {SERPER_API_KEY_ENV} is not set",
            details={"env_var": SERPER_API_KEY_ENV},
        )

    response = api_request(
        "POST",
        SERPER_API_URL,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        json={"q": query, "num": num_results},
    )

    data = response.json()
    organic = data.get("organic", [])

    results = [
        SearchResult(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
        )
        for item in organic[:num_results]
    ]

    return SearchResponse(query=query, results=results)
