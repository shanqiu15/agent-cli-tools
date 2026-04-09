"""Tests for the memory tool CLI."""

import json

from typer.testing import CliRunner

from memory_tool.cli import app

runner = CliRunner()


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "write" in result.output.lower()
    assert "read" in result.output.lower()
    assert "search" in result.output.lower()


def test_write_and_read_roundtrip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Write a file then read it back — content should match."""
    mem_dir = str(tmp_path)
    result = runner.invoke(
        app,
        ["write", "--path", "test.md", "--content", "hello world", "--memory-dir", mem_dir],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["path"] == "test.md"
    assert data["result"]["appended"] is False

    result = runner.invoke(
        app,
        ["read", "--path", "test.md", "--memory-dir", mem_dir],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["content"] == "hello world"


def test_write_append_mode(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Append mode adds content to existing file."""
    mem_dir = str(tmp_path)
    runner.invoke(
        app,
        ["write", "--path", "test.md", "--content", "first", "--memory-dir", mem_dir],
    )
    result = runner.invoke(
        app,
        ["write", "--path", "test.md", "--content", " second", "--append", "--memory-dir", mem_dir],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["appended"] is True

    result = runner.invoke(
        app,
        ["read", "--path", "test.md", "--memory-dir", mem_dir],
    )
    data = json.loads(result.output)
    assert data["result"]["content"] == "first second"


def test_read_missing_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Reading a nonexistent file returns FILE_NOT_FOUND error."""
    mem_dir = str(tmp_path)
    result = runner.invoke(
        app,
        ["read", "--path", "nope.md", "--memory-dir", mem_dir],
    )
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "FILE_NOT_FOUND"


def test_write_directory_traversal_rejected(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Paths with ../ that escape memory dir are rejected."""
    mem_dir = str(tmp_path)
    result = runner.invoke(
        app,
        ["write", "--path", "../escape.md", "--content", "bad", "--memory-dir", mem_dir],
    )
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_PATH"


def test_write_absolute_path_rejected(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Absolute paths are rejected."""
    mem_dir = str(tmp_path)
    result = runner.invoke(
        app,
        ["write", "--path", "/etc/passwd", "--content", "bad", "--memory-dir", mem_dir],
    )
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_PATH"


def test_search_matching(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Search returns files whose content matches the query."""
    mem_dir = str(tmp_path)
    runner.invoke(
        app,
        ["write", "--path", "a.md", "--content", "hello world", "--memory-dir", mem_dir],
    )
    runner.invoke(
        app,
        ["write", "--path", "b.md", "--content", "goodbye", "--memory-dir", mem_dir],
    )
    runner.invoke(
        app,
        ["write", "--path", "c.txt", "--content", "hello txt", "--memory-dir", mem_dir],
    )

    result = runner.invoke(
        app,
        ["search", "--query", "hello", "--memory-dir", mem_dir],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["total"] == 1  # only .md files
    assert data["result"]["matches"][0]["path"] == "a.md"


def test_write_creates_parent_dirs(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Write creates parent directories as needed."""
    mem_dir = str(tmp_path)
    result = runner.invoke(
        app,
        ["write", "--path", "sub/dir/test.md", "--content", "nested", "--memory-dir", mem_dir],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True

    result = runner.invoke(
        app,
        ["read", "--path", "sub/dir/test.md", "--memory-dir", mem_dir],
    )
    data = json.loads(result.output)
    assert data["result"]["content"] == "nested"
