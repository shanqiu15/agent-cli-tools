"""LLM-based OCR engine using the Anthropic API."""

import base64
import mimetypes
import os
from pathlib import Path

from typing import cast

import anthropic
from anthropic.types import Base64ImageSourceParam, ImageBlockParam, TextBlockParam
from PIL import Image

from ocr_tool.errors import OcrError

_DEFAULT_MODEL = "claude-sonnet-4-20250514"


def extract_text_llm(image_path: Path, model: str | None = None) -> str:
    """Extract text from an image using a multimodal LLM.

    Args:
        image_path: Path to the image file.
        model: Optional model name override. Defaults to claude-sonnet-4-20250514.

    Returns:
        Extracted text as a string.

    Raises:
        OcrError: If the API key is missing, image path doesn't exist,
            or the image is invalid.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise OcrError(
            code="MISSING_API_KEY",
            message="ANTHROPIC_API_KEY environment variable is not set",
        )

    if not image_path.exists():
        raise OcrError(
            code="IMAGE_NOT_FOUND",
            message=f"Image file not found: {image_path}",
            details={"image_path": str(image_path)},
        )

    try:
        img = Image.open(image_path)
        img.verify()
    except Exception as exc:
        raise OcrError(
            code="INVALID_IMAGE",
            message=f"Cannot open image: {image_path}",
            details={"image_path": str(image_path), "reason": str(exc)},
        ) from exc

    image_data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    media_type = mimetypes.guess_type(str(image_path))[0] or "image/png"

    source = cast(
        Base64ImageSourceParam,
        {
            "type": "base64",
            "media_type": media_type,
            "data": image_data,
        },
    )
    image_block: ImageBlockParam = {
        "type": "image",
        "source": source,
    }
    text_block: TextBlockParam = {
        "type": "text",
        "text": "Extract all text from this image. Return only the extracted text, preserving the original layout as much as possible. Do not add any commentary or explanation.",
    }

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model or _DEFAULT_MODEL,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [image_block, text_block],
            }
        ],
    )

    block = message.content[0]
    assert hasattr(block, "text"), f"Unexpected content block type: {block.type}"
    return block.text
