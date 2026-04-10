"""Typer CLI for the TTS tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from tts_tool.service import speak_text

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Text-to-speech tool for LLM agents."""


@app.command("speak")
def speak_cmd(
    text: Annotated[
        str,
        typer.Option(help="Text to convert to speech"),
    ],
    output: Annotated[
        str | None,
        typer.Option(help="Output file path for the generated audio"),
    ] = None,
    provider: Annotated[
        str | None,
        typer.Option(help="TTS provider to use (edge or openai)"),
    ] = None,
    voice: Annotated[
        str | None,
        typer.Option(help="Voice name to use for synthesis"),
    ] = None,
) -> None:
    """Convert text to speech and save as an audio file."""
    try:
        result = speak_text(text=text, output=output, provider=provider, voice=voice)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
