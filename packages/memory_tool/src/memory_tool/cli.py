"""Typer CLI for the memory tool."""

from pathlib import Path
from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from memory_tool.service import read_memory, search_memory, write_memory

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """File-based memory system for LLM agents."""


@app.command("write")
def write_cmd(
    path: Annotated[
        str,
        typer.Option(help="Relative path within the memory directory"),
    ],
    content: Annotated[
        str,
        typer.Option(help="Content to write"),
    ],
    append: Annotated[
        bool,
        typer.Option(help="Append to existing file instead of overwriting"),
    ] = False,
    memory_dir: Annotated[
        Path,
        typer.Option(help="Root memory directory"),
    ] = Path("./memory/"),
) -> None:
    """Write content to a memory file."""
    try:
        result = write_memory(
            memory_dir=memory_dir,
            path=path,
            content=content,
            append=append,
        )
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("read")
def read_cmd(
    path: Annotated[
        str,
        typer.Option(help="Relative path within the memory directory"),
    ],
    memory_dir: Annotated[
        Path,
        typer.Option(help="Root memory directory"),
    ] = Path("./memory/"),
) -> None:
    """Read a memory file."""
    try:
        result = read_memory(memory_dir=memory_dir, path=path)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("search")
def search_cmd(
    query: Annotated[
        str,
        typer.Option(help="Substring to search for in .md files"),
    ],
    memory_dir: Annotated[
        Path,
        typer.Option(help="Root memory directory"),
    ] = Path("./memory/"),
) -> None:
    """Search memory files for matching content."""
    try:
        result = search_memory(memory_dir=memory_dir, query=query)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
