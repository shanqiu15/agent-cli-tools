"""Business logic for AI-powered search via the Perplexity Sonar API."""

import os

from cli_common.errors import ToolException
from cli_common.http import api_request

from sonar_tool.models import Citation, SonarResponse

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_API_KEY_ENV = "PERPLEXITY_API_KEY"

VALID_MODELS = ("sonar", "sonar-pro", "sonar-reasoning-pro", "sonar-deep-research")


def search(query: str, model: str = "sonar") -> SonarResponse:
    """Query the Perplexity Sonar API for AI-powered search with citations.

    Args:
        query: The search query string.
        model: Sonar model to use.

    Returns:
        SonarResponse with answer text, citations, and model used.

    Raises:
        ToolException: On missing credentials or API errors.
    """
    api_key = os.environ.get(PERPLEXITY_API_KEY_ENV)
    if not api_key:
        raise ToolException(
            code="MISSING_CREDENTIALS",
            message=f"Environment variable {PERPLEXITY_API_KEY_ENV} is not set",
            details={"env_var": PERPLEXITY_API_KEY_ENV},
        )

    response = api_request(
        "POST",
        PERPLEXITY_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": query}],
        },
    )

    data = response.json()

    answer = data["choices"][0]["message"]["content"]

    raw_citations = data.get("citations", [])
    citations = [
        Citation(
            url=c if isinstance(c, str) else c.get("url", ""),
            title=c if isinstance(c, str) else c.get("title", ""),
        )
        for c in raw_citations
    ]

    return SonarResponse(answer=answer, citations=citations, model=model)
