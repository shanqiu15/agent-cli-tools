"""Pydantic models for web crawl tool."""

from pydantic import BaseModel, Field


class CrawlResult(BaseModel):
    """Result of crawling a web page."""

    url: str = Field(description="The URL that was crawled")
    content: str = Field(description="Extracted text/markdown content")
    content_length: int = Field(description="Length of the extracted content")
    truncated: bool = Field(
        default=False,
        description="Whether the content was truncated to max_length",
    )
