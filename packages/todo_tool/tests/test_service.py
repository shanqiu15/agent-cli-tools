"""Tests for the todo tool service layer."""

import json

import pytest

from todo_tool.errors import TodoError
from todo_tool.models import VALID_STATUSES
from todo_tool.service import clear_todos, list_todos, write_todos


# --- list_todos ---


def test_list_empty(tmp_path: object) -> None:
    """Listing with no existing file returns an empty list."""
    result = list_todos(data_dir=str(tmp_path))
    assert result.items == []
    assert result.summary.total == 0


def test_list_after_write(tmp_path: object) -> None:
    """Items written in one call are returned by list."""
    data_dir = str(tmp_path)
    items = json.dumps([
        {"id": "1", "content": "First task", "status": "pending"},
        {"id": "2", "content": "Second task", "status": "in_progress"},
    ])
    write_todos(items_json=items, data_dir=data_dir)

    result = list_todos(data_dir=data_dir)
    assert len(result.items) == 2
    assert result.items[0].id == "1"
    assert result.items[1].id == "2"
    assert result.summary.total == 2
    assert result.summary.pending == 1
    assert result.summary.in_progress == 1


# --- write_todos ---


def test_write_replace_mode(tmp_path: object) -> None:
    """Default write replaces the entire list."""
    data_dir = str(tmp_path)

    first = json.dumps([{"id": "1", "content": "Task A", "status": "pending"}])
    write_todos(items_json=first, data_dir=data_dir)

    second = json.dumps([{"id": "2", "content": "Task B", "status": "completed"}])
    result = write_todos(items_json=second, data_dir=data_dir)

    assert len(result.items) == 1
    assert result.items[0].id == "2"
    assert result.summary.completed == 1


def test_write_merge_updates_existing(tmp_path: object) -> None:
    """Merge mode updates existing items by id."""
    data_dir = str(tmp_path)

    initial = json.dumps([
        {"id": "1", "content": "Task A", "status": "pending"},
        {"id": "2", "content": "Task B", "status": "pending"},
    ])
    write_todos(items_json=initial, data_dir=data_dir)

    update = json.dumps([
        {"id": "1", "content": "Task A updated", "status": "completed"},
    ])
    result = write_todos(items_json=update, merge=True, data_dir=data_dir)

    assert len(result.items) == 2
    assert result.items[0].id == "1"
    assert result.items[0].content == "Task A updated"
    assert result.items[0].status == "completed"
    assert result.items[1].id == "2"
    assert result.items[1].status == "pending"


def test_write_merge_appends_new(tmp_path: object) -> None:
    """Merge mode appends items with new ids."""
    data_dir = str(tmp_path)

    initial = json.dumps([{"id": "1", "content": "Existing", "status": "pending"}])
    write_todos(items_json=initial, data_dir=data_dir)

    update = json.dumps([{"id": "2", "content": "New item", "status": "in_progress"}])
    result = write_todos(items_json=update, merge=True, data_dir=data_dir)

    assert len(result.items) == 2
    assert result.items[0].id == "1"
    assert result.items[1].id == "2"


def test_write_merge_preserves_order(tmp_path: object) -> None:
    """Merge mode preserves the order of existing items."""
    data_dir = str(tmp_path)

    initial = json.dumps([
        {"id": "a", "content": "First", "status": "pending"},
        {"id": "b", "content": "Second", "status": "pending"},
        {"id": "c", "content": "Third", "status": "pending"},
    ])
    write_todos(items_json=initial, data_dir=data_dir)

    # Update b and add d
    update = json.dumps([
        {"id": "d", "content": "Fourth", "status": "pending"},
        {"id": "b", "content": "Second updated", "status": "completed"},
    ])
    result = write_todos(items_json=update, merge=True, data_dir=data_dir)

    ids = [item.id for item in result.items]
    assert ids == ["a", "b", "c", "d"]
    assert result.items[1].content == "Second updated"


def test_write_invalid_json(tmp_path: object) -> None:
    """Invalid JSON raises INVALID_INPUT."""
    with pytest.raises(TodoError) as exc_info:
        write_todos(items_json="not json", data_dir=str(tmp_path))
    assert exc_info.value.code == "INVALID_INPUT"


def test_write_not_array(tmp_path: object) -> None:
    """Non-array JSON raises INVALID_INPUT."""
    with pytest.raises(TodoError) as exc_info:
        write_todos(items_json='{"id": "1"}', data_dir=str(tmp_path))
    assert exc_info.value.code == "INVALID_INPUT"


def test_write_non_object_item(tmp_path: object) -> None:
    """Non-object items in the array raise INVALID_INPUT."""
    with pytest.raises(TodoError) as exc_info:
        write_todos(items_json='["not an object"]', data_dir=str(tmp_path))
    assert exc_info.value.code == "INVALID_INPUT"


# --- status validation ---


def test_invalid_status_defaults_to_pending(tmp_path: object) -> None:
    """An invalid status value is defaulted to pending."""
    data_dir = str(tmp_path)
    items = json.dumps([{"id": "1", "content": "Task", "status": "invalid_status"}])
    result = write_todos(items_json=items, data_dir=data_dir)
    assert result.items[0].status == "pending"


def test_all_valid_statuses_accepted(tmp_path: object) -> None:
    """All four valid statuses are accepted."""
    data_dir = str(tmp_path)
    items = json.dumps([
        {"id": str(i), "content": f"Task {s}", "status": s}
        for i, s in enumerate(VALID_STATUSES)
    ])
    result = write_todos(items_json=items, data_dir=data_dir)
    statuses = {item.status for item in result.items}
    assert statuses == set(VALID_STATUSES)


# --- clear_todos ---


def test_clear_removes_all(tmp_path: object) -> None:
    """Clear removes all items and returns the count."""
    data_dir = str(tmp_path)
    items = json.dumps([
        {"id": "1", "content": "A", "status": "pending"},
        {"id": "2", "content": "B", "status": "completed"},
    ])
    write_todos(items_json=items, data_dir=data_dir)

    result = clear_todos(data_dir=data_dir)
    assert result.cleared == 2

    listed = list_todos(data_dir=data_dir)
    assert listed.items == []


def test_clear_empty(tmp_path: object) -> None:
    """Clearing when no items exist returns 0."""
    result = clear_todos(data_dir=str(tmp_path))
    assert result.cleared == 0


# --- persistence across invocations ---


def test_persistence_across_calls(tmp_path: object) -> None:
    """Data persists between separate service calls (simulating separate processes)."""
    data_dir = str(tmp_path)

    items = json.dumps([{"id": "1", "content": "Persist me", "status": "pending"}])
    write_todos(items_json=items, data_dir=data_dir)

    # Simulate separate invocation by calling list_todos independently
    result = list_todos(data_dir=data_dir)
    assert len(result.items) == 1
    assert result.items[0].content == "Persist me"


# --- summary counts ---


def test_summary_counts(tmp_path: object) -> None:
    """Summary counts reflect item statuses correctly."""
    data_dir = str(tmp_path)
    items = json.dumps([
        {"id": "1", "content": "A", "status": "pending"},
        {"id": "2", "content": "B", "status": "in_progress"},
        {"id": "3", "content": "C", "status": "completed"},
        {"id": "4", "content": "D", "status": "cancelled"},
        {"id": "5", "content": "E", "status": "pending"},
    ])
    result = write_todos(items_json=items, data_dir=data_dir)
    assert result.summary.total == 5
    assert result.summary.pending == 2
    assert result.summary.in_progress == 1
    assert result.summary.completed == 1
    assert result.summary.cancelled == 1
