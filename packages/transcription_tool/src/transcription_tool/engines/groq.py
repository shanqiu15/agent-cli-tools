"""Groq Whisper transcription engine (OpenAI-compatible endpoint)."""

from pathlib import Path

from openai import OpenAI, OpenAIError

from transcription_tool.errors import TranscriptionError

MODEL = "whisper-large-v3"
BASE_URL = "https://api.groq.com/openai/v1"


def transcribe(file_path: Path, api_key: str) -> tuple[str, str]:
    """Transcribe an audio file using the Groq Whisper API.

    Args:
        file_path: Path to the audio file.
        api_key: Groq API key.

    Returns:
        Tuple of (transcript_text, model_name).

    Raises:
        TranscriptionError: On API errors.
    """
    client = OpenAI(api_key=api_key, base_url=BASE_URL)

    try:
        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=MODEL,
                file=audio_file,
            )
    except OpenAIError as exc:
        raise TranscriptionError(
            code="API_ERROR",
            message=f"Groq API error: {exc}",
            details={"model": MODEL},
        ) from exc

    return response.text, MODEL
