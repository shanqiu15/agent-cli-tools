"""Typer CLI for the OCR tool."""

from pathlib import Path
from typing import Annotated

import typer

from cli_common.io import emit_error, emit_success
from ocr_tool.errors import OcrError
from ocr_tool.models import OcrRequest
from ocr_tool.service import run_ocr

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """OCR tool for extracting text from images."""


@app.command()
def extract(
    image: Annotated[
        Path,
        typer.Option(
            help="Path to the input image or PDF file (PDF supported in google mode only)"
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            help="Path for the output text file; defaults to <image_stem>.txt"
        ),
    ] = None,
    mode: Annotated[
        str | None, typer.Option(help="OCR engine mode: 'local' or 'google'")
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(help="Optional model name override for the selected engine"),
    ] = None,
) -> None:
    """Extract text from an image using OCR."""
    # When mode is not provided, default to 'google' with implicit mode (allows fallback)
    if mode is None:
        effective_mode = "google"
        explicit_mode = False
    else:
        effective_mode = mode
        explicit_mode = True

    if effective_mode not in ("local", "google"):
        emit_error(
            code="INVALID_MODE",
            message=f"Invalid mode '{effective_mode}'. Must be 'local' or 'google'.",
        )
        return

    try:
        request = OcrRequest(
            image_path=image,
            output_path=output,
            mode=effective_mode,  # type: ignore[arg-type]
            model=model,
            explicit_mode=explicit_mode,
        )
        result = run_ocr(request)
        emit_success(result.model_dump(mode="json"))
    except OcrError as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
