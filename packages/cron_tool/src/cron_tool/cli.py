"""Typer CLI for the cron tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from cron_tool.service import create_job, delete_job, list_jobs

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Schedule jobs via an HTTP gateway API."""


@app.command("create")
def create_command(
    name: Annotated[
        str,
        typer.Option(help="Human-readable name for the job"),
    ],
    schedule: Annotated[
        str,
        typer.Option(help="Cron expression, interval (e.g. 'every 5m'), or ISO timestamp"),
    ],
    command: Annotated[
        str,
        typer.Option(help="Command to execute on schedule"),
    ],
    timezone: Annotated[
        str,
        typer.Option(help="Timezone for the schedule"),
    ] = "UTC",
) -> None:
    """Create a new scheduled job."""
    try:
        result = create_job(
            name=name, schedule=schedule, command=command, timezone=timezone
        )
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("list")
def list_command() -> None:
    """List all scheduled jobs."""
    try:
        result = list_jobs()
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("delete")
def delete_command(
    job_id: Annotated[
        str,
        typer.Option(help="ID of the job to delete"),
    ],
) -> None:
    """Delete a scheduled job."""
    try:
        result = delete_job(job_id=job_id)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
