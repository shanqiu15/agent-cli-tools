"""Google Gemini vision engine."""

import base64
import json

import httpx

from vision_tool.errors import VisionError

MODEL = "gemini-2.0-flash"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def analyze(
    image_bytes: bytes,
    mime_type: str,
    prompt: str,
    api_key: str,
) -> tuple[str, str]:
    """Analyze an image using the Google Gemini API.

    Args:
        image_bytes: Raw image bytes.
        mime_type: MIME type of the image.
        prompt: User prompt describing what to analyze.
        api_key: Google API key.

    Returns:
        Tuple of (analysis_text, model_name).

    Raises:
        VisionError: On API errors.
    """
    b64_data = base64.b64encode(image_bytes).decode("ascii")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_data,
                        }
                    },
                ]
            }
        ]
    }

    url = API_URL.format(model=MODEL)
    try:
        response = httpx.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise VisionError(
            code="TIMEOUT",
            message="Gemini API request timed out",
            details={"model": MODEL},
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise VisionError(
            code="API_ERROR",
            message=f"Gemini API returned HTTP {exc.response.status_code}",
            details={
                "status_code": exc.response.status_code,
                "body": exc.response.text[:500],
            },
        ) from exc

    try:
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        raise VisionError(
            code="API_ERROR",
            message="Unexpected response format from Gemini API",
            details={"body": response.text[:500]},
        ) from exc

    return text, MODEL
