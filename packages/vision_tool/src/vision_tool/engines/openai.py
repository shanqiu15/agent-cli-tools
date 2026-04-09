"""OpenAI vision engine."""

import base64
import json

import httpx

from vision_tool.errors import VisionError

MODEL = "gpt-4o-mini"
API_URL = "https://api.openai.com/v1/chat/completions"


def analyze(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    api_key: str,
) -> tuple[str, str]:
    """Analyze an image using the OpenAI chat completions API with vision.

    Args:
        image_bytes: Raw image bytes.
        mime_type: MIME type of the image.
        prompt: User prompt describing what to analyze.
        api_key: OpenAI API key.

    Returns:
        Tuple of (analysis_text, model_name).

    Raises:
        VisionError: On API errors.
    """
    b64_data = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64_data}"

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url},
                    },
                ],
            }
        ],
        "max_tokens": 1024,
    }

    try:
        response = httpx.post(
            API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise VisionError(
            code="TIMEOUT",
            message="OpenAI API request timed out",
            details={"model": MODEL},
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise VisionError(
            code="API_ERROR",
            message=f"OpenAI API returned HTTP {exc.response.status_code}",
            details={
                "status_code": exc.response.status_code,
                "body": exc.response.text[:500],
            },
        ) from exc

    try:
        data = response.json()
        text = data["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        raise VisionError(
            code="API_ERROR",
            message="Unexpected response format from OpenAI API",
            details={"body": response.text[:500]},
        ) from exc

    return text, MODEL
