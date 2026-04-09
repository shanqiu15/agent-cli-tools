"""Tests for the todo tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from todo_tool.cli import app
from todo_tool.errors import TodoError
from todo_tool.models import (
    ClearResult,
    ListResult,
    TodoItem,
    TodoSummary,
    WriteResult,
)

runner = CliRunner()


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    output = result.output.lower()
    assert "list" in output
    assert "write" in output
    assert "clear" in output


@patch("todo_tool.cli.list_todos")
def test_list_success(mock_list) -> None:  # type: ignore[no-untyped-def]
    """A successful list emits JSON with ok=true."""
    mock_list.return_value = ListResult(
        items=[
            TodoItem(id="1", content="Task A", status="pending"),
        ],
        summary=TodoSummary(
            total=1, pending=1, in_progress=0, completed=0, cancelled=0
        ),
    )

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert len(data["result"]["items"]) == 1
    assert data["result"]["summary"]["total"] == 1


@patch("todo_tool.cli.write_todos")
def test_write_success(mock_write) -> None:  # type: ignore[no-untyped-def]
    """A successful write emits JSON with ok=true."""
    mock_write.return_value = WriteResult(
        items=[
            TodoItem(id="1", content="Task A", status="pending"),
        ],
        summary=TodoSummary(
            total=1, pending=1, in_progress=0, completed=0, cancelled=0
        ),
    )

    items_json = '[{"id": "1", "content": "Task A", "status": "pending"}]'
    result = runner.invoke(app, ["write", "--items", items_json])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["summary"]["total"] == 1


@patch(
    "todo_tool.cli.write_todos",
    side_effect=TodoError(
        code="INVALID_INPUT",
        message="Invalid JSON",
        details={"input": "bad"},
    ),
)
def test_write_invalid_input_error(mock_write) -> None:  # type: ignore[no-untyped-def]
    """Invalid input emits structured error."""
    result = runner.invoke(app, ["write", "--items", "bad"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_INPUT"


@patch("todo_tool.cli.clear_todos")
def test_clear_success(mock_clear) -> None:  # type: ignore[no-untyped-def]
    """A successful clear emits JSON with ok=true."""
    mock_clear.return_value = ClearResult(cleared=3)

    result = runner.invoke(app, ["clear"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["cleared"] == 3


@patch(
    "todo_tool.cli.list_todos",
    side_effect=TodoError(
        code="READ_ERROR",
        message="Failed to read todo file",
        details={"path": "/bad/path"},
    ),
)
def test_list_error(mock_list) -> None:  # type: ignore[no-untyped-def]
    """A read error emits structured error."""
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "READ_ERROR"
