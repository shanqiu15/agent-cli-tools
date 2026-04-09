"""Typer CLI for the bash tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from bash_tool.service import run_command

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Shell command execution tool."""


@app.command("run")
def run_command_cli(
    command: Annotated[
        str,
        typer.Option(help="Shell command to execute"),
    ],
    timeout: Annotated[
        int,
        typer.Option(help="Maximum execution time in seconds"),
    ] = 30,
    max_output: Annotated[
        int,
        typer.Option(help="Maximum output characters"),
    ] = 10000,
) -> None:
    """Execute a shell command and return structured output."""
    try:
        result = run_command(command=command, timeout=timeout, max_output=max_output)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
