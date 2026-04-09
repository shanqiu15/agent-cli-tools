"""Typer CLI for the vision tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from vision_tool.service import analyze_image

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Vision analysis tool for LLM agents."""


@app.command("analyze")
def analyze_cmd(
    image: Annotated[
        str,
        typer.Option(help="Local file path or URL of the image to analyze"),
    ],
    prompt: Annotated[
        str,
        typer.Option(help="Question or instruction for the vision model"),
    ],
    provider: Annotated[
        str | None,
        typer.Option(help="Vision provider to use (gemini or openai)"),
    ] = None,
) -> None:
    """Analyze an image using a vision model."""
    try:
        result = analyze_image(image=image, prompt=prompt, provider=provider)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
