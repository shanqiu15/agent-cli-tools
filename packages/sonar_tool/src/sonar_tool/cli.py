"""Typer CLI for the sonar tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from sonar_tool.service import VALID_MODELS, search

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """AI-powered search tool using the Perplexity Sonar API."""


@app.command("search")
def search_command(
    query: Annotated[
        str,
        typer.Option(help="Search query string"),
    ],
    model: Annotated[
        str,
        typer.Option(help="Sonar model to use"),
    ] = "sonar",
) -> None:
    """Query the Perplexity Sonar API for AI-powered search with citations."""
    if model not in VALID_MODELS:
        emit_error(
            code="INVALID_INPUT",
            message=f"Invalid model '{model}'. Choose from: {', '.join(VALID_MODELS)}",
        )
        return

    try:
        result = search(query=query, model=model)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
