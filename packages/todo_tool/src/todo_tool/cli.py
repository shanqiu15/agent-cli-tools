"""Typer CLI for the todo tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from todo_tool.service import clear_todos, list_todos, write_todos

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Structured task list tool for LLM agents."""


@app.command("list")
def list_cmd(
    data_dir: Annotated[
        str | None,
        typer.Option(help="Override the default data directory"),
    ] = None,
) -> None:
    """List all todo items."""
    try:
        result = list_todos(data_dir=data_dir)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("write")
def write_cmd(
    items: Annotated[
        str,
        typer.Option(help="JSON array of {id, content, status} objects"),
    ],
    merge: Annotated[
        bool,
        typer.Option("--merge", help="Merge with existing items instead of replacing"),
    ] = False,
    data_dir: Annotated[
        str | None,
        typer.Option(help="Override the default data directory"),
    ] = None,
) -> None:
    """Write todo items to the task list."""
    try:
        result = write_todos(items_json=items, merge=merge, data_dir=data_dir)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("clear")
def clear_cmd(
    data_dir: Annotated[
        str | None,
        typer.Option(help="Override the default data directory"),
    ] = None,
) -> None:
    """Clear all todo items."""
    try:
        result = clear_todos(data_dir=data_dir)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
