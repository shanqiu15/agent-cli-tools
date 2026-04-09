"""Typer CLI for the image gen tool."""

from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from image_gen_tool.service import VALID_ASPECT_RATIOS, VALID_IMAGE_SIZES, generate

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Image generation tool using the Google Gemini API."""


@app.command("generate")
def generate_command(
    prompt: Annotated[
        str,
        typer.Option(help="Text prompt for image generation"),
    ],
    output_path: Annotated[
        str,
        typer.Option(help="File path to save the generated image"),
    ] = "./build/imagen/output.png",
    aspect_ratio: Annotated[
        str,
        typer.Option(help="Aspect ratio for the generated image"),
    ] = "1:1",
    image_size: Annotated[
        str | None,
        typer.Option(help="Image size: 512, 1K, 2K, or 4K"),
    ] = None,
) -> None:
    """Generate an image from a text prompt using the Gemini API."""
    if aspect_ratio not in VALID_ASPECT_RATIOS:
        emit_error(
            code="INVALID_INPUT",
            message=f"Invalid aspect ratio '{aspect_ratio}'. Choose from: {', '.join(VALID_ASPECT_RATIOS)}",
        )
        return

    if image_size is not None and image_size not in VALID_IMAGE_SIZES:
        emit_error(
            code="INVALID_INPUT",
            message=f"Invalid image size '{image_size}'. Choose from: {', '.join(VALID_IMAGE_SIZES)}",
        )
        return

    try:
        result = generate(
            prompt=prompt, output_path=output_path, aspect_ratio=aspect_ratio, image_size=image_size
        )
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
