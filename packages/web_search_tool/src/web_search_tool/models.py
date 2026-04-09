"""Pydantic models for web search tool."""

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A single search result."""

    title: str = Field(description="Title of the search result")
    url: str = Field(description="URL of the search result")
    snippet: str = Field(description="Text snippet from the search result")


class SearchResponse(BaseModel):
    """Response containing a list of search results."""

    query: str = Field(description="The original search query")
    results: list[SearchResult] = Field(description="List of search results")
