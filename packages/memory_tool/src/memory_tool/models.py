"""Pydantic models for memory tool."""

from pydantic import BaseModel, Field


class WriteResult(BaseModel):
    """Result of a memory write operation."""

    path: str = Field(description="Relative path of the written file")
    bytes_written: int = Field(description="Number of bytes written")
    appended: bool = Field(description="Whether content was appended")


class ReadResult(BaseModel):
    """Result of a memory read operation."""

    path: str = Field(description="Relative path of the file")
    content: str = Field(description="File content")
    size: int = Field(description="File size in bytes")


class SearchMatch(BaseModel):
    """A single search match."""

    path: str = Field(description="Relative path of the matching file")
    size: int = Field(description="File size in bytes")
    modified: float = Field(description="Last modification timestamp")


class SearchResult(BaseModel):
    """Result of a memory search operation."""

    query: str = Field(description="The search query")
    matches: list[SearchMatch] = Field(description="Matching files")
    total: int = Field(description="Total number of matches")
