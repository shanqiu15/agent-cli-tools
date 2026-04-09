"""Tests for the memory tool service layer."""

import pytest

from memory_tool.errors import MemoryError
from memory_tool.service import read_memory, search_memory, write_memory


def test_write_and_read(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Write then read returns the same content."""
    write_memory(tmp_path, "note.md", "test content")
    result = read_memory(tmp_path, "note.md")
    assert result.content == "test content"
    assert result.path == "note.md"


def test_append_mode(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Append adds to existing content."""
    write_memory(tmp_path, "note.md", "first")
    result = write_memory(tmp_path, "note.md", " second", append=True)
    assert result.appended is True

    read_result = read_memory(tmp_path, "note.md")
    assert read_result.content == "first second"


def test_directory_traversal_rejected(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Paths escaping memory dir raise INVALID_PATH."""
    with pytest.raises(MemoryError, match="within the memory directory"):
        write_memory(tmp_path, "../../etc/passwd", "bad")


def test_absolute_path_rejected(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Absolute paths raise INVALID_PATH."""
    with pytest.raises(MemoryError, match="Absolute paths"):
        write_memory(tmp_path, "/etc/passwd", "bad")


def test_read_missing_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Reading nonexistent file raises FILE_NOT_FOUND."""
    with pytest.raises(MemoryError, match="File not found"):
        read_memory(tmp_path, "missing.md")


def test_search_matches(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Search finds .md files with matching content."""
    write_memory(tmp_path, "a.md", "hello world")
    write_memory(tmp_path, "b.md", "goodbye")
    write_memory(tmp_path, "c.txt", "hello txt")

    result = search_memory(tmp_path, "hello")
    assert result.total == 1
    assert result.matches[0].path == "a.md"


def test_search_empty_dir(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Search on empty directory returns no matches."""
    result = search_memory(tmp_path, "anything")
    assert result.total == 0
    assert result.matches == []


def test_creates_parent_dirs(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Write creates parent directories as needed."""
    write_memory(tmp_path, "sub/dir/note.md", "nested")
    result = read_memory(tmp_path, "sub/dir/note.md")
    assert result.content == "nested"
