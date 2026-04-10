"""OpenAI TTS engine."""

from pathlib import Path

from openai import OpenAI, OpenAIError

from tts_tool.errors import TTSError

MODEL = "tts-1"
DEFAULT_VOICE = "alloy"


def speak(text: str, output_path: Path, api_key: str, voice: str = DEFAULT_VOICE) -> str:
    """Generate speech using the OpenAI TTS API.

    Args:
        text: Text to convert to speech.
        output_path: Path to write the output audio file.
        api_key: OpenAI API key.
        voice: OpenAI TTS voice name.

    Returns:
        The voice name used.

    Raises:
        TTSError: On API errors.
    """
    client = OpenAI(api_key=api_key)

    try:
        response = client.audio.speech.create(
            model=MODEL,
            voice=voice,  # type: ignore[arg-type]
            input=text,
        )
        response.stream_to_file(str(output_path))
    except OpenAIError as exc:
        raise TTSError(
            code="API_ERROR",
            message=f"OpenAI TTS API error: {exc}",
            details={"model": MODEL, "voice": voice},
        ) from exc

    return voice
