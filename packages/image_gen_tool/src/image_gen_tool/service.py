"""Business logic for image generation via the Google Gemini API."""

import os
from pathlib import Path

from cli_common.errors import ToolException
from google import genai

from image_gen_tool.models import ImageGenResponse

GOOGLE_API_KEY_ENV = "GOOGLE_API_KEY"
MODEL = "gemini-3.1-flash-image-preview"

VALID_ASPECT_RATIOS = ("1:1", "16:9", "9:16", "4:3", "3:4")
VALID_IMAGE_SIZES = ("512", "1K", "2K", "4K")


def generate(
    prompt: str,
    output_path: str,
    aspect_ratio: str = "1:1",
    image_size: str | None = None,
) -> ImageGenResponse:
    """Generate an image using the Gemini API and save it to disk.

    Args:
        prompt: Text prompt for image generation.
        output_path: File path to save the generated image.
        aspect_ratio: Aspect ratio for the generated image.

    Returns:
        ImageGenResponse with path, prompt, and aspect_ratio.

    Raises:
        ToolException: On missing credentials, API errors, or file write errors.
    """
    api_key = os.environ.get(GOOGLE_API_KEY_ENV)
    if not api_key:
        raise ToolException(
            code="MISSING_CREDENTIALS",
            message=f"Environment variable {GOOGLE_API_KEY_ENV} is not set",
            details={"env_var": GOOGLE_API_KEY_ENV},
        )

    out = Path(output_path)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ToolException(
            code="INVALID_OUTPUT_PATH",
            message=f"Cannot create output directory: {exc}",
            details={"output_path": output_path},
        ) from exc

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL,
            contents=[prompt],
            config=genai.types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=genai.types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    **({"image_size": image_size} if image_size else {}),
                ),
            ),
        )
    except Exception as exc:
        raise ToolException(
            code="API_ERROR",
            message=f"Gemini API error: {exc}",
            details={"prompt": prompt},
        ) from exc

    image_bytes = None
    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_bytes = part.inline_data.data
                break

    if not image_bytes:
        raise ToolException(
            code="API_ERROR",
            message="Gemini API returned no image data",
            details={"prompt": prompt},
        )

    try:
        out.write_bytes(image_bytes)
    except OSError as exc:
        raise ToolException(
            code="FILE_WRITE_ERROR",
            message=f"Failed to write image to {output_path}: {exc}",
            details={"output_path": output_path},
        ) from exc

    return ImageGenResponse(
        path=str(out.resolve()),
        prompt=prompt,
        aspect_ratio=aspect_ratio,
    )
