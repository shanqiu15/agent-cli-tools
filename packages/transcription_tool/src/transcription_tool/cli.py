"""Typer CLI for the transcription tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from transcription_tool.service import transcribe_audio

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Audio transcription tool for LLM agents."""


@app.command("transcribe")
def transcribe_cmd(
    file: Annotated[
        str,
        typer.Option(help="Path to the audio file to transcribe"),
    ],
    provider: Annotated[
        str | None,
        typer.Option(help="Transcription provider to use (groq or openai)"),
    ] = None,
) -> None:
    """Transcribe an audio file using a speech-to-text model."""
    try:
        result = transcribe_audio(file=file, provider=provider)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
