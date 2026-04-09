"""Business logic for structured task list operations."""

import json
import os
from pathlib import Path

from todo_tool.errors import TodoError
from todo_tool.models import (
    ClearResult,
    ListResult,
    TodoItem,
    TodoSummary,
    VALID_STATUSES,
    WriteResult,
)

DEFAULT_DATA_DIR = os.path.join(Path.home(), ".local", "share", "todo_tool")
TODO_FILENAME = "todos.json"


def _todo_path(data_dir: str | None = None) -> str:
    """Return the absolute path to the todo JSON file.

    Args:
        data_dir: Optional override for the data directory.

    Returns:
        Absolute path to the todo file.
    """
    directory = data_dir or DEFAULT_DATA_DIR
    return os.path.join(directory, TODO_FILENAME)


def _load_items(data_dir: str | None = None) -> list[TodoItem]:
    """Load todo items from disk.

    Args:
        data_dir: Optional override for the data directory.

    Returns:
        List of TodoItem objects. Empty list if no file exists.

    Raises:
        TodoError: On read or parse errors.
    """
    path = _todo_path(data_dir)

    if not os.path.exists(path):
        return []

    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise TodoError(
            code="READ_ERROR",
            message=f"Failed to read todo file: {exc}",
            details={"path": path},
        ) from exc

    if not isinstance(raw, list):
        raise TodoError(
            code="READ_ERROR",
            message="Todo file does not contain a JSON array",
            details={"path": path},
        )

    items: list[TodoItem] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        items.append(
            TodoItem(
                id=str(entry.get("id", "")),
                content=str(entry.get("content", "")),
                status=entry.get("status", "pending")
                if entry.get("status") in VALID_STATUSES
                else "pending",
            )
        )
    return items


def _save_items(items: list[TodoItem], data_dir: str | None = None) -> None:
    """Save todo items to disk.

    Args:
        items: List of TodoItem objects to persist.
        data_dir: Optional override for the data directory.

    Raises:
        TodoError: On write errors.
    """
    path = _todo_path(data_dir)
    directory = os.path.dirname(path)

    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as exc:
        raise TodoError(
            code="WRITE_ERROR",
            message=f"Failed to create data directory: {exc}",
            details={"path": directory},
        ) from exc

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump([item.model_dump() for item in items], f, indent=2)
    except OSError as exc:
        raise TodoError(
            code="WRITE_ERROR",
            message=f"Failed to write todo file: {exc}",
            details={"path": path},
        ) from exc


def _summarize(items: list[TodoItem]) -> TodoSummary:
    """Compute summary counts for a list of todo items.

    Args:
        items: List of TodoItem objects.

    Returns:
        TodoSummary with counts by status.
    """
    return TodoSummary(
        total=len(items),
        pending=sum(1 for i in items if i.status == "pending"),
        in_progress=sum(1 for i in items if i.status == "in_progress"),
        completed=sum(1 for i in items if i.status == "completed"),
        cancelled=sum(1 for i in items if i.status == "cancelled"),
    )


def list_todos(data_dir: str | None = None) -> ListResult:
    """List all todo items.

    Args:
        data_dir: Optional override for the data directory.

    Returns:
        ListResult with items and summary.

    Raises:
        TodoError: On read errors.
    """
    items = _load_items(data_dir)
    return ListResult(items=items, summary=_summarize(items))


def write_todos(
    items_json: str,
    merge: bool = False,
    data_dir: str | None = None,
) -> WriteResult:
    """Write todo items to disk.

    In default mode, replaces the entire list. In merge mode, updates existing
    items by id and appends new ones, preserving order of existing items.

    Args:
        items_json: JSON string containing an array of todo item objects.
        merge: If True, merge with existing items instead of replacing.
        data_dir: Optional override for the data directory.

    Returns:
        WriteResult with the full list and summary counts.

    Raises:
        TodoError: On invalid input or write errors.
    """
    try:
        raw = json.loads(items_json)
    except json.JSONDecodeError as exc:
        raise TodoError(
            code="INVALID_INPUT",
            message=f"Invalid JSON: {exc}",
            details={"input": items_json[:200]},
        ) from exc

    if not isinstance(raw, list):
        raise TodoError(
            code="INVALID_INPUT",
            message="Expected a JSON array of todo items",
            details={"type": type(raw).__name__},
        )

    new_items: list[TodoItem] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise TodoError(
                code="INVALID_INPUT",
                message="Each item must be a JSON object with id, content, status",
                details={"item": str(entry)[:200]},
            )
        status = entry.get("status", "pending")
        if status not in VALID_STATUSES:
            status = "pending"
        new_items.append(
            TodoItem(
                id=str(entry.get("id", "")),
                content=str(entry.get("content", "")),
                status=status,
            )
        )

    if merge:
        existing = _load_items(data_dir)
        new_by_id = {item.id: item for item in new_items}
        merged: list[TodoItem] = []
        seen_ids: set[str] = set()

        # Update existing items in their original order
        for item in existing:
            if item.id in new_by_id:
                merged.append(new_by_id[item.id])
            else:
                merged.append(item)
            seen_ids.add(item.id)

        # Append new items not seen in existing
        for item in new_items:
            if item.id not in seen_ids:
                merged.append(item)

        result_items = merged
    else:
        result_items = new_items

    _save_items(result_items, data_dir)
    return WriteResult(items=result_items, summary=_summarize(result_items))


def clear_todos(data_dir: str | None = None) -> ClearResult:
    """Clear all todo items.

    Args:
        data_dir: Optional override for the data directory.

    Returns:
        ClearResult with the number of items cleared.

    Raises:
        TodoError: On read or write errors.
    """
    items = _load_items(data_dir)
    count = len(items)
    _save_items([], data_dir)
    return ClearResult(cleared=count)
