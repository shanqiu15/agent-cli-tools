"""Typer CLI for the OCR tool."""

from pathlib import Path
from typing import Annotated

import typer

from cli_common.io import emit_error, emit_success
from ocr_tool.errors import OcrError
from ocr_tool.models import OcrRequest
from ocr_tool.service import run_ocr

app = typer.Typer(add_completion=False)


@app.command()
def extract(
    image: Annotated[Path, typer.Option(help="Path to the input image file")],
    output: Annotated[
        Path | None,
        typer.Option(
            help="Path for the output text file; defaults to <image_stem>.txt"
        ),
    ] = None,
    mode: Annotated[
        str, typer.Option(help="OCR engine mode: 'local' or 'llm'")
    ] = "local",
    model: Annotated[
        str | None,
        typer.Option(help="Optional model name override for the selected engine"),
    ] = None,
) -> None:
    """Extract text from an image using OCR."""
    if mode not in ("local", "llm"):
        emit_error(
            code="INVALID_MODE",
            message=f"Invalid mode '{mode}'. Must be 'local' or 'llm'.",
        )

    try:
        request = OcrRequest(
            image_path=image,
            output_path=output,
            mode=mode,  # type: ignore[arg-type]
            model=model,
        )
        result = run_ocr(request)
        emit_success(result.model_dump(mode="json"))
    except OcrError as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
