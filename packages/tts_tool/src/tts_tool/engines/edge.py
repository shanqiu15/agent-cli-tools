"""Edge TTS engine using the edge-tts package."""

import asyncio
from pathlib import Path

import edge_tts

from tts_tool.errors import TTSError

DEFAULT_VOICE = "en-US-AriaNeural"


def speak(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> str:
    """Generate speech using Edge TTS.

    Args:
        text: Text to convert to speech.
        output_path: Path to write the MP3 output file.
        voice: Edge TTS voice name.

    Returns:
        The voice name used.

    Raises:
        TTSError: On generation errors.
    """
    try:
        asyncio.run(_generate(text, output_path, voice))
    except Exception as exc:
        raise TTSError(
            code="API_ERROR",
            message=f"Edge TTS error: {exc}",
            details={"voice": voice},
        ) from exc

    return voice


async def _generate(text: str, output_path: Path, voice: str) -> None:
    """Async helper to run edge-tts communicate."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
