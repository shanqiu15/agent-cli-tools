"""Typer CLI for the web crawl tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from web_crawl_tool.service import crawl

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Web crawl tool for extracting readable content from web pages."""


@app.command("crawl")
def crawl_command(
    url: Annotated[
        str,
        typer.Option(help="URL to crawl"),
    ],
    timeout: Annotated[
        int,
        typer.Option(help="Request timeout in seconds"),
    ] = 60,
    max_length: Annotated[
        int,
        typer.Option(help="Maximum content length before truncation"),
    ] = 20000,
) -> None:
    """Fetch and extract readable content from a web page."""
    try:
        result = crawl(url=url, timeout=timeout, max_length=max_length)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
