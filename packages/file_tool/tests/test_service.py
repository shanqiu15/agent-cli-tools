"""Tests for the file tool service layer."""

import os

import pytest

from file_tool.errors import FileError
from file_tool.service import (
    list_directory,
    patch_file,
    read_file,
    search_files,
    tree_directory,
    write_file,
)


# --- read_file ---


def test_read_file_success(tmp_path: object) -> None:
    """Reading a valid text file returns its content."""
    p = tmp_path / "hello.txt"  # type: ignore[operator]
    p.write_text("line1\nline2\nline3\n")

    result = read_file(str(p))
    assert result.content == "line1\nline2\nline3\n"
    assert result.lines == 3
    assert result.truncated is False


def test_read_file_with_offset(tmp_path: object) -> None:
    """Reading with an offset skips initial lines."""
    p = tmp_path / "offset.txt"  # type: ignore[operator]
    p.write_text("line1\nline2\nline3\nline4\n")

    result = read_file(str(p), offset=2)
    assert result.content == "line2\nline3\nline4\n"


def test_read_file_with_limit(tmp_path: object) -> None:
    """Reading with a limit returns only that many lines."""
    p = tmp_path / "limit.txt"  # type: ignore[operator]
    p.write_text("line1\nline2\nline3\nline4\n")

    result = read_file(str(p), offset=1, limit=2)
    assert result.content == "line1\nline2\n"


def test_read_file_with_offset_and_limit(tmp_path: object) -> None:
    """Reading with both offset and limit returns the correct slice."""
    p = tmp_path / "slice.txt"  # type: ignore[operator]
    p.write_text("a\nb\nc\nd\ne\n")

    result = read_file(str(p), offset=2, limit=2)
    assert result.content == "b\nc\n"


def test_read_file_not_found() -> None:
    """Reading a nonexistent file raises FILE_NOT_FOUND."""
    with pytest.raises(FileError) as exc_info:
        read_file("/tmp/nonexistent_file_abc123.txt")
    assert exc_info.value.code == "FILE_NOT_FOUND"


def test_read_blocked_device_path() -> None:
    """Reading /dev/zero is blocked."""
    with pytest.raises(FileError) as exc_info:
        read_file("/dev/zero")
    assert exc_info.value.code == "BLOCKED_PATH"


def test_read_blocked_dev_urandom() -> None:
    """Reading /dev/urandom is blocked."""
    with pytest.raises(FileError) as exc_info:
        read_file("/dev/urandom")
    assert exc_info.value.code == "BLOCKED_PATH"


def test_read_blocked_dev_subpath() -> None:
    """Reading any path under /dev/ is blocked."""
    with pytest.raises(FileError) as exc_info:
        read_file("/dev/null")
    assert exc_info.value.code == "BLOCKED_PATH"


def test_read_binary_file_extension(tmp_path: object) -> None:
    """Reading a file with a binary extension is blocked."""
    p = tmp_path / "image.png"  # type: ignore[operator]
    p.write_bytes(b"\x89PNG\r\n")

    with pytest.raises(FileError) as exc_info:
        read_file(str(p))
    assert exc_info.value.code == "BINARY_FILE"


def test_read_binary_exe_extension(tmp_path: object) -> None:
    """Reading a .exe file is blocked."""
    p = tmp_path / "program.exe"  # type: ignore[operator]
    p.write_bytes(b"MZ")

    with pytest.raises(FileError) as exc_info:
        read_file(str(p))
    assert exc_info.value.code == "BINARY_FILE"


# --- write_file ---


def test_write_file_success(tmp_path: object) -> None:
    """Writing to a valid path creates the file with correct content."""
    p = tmp_path / "output.txt"  # type: ignore[operator]
    result = write_file(str(p), "hello world")
    assert result.bytes_written == len("hello world".encode("utf-8"))
    assert p.read_text() == "hello world"


def test_write_file_creates_parent_dirs(tmp_path: object) -> None:
    """Writing to a nested path creates parent directories."""
    p = tmp_path / "a" / "b" / "c.txt"  # type: ignore[operator]
    result = write_file(str(p), "nested")
    assert result.bytes_written > 0
    assert p.read_text() == "nested"


def test_write_sensitive_path_blocked() -> None:
    """Writing to ~/.ssh/id_rsa is blocked."""
    ssh_key = os.path.expanduser("~/.ssh/id_rsa")
    with pytest.raises(FileError) as exc_info:
        write_file(ssh_key, "bad content")
    assert exc_info.value.code == "PERMISSION_DENIED"


def test_write_etc_shadow_blocked() -> None:
    """Writing to /etc/shadow is blocked."""
    with pytest.raises(FileError) as exc_info:
        write_file("/etc/shadow", "bad content")
    assert exc_info.value.code == "PERMISSION_DENIED"


# --- patch_file ---


def test_patch_file_success(tmp_path: object) -> None:
    """Patching a unique occurrence replaces it."""
    p = tmp_path / "patch.txt"  # type: ignore[operator]
    p.write_text("hello world")

    result = patch_file(str(p), "hello", "goodbye")
    assert result.replacements == 1
    assert p.read_text() == "goodbye world"


