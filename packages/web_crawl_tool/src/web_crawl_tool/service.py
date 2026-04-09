"""Business logic for web crawling and content extraction."""

import os
import re

from cli_common.errors import ToolException
from cli_common.http import api_request

from web_crawl_tool.models import CrawlResult

CRAWL4AI_BASE_URL_ENV = "CRAWL4AI_BASE_URL"


def _strip_html_tags(html: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _crawl_via_crawl4ai(url: str, timeout: float) -> str | None:
    """Attempt to crawl via crawl4ai service. Returns content or None."""
    base_url = os.environ.get(CRAWL4AI_BASE_URL_ENV)
    if not base_url:
        return None

    base_url = base_url.rstrip("/")
    response = api_request(
        "POST",
        f"{base_url}/crawl",
        json={"url": url},
        timeout=timeout,
    )
    data = response.json()
    return data.get("markdown") or data.get("content") or data.get("text")


def _crawl_direct(url: str, timeout: float) -> str:
    """Fetch URL directly and extract readable content with readability-lxml."""
    from readability import Document  # type: ignore[import-untyped]

    response = api_request("GET", url, timeout=timeout)
    html = response.text
    doc = Document(html)
    summary_html = doc.summary()
    return _strip_html_tags(summary_html)


def crawl(url: str, timeout: float = 60.0, max_length: int = 20000) -> CrawlResult:
    """Crawl a URL and extract readable content.

    Tries crawl4ai service first (if CRAWL4AI_BASE_URL is set),
    then falls back to direct fetch + readability extraction.

    Args:
        url: The URL to crawl.
        timeout: Request timeout in seconds.
        max_length: Maximum content length before truncation.

    Returns:
        CrawlResult with extracted content.

    Raises:
        ToolException: On network errors or extraction failures.
    """
    if not url.startswith(("http://", "https://")):
        raise ToolException(
            code="INVALID_URL",
            message=f"URL must start with http:// or https://, got: {url}",
            details={"url": url},
        )

    content: str | None = None

    # Try crawl4ai first
    try:
        content = _crawl_via_crawl4ai(url, timeout)
    except ToolException:
        pass

    # Fall back to direct fetch
    if not content:
        content = _crawl_direct(url, timeout)

    if not content:
        raise ToolException(
            code="EXTRACTION_FAILED",
            message=f"Could not extract content from {url}",
            details={"url": url},
        )

    truncated = len(content) > max_length
    if truncated:
        content = content[:max_length] + "\n\n[Content truncated]"

    return CrawlResult(
        url=url,
        content=content,
        content_length=len(content),
        truncated=truncated,
    )
