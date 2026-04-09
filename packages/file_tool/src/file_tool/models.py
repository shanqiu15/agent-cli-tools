"""Pydantic models for file tool."""

from pydantic import BaseModel, Field


class ReadResult(BaseModel):
    """Result of reading a file."""

    path: str = Field(description="Absolute path of the file that was read")
    content: str = Field(description="File content (possibly truncated)")
    lines: int = Field(description="Total number of lines in the returned content")
    truncated: bool = Field(description="Whether the content was truncated")
    char_count: int = Field(description="Character count of the returned content")


class WriteResult(BaseModel):
    """Result of writing a file."""

    path: str = Field(description="Absolute path of the file that was written")
    bytes_written: int = Field(description="Number of bytes written")


class PatchResult(BaseModel):
    """Result of patching a file."""

    path: str = Field(description="Absolute path of the file that was patched")
    replacements: int = Field(description="Number of replacements made")


class SearchMatch(BaseModel):
    """A single search match."""

    file: str = Field(description="Path of the file containing the match")
    line: int = Field(description="1-indexed line number of the match")
    content: str = Field(description="Content of the matching line")


class SearchResult(BaseModel):
    """Result of a regex search across files."""

    pattern: str = Field(description="The regex pattern that was searched")
    matches: list[SearchMatch] = Field(description="List of matches found")
    total: int = Field(description="Total number of matches before offset/limit")
    truncated: bool = Field(description="Whether results were truncated by limit")


class FileEntry(BaseModel):
    """A single file or directory entry."""

    name: str = Field(description="Name of the file or directory")
    path: str = Field(description="Relative path from the listed directory")
    is_dir: bool = Field(description="True if this entry is a directory")
    size: int = Field(description="File size in bytes (0 for directories)")


class ListResult(BaseModel):
    """Result of listing a directory."""

    path: str = Field(description="Absolute path of the listed directory")
    entries: list[FileEntry] = Field(description="Sorted list of directory entries")
    total: int = Field(description="Total number of entries")


class TreeEntry(BaseModel):
    """A single entry in a directory tree."""

    path: str = Field(description="Relative path from the tree root")
    is_dir: bool = Field(description="True if this entry is a directory")


class TreeResult(BaseModel):
    """Result of a directory tree listing."""

    path: str = Field(description="Absolute path of the tree root")
    entries: list[TreeEntry] = Field(description="Flat list of all entries in the tree")
    total: int = Field(description="Total number of entries")
