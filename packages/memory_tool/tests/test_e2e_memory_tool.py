"""End-to-end tests for memory_tool using real filesystem operations."""

import json
from pathlib import Path

from typer.testing import CliRunner

from memory_tool.cli import app

runner = CliRunner()


class TestMemoryWriteReadE2E:
    def test_write_and_read(self, tmp_path: Path) -> None:
        mem_dir = str(tmp_path)
        result = runner.invoke(
            app,
            ["write", "--path", "notes.md", "--content", "hello world", "--memory-dir", mem_dir],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["result"]["bytes_written"] == 11

        result = runner.invoke(
            app, ["read", "--path", "notes.md", "--memory-dir", mem_dir]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["result"]["content"] == "hello world"

    def test_append(self, tmp_path: Path) -> None:
        mem_dir = str(tmp_path)
        runner.invoke(
            app,
            ["write", "--path", "log.md", "--content", "first\n", "--memory-dir", mem_dir],
        )
        runner.invoke(
            app,
            ["write", "--path", "log.md", "--content", "second\n", "--append", "--memory-dir", mem_dir],
        )
        result = runner.invoke(
            app, ["read", "--path", "log.md", "--memory-dir", mem_dir]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "first" in data["result"]["content"]
        assert "second" in data["result"]["content"]

    def test_nested_path(self, tmp_path: Path) -> None:
        mem_dir = str(tmp_path)
        result = runner.invoke(
            app,
            ["write", "--path", "2026/04/notes.md", "--content", "nested", "--memory-dir", mem_dir],
        )
        assert result.exit_code == 0
        assert (tmp_path / "2026" / "04" / "notes.md").exists()


class TestMemorySearchE2E:
    def test_search_finds_matching_files(self, tmp_path: Path) -> None:
        mem_dir = str(tmp_path)
        runner.invoke(
            app,
            ["write", "--path", "a.md", "--content", "Python is great", "--memory-dir", mem_dir],
        )
        runner.invoke(
            app,
            ["write", "--path", "b.md", "--content", "Java is fine", "--memory-dir", mem_dir],
        )
        result = runner.invoke(
            app, ["search", "--query", "Python", "--memory-dir", mem_dir]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["result"]["total"] == 1
        assert data["result"]["matches"][0]["path"] == "a.md"

    def test_search_case_insensitive(self, tmp_path: Path) -> None:
        mem_dir = str(tmp_path)
        runner.invoke(
            app,
            ["write", "--path", "doc.md", "--content", "Hello World", "--memory-dir", mem_dir],
        )
        result = runner.invoke(
            app, ["search", "--query", "hello", "--memory-dir", mem_dir]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["result"]["total"] == 1

    def test_search_no_match(self, tmp_path: Path) -> None:
        mem_dir = str(tmp_path)
        runner.invoke(
            app,
            ["write", "--path", "doc.md", "--content", "nothing here", "--memory-dir", mem_dir],
        )
        result = runner.invoke(
            app, ["search", "--query", "nonexistent", "--memory-dir", mem_dir]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["result"]["total"] == 0


class TestMemoryErrorsE2E:
    def test_read_nonexistent_file(self, tmp_path: Path) -> None:
        mem_dir = str(tmp_path)
        result = runner.invoke(
            app, ["read", "--path", "missing.md", "--memory-dir", mem_dir]
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "FILE_NOT_FOUND"

    def test_absolute_path_rejected(self, tmp_path: Path) -> None:
        mem_dir = str(tmp_path)
        result = runner.invoke(
            app, ["read", "--path", "/etc/passwd", "--memory-dir", mem_dir]
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "INVALID_PATH"

    def test_directory_traversal_rejected(self, tmp_path: Path) -> None:
        mem_dir = str(tmp_path)
        result = runner.invoke(
            app, ["read", "--path", "../../etc/passwd", "--memory-dir", mem_dir]
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "INVALID_PATH"
