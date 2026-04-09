"""Typer CLI for the browser tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from browser_tool.service import PlaywrightCLI

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Browser automation tool wrapping @playwright/cli."""


def _get_cli(session: str = "default") -> PlaywrightCLI:
    """Create a PlaywrightCLI instance, handling not-found errors."""
    return PlaywrightCLI(session=session)


@app.command("start")
def start_cmd(
    session: Annotated[
        str,
        typer.Option(help="Named session identifier"),
    ] = "default",
) -> None:
    """Launch a headless browser session."""
    try:
        cli = _get_cli(session)
        result = cli.start()
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("stop")
def stop_cmd(
    session: Annotated[
        str,
        typer.Option(help="Named session identifier"),
    ] = "default",
) -> None:
    """Terminate the browser session."""
    try:
        cli = _get_cli(session)
        result = cli.stop()
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("status")
def status_cmd(
    session: Annotated[
        str,
        typer.Option(help="Named session identifier"),
    ] = "default",
) -> None:
    """Check whether a browser session is active."""
    try:
        cli = _get_cli(session)
        result = cli.status()
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("navigate")
def navigate_cmd(
    url: Annotated[
        str,
        typer.Option(help="URL to navigate to"),
    ],
    session: Annotated[
        str,
        typer.Option(help="Named session identifier"),
    ] = "default",
) -> None:
    """Navigate to a URL and return the page snapshot."""
    try:
        cli = _get_cli(session)
        result = cli.navigate(url)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("snapshot")
def snapshot_cmd(
    session: Annotated[
        str,
        typer.Option(help="Named session identifier"),
    ] = "default",
) -> None:
    """Return the accessibility tree of the current page."""
    try:
        cli = _get_cli(session)
        result = cli.snapshot()
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("screenshot")
def screenshot_cmd(
    path: Annotated[
        str,
        typer.Option(help="File path to save the screenshot"),
    ],
    session: Annotated[
        str,
        typer.Option(help="Named session identifier"),
    ] = "default",
) -> None:
    """Capture a screenshot and save to a file."""
    try:
        cli = _get_cli(session)
        result = cli.screenshot(path)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("click")
def click_cmd(
    ref: Annotated[
        str,
        typer.Option(help="Element ref from accessibility snapshot"),
    ],
    session: Annotated[
        str,
        typer.Option(help="Named session identifier"),
    ] = "default",
) -> None:
    """Click an element by its accessibility ref."""
    try:
        cli = _get_cli(session)
        result = cli.click(ref)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("type")
def type_cmd(
    ref: Annotated[
        str,
        typer.Option(help="Element ref from accessibility snapshot"),
    ],
    text: Annotated[
        str,
        typer.Option(help="Text to type into the element"),
    ],
    session: Annotated[
        str,
        typer.Option(help="Named session identifier"),
    ] = "default",
) -> None:
    """Type text into an element by its accessibility ref."""
    try:
        cli = _get_cli(session)
        result = cli.type_text(ref, text)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("press")
def press_cmd(
    key: Annotated[
        str,
        typer.Option(help="Key to press (e.g. Enter, Tab, Escape)"),
    ],
    session: Annotated[
        str,
        typer.Option(help="Named session identifier"),
    ] = "default",
) -> None:
    """Press a keyboard key."""
    try:
        cli = _get_cli(session)
        result = cli.press(key)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
