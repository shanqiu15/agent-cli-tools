"""Typer CLI for the web search tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from web_search_tool.service import search

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Web search tool using the Serper API."""


@app.command("search")
def search_command(
    query: Annotated[
        str,
        typer.Option(help="Search query string"),
    ],
    num_results: Annotated[
        int,
        typer.Option(help="Number of results to return (1-10)"),
    ] = 5,
) -> None:
    """Perform a Google search and return structured results."""
    if num_results < 1 or num_results > 10:
        emit_error(
            code="INVALID_INPUT",
            message=f"num-results must be between 1 and 10, got {num_results}",
        )
        return

    try:
        result = search(query=query, num_results=num_results)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
