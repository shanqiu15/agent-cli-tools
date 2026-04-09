"""Tests for the file tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from file_tool.cli import app
from file_tool.errors import FileError
from file_tool.models import (
    FileEntry,
    ListResult,
    PatchResult,
    ReadResult,
    SearchMatch,
    SearchResult,
    TreeEntry,
    TreeResult,
    WriteResult,
)

runner = CliRunner()


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    output = result.output.lower()
    assert "read" in output
    assert "write" in output
    assert "patch" in output
    assert "search" in output
    assert "list" in output
    assert "tree" in output


@patch("file_tool.cli.read_file")
def test_read_success(mock_read) -> None:  # type: ignore[no-untyped-def]
    """A successful read emits JSON with ok=true."""
    mock_read.return_value = ReadResult(
        path="/tmp/test.txt",
        content="hello\n",
        lines=1,
        truncated=False,
        char_count=6,
    )

    result = runner.invoke(app, ["read", "--file", "/tmp/test.txt"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["content"] == "hello\n"
    assert data["result"]["truncated"] is False


@patch(
    "file_tool.cli.read_file",
    side_effect=FileError(
        code="BLOCKED_PATH",
        message="Access to /dev/zero is blocked",
        details={"path": "/dev/zero"},
    ),
)
def test_read_blocked_path_error(mock_read) -> None:  # type: ignore[no-untyped-def]
    """Reading a blocked path emits structured error."""
    result = runner.invoke(app, ["read", "--file", "/dev/zero"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "BLOCKED_PATH"


@patch("file_tool.cli.write_file")
def test_write_success(mock_write) -> None:  # type: ignore[no-untyped-def]
    """A successful write emits JSON with ok=true."""
    mock_write.return_value = WriteResult(
        path="/tmp/out.txt",
        bytes_written=5,
    )

    result = runner.invoke(app, ["write", "--file", "/tmp/out.txt", "--content", "hello"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["bytes_written"] == 5


@patch(
    "file_tool.cli.write_file",
    side_effect=FileError(
        code="PERMISSION_DENIED",
        message="Write to sensitive path is blocked",
        details={"path": "/etc/shadow"},
    ),
)
def test_write_sensitive_path_error(mock_write) -> None:  # type: ignore[no-untyped-def]
    """Writing to a sensitive path emits PERMISSION_DENIED error."""
    result = runner.invoke(app, ["write", "--file", "/etc/shadow", "--content", "x"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "PERMISSION_DENIED"


@patch("file_tool.cli.patch_file")
def test_patch_success(mock_patch) -> None:  # type: ignore[no-untyped-def]
    """A successful patch emits JSON with ok=true."""
    mock_patch.return_value = PatchResult(
        path="/tmp/f.txt",
        replacements=1,
    )

    result = runner.invoke(
        app, ["patch", "--file", "/tmp/f.txt", "--old", "foo", "--new", "bar"]
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["replacements"] == 1


@patch(
    "file_tool.cli.patch_file",
    side_effect=FileError(
        code="NOT_UNIQUE",
        message="old_string found 3 times",
        details={"count": 3},
    ),
)
def test_patch_not_unique_error(mock_patch) -> None:  # type: ignore[no-untyped-def]
    """Patching a non-unique string emits NOT_UNIQUE error."""
    result = runner.invoke(
        app, ["patch", "--file", "/tmp/f.txt", "--old", "x", "--new", "y"]
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "NOT_UNIQUE"


@patch("file_tool.cli.search_files")
def test_search_success(mock_search) -> None:  # type: ignore[no-untyped-def]
    """A successful search emits JSON with matches."""
    mock_search.return_value = SearchResult(
        pattern="def \\w+",
        matches=[
            SearchMatch(file="a.py", line=1, content="def foo():"),
        ],
        total=1,
        truncated=False,
    )

    result = runner.invoke(app, ["search", "--pattern", "def \\w+"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert len(data["result"]["matches"]) == 1


@patch("file_tool.cli.list_directory")
def test_list_success(mock_list) -> None:  # type: ignore[no-untyped-def]
    """A successful list emits JSON with entries."""
    mock_list.return_value = ListResult(
        path="/tmp",
        entries=[
            FileEntry(name="a.txt", path="a.txt", is_dir=False, size=10),
        ],
        total=1,
    )

    result = runner.invoke(app, ["list", "--path", "/tmp"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["total"] == 1


@patch("file_tool.cli.tree_directory")
def test_tree_success(mock_tree) -> None:  # type: ignore[no-untyped-def]
    """A successful tree emits JSON with entries."""
    mock_tree.return_value = TreeResult(
        path="/tmp",
        entries=[
            TreeEntry(path="a.txt", is_dir=False),
            TreeEntry(path="sub", is_dir=True),
        ],
        total=2,
    )

    result = runner.invoke(app, ["tree", "--path", "/tmp"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["total"] == 2
