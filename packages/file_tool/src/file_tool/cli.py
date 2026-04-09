"""Typer CLI for the file tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from file_tool.service import (
    list_directory,
    patch_file,
    read_file,
    search_files,
    tree_directory,
    write_file,
)

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Safe filesystem operations tool for LLM agents."""


@app.command("read")
def read_cmd(
    file: Annotated[
        str,
        typer.Option(help="Path to the file to read"),
    ],
    offset: Annotated[
        int,
        typer.Option(help="1-indexed starting line number"),
    ] = 1,
    limit: Annotated[
        int,
        typer.Option(help="Maximum number of lines to return (0 = no limit)"),
    ] = 0,
) -> None:
    """Read a file and return its contents as JSON."""
    try:
        result = read_file(
            file=file,
            offset=offset,
            limit=limit if limit > 0 else None,
        )
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("write")
def write_cmd(
    file: Annotated[
        str,
        typer.Option(help="Path to the file to write"),
    ],
    content: Annotated[
        str,
        typer.Option(help="Content to write to the file"),
    ],
) -> None:
    """Write content to a file."""
    try:
        result = write_file(file=file, content=content)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("patch")
def patch_cmd(
    file: Annotated[
        str,
        typer.Option(help="Path to the file to patch"),
    ],
    old: Annotated[
        str,
        typer.Option(help="Text to find and replace"),
    ],
    new: Annotated[
        str,
        typer.Option(help="Replacement text"),
    ],
    replace_all: Annotated[
        bool,
        typer.Option("--replace-all", help="Replace all occurrences"),
    ] = False,
) -> None:
    """Find and replace text in a file."""
    try:
        result = patch_file(file=file, old=old, new=new, replace_all=replace_all)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("search")
def search_cmd(
    pattern: Annotated[
        str,
        typer.Option(help="Regex pattern to search for"),
    ],
    path: Annotated[
        str,
        typer.Option(help="Directory to search in"),
    ] = ".",
    glob: Annotated[
        str | None,
        typer.Option(help="Glob pattern to filter files (e.g. '*.py')"),
    ] = None,
    context_lines: Annotated[
        int,
        typer.Option(help="Number of context lines around each match"),
    ] = 0,
    offset: Annotated[
        int,
        typer.Option(help="Number of matches to skip"),
    ] = 0,
    limit: Annotated[
        int,
        typer.Option(help="Maximum number of matches to return"),
    ] = 100,
) -> None:
    """Search files for a regex pattern."""
    try:
        result = search_files(
            pattern=pattern,
            path=path,
            glob=glob,
            context_lines=context_lines,
            offset=offset,
            limit=limit,
        )
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("list")
def list_cmd(
    path: Annotated[
        str,
        typer.Option(help="Directory path to list"),
    ] = ".",
    depth: Annotated[
        int,
        typer.Option(help="How many levels deep to list"),
    ] = 1,
) -> None:
    """List the contents of a directory."""
    try:
        result = list_directory(path=path, depth=depth)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("tree")
def tree_cmd(
    path: Annotated[
        str,
        typer.Option(help="Directory path to tree"),
    ] = ".",
    depth: Annotated[
        int,
        typer.Option(help="Maximum depth to recurse"),
    ] = 3,
) -> None:
    """Generate a tree listing of a directory."""
    try:
        result = tree_directory(path=path, depth=depth)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