def test_patch_file_not_found_error(tmp_path: object) -> None:
    """Patching when old_string is not in the file raises NOT_FOUND."""
    p = tmp_path / "patch2.txt"  # type: ignore[operator]
    p.write_text("hello world")

    with pytest.raises(FileError) as exc_info:
        patch_file(str(p), "xyz", "abc")
    assert exc_info.value.code == "NOT_FOUND"


def test_patch_file_non_unique_error(tmp_path: object) -> None:
    """Patching a non-unique occurrence without --replace-all raises NOT_UNIQUE."""
    p = tmp_path / "patch3.txt"  # type: ignore[operator]
    p.write_text("aaa bbb aaa")

    with pytest.raises(FileError) as exc_info:
        patch_file(str(p), "aaa", "ccc")
    assert exc_info.value.code == "NOT_UNIQUE"


def test_patch_file_replace_all(tmp_path: object) -> None:
    """Patching with replace_all replaces all occurrences."""
    p = tmp_path / "patch4.txt"  # type: ignore[operator]
    p.write_text("aaa bbb aaa")

    result = patch_file(str(p), "aaa", "ccc", replace_all=True)
    assert result.replacements == 2
    assert p.read_text() == "ccc bbb ccc"


# --- search_files ---


def test_search_with_matches(tmp_path: object) -> None:
    """Searching with a matching pattern returns results."""
    d = tmp_path / "src"  # type: ignore[operator]
    d.mkdir()
    (d / "file1.py").write_text("def foo():\n    return 42\n")
    (d / "file2.py").write_text("def bar():\n    return 0\n")

    result = search_files("def \\w+", str(d))
    assert result.total == 2
    assert len(result.matches) == 2
    assert all(m.line == 1 for m in result.matches)


def test_search_with_no_matches(tmp_path: object) -> None:
    """Searching with a non-matching pattern returns empty results."""
    d = tmp_path / "empty_search"  # type: ignore[operator]
    d.mkdir()
    (d / "file.txt").write_text("hello world\n")

    result = search_files("zzz_no_match", str(d))
    assert result.total == 0
    assert result.matches == []


def test_search_with_glob_filter(tmp_path: object) -> None:
    """Searching with a glob filter only matches filtered files."""
    d = tmp_path / "filtered"  # type: ignore[operator]
    d.mkdir()
    (d / "code.py").write_text("hello\n")
    (d / "data.txt").write_text("hello\n")

    result = search_files("hello", str(d), glob="*.py")
    assert result.total == 1
    assert result.matches[0].file == "code.py"


def test_search_with_context_lines(tmp_path: object) -> None:
    """Search with context lines includes surrounding content."""
    d = tmp_path / "ctx"  # type: ignore[operator]
    d.mkdir()
    (d / "f.txt").write_text("aaa\nbbb\nccc\nddd\neee\n")

    result = search_files("ccc", str(d), context_lines=1)
    assert result.total == 1
    assert "bbb" in result.matches[0].content
    assert "ddd" in result.matches[0].content


def test_search_with_offset_and_limit(tmp_path: object) -> None:
    """Search with offset and limit returns correct slice."""
    d = tmp_path / "paginated"  # type: ignore[operator]
    d.mkdir()
    (d / "f.txt").write_text("match\nmatch\nmatch\nmatch\nmatch\n")

    result = search_files("match", str(d), offset=1, limit=2)
    assert len(result.matches) == 2
    assert result.total == 5
    assert result.truncated is True


# --- list_directory ---


def test_list_directory(tmp_path: object) -> None:
    """Listing a directory returns its entries."""
    d = tmp_path / "mydir"  # type: ignore[operator]
    d.mkdir()
    (d / "a.txt").write_text("a")
    (d / "b.txt").write_text("bb")
    sub = d / "sub"
    sub.mkdir()

    result = list_directory(str(d))
    assert result.total == 3
    names = [e.name for e in result.entries]
    assert "a.txt" in names
    assert "b.txt" in names
    assert "sub" in names


def test_list_directory_not_found() -> None:
    """Listing a nonexistent directory raises DIR_NOT_FOUND."""
    with pytest.raises(FileError) as exc_info:
        list_directory("/tmp/nonexistent_dir_abc123")
    assert exc_info.value.code == "DIR_NOT_FOUND"


# --- tree_directory ---


def test_tree_directory(tmp_path: object) -> None:
    """Tree listing returns nested entries."""
    d = tmp_path / "tree_root"  # type: ignore[operator]
    d.mkdir()
    (d / "file.txt").write_text("f")
    sub = d / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("n")

    result = tree_directory(str(d))
    assert result.total == 3
    paths = [e.path for e in result.entries]
    assert "file.txt" in paths
    assert "sub" in paths
    assert os.path.join("sub", "nested.txt") in paths


def test_tree_depth_limit(tmp_path: object) -> None:
    """Tree listing respects depth limit."""
    d = tmp_path / "deep"  # type: ignore[operator]
    d.mkdir()
    (d / "top.txt").write_text("t")
    sub = d / "level1"
    sub.mkdir()
    (sub / "mid.txt").write_text("m")
    sub2 = sub / "level2"
    sub2.mkdir()
    (sub2 / "bottom.txt").write_text("b")

    result = tree_directory(str(d), depth=1)
    paths = [e.path for e in result.entries]
    assert "top.txt" in paths
    assert "level1" in paths
    # depth=1 should not include level2 contents
    assert os.path.join("level1", "level2", "bottom.txt") not in paths
