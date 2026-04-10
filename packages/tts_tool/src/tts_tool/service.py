"""Business logic for text-to-speech generation."""

import tempfile
from pathlib import Path

from cli_common.config import load_config

from tts_tool.engines import edge, openai
from tts_tool.errors import TTSError
from tts_tool.models import SpeakResult

DEFAULT_PROVIDER = "edge"
VALID_PROVIDERS = ("edge", "openai")
MAX_TEXT_LENGTH = 4000


def _validate_text(text: str) -> None:
    """Validate that the input text is non-empty and within length limits.

    Args:
        text: The text to validate.

    Raises:
        TTSError: On validation failure.
    """
    if not text or not text.strip():
        raise TTSError(
            code="INVALID_INPUT",
            message="Text must not be empty",
        )

    if len(text) > MAX_TEXT_LENGTH:
        raise TTSError(
            code="INVALID_INPUT",
            message=f"Text exceeds {MAX_TEXT_LENGTH} character limit ({len(text)} characters)",
            details={"length": len(text), "max_length": MAX_TEXT_LENGTH},
        )


def _resolve_provider(config_path: str | None = None) -> str:
    """Resolve which provider to use via the config cascade."""
    provider = load_config(
        tool_name="tts",
        key="provider",
        env_var="TTS_PROVIDER",
        default=DEFAULT_PROVIDER,
        config_path=config_path,
    )
    if provider not in VALID_PROVIDERS:
        raise TTSError(
            code="INVALID_INPUT",
            message=f"Unknown provider '{provider}'; choose from: {', '.join(VALID_PROVIDERS)}",
            details={"provider": provider},
        )
    return str(provider)


def _resolve_voice(provider: str, voice: str | None = None, config_path: str | None = None) -> str:
    """Resolve which voice to use.

    Priority: explicit --voice arg > config cascade > provider default.

    Args:
        provider: The resolved provider name.
        voice: Explicit voice override from CLI.
        config_path: Optional config file path override.

    Returns:
        The voice name to use.
    """
    if voice is not None:
        return voice

    config_voice = load_config(
        tool_name="tts",
        key="voice",
        env_var="TTS_VOICE",
        config_path=config_path,
    )
    if config_voice:
        return str(config_voice)

    if provider == "openai":
        return openai.DEFAULT_VOICE
    return edge.DEFAULT_VOICE


def _get_api_key(config_path: str | None = None) -> str:
    """Get the OpenAI API key for TTS.

    Args:
        config_path: Optional config file path override.

    Returns:
        The API key string.

    Raises:
        TTSError: If the key is not found.
    """
    key = load_config(
        tool_name="tts",
        key="openai_api_key",
        env_var="OPENAI_API_KEY",
        config_path=config_path,
    )
    if not key:
        raise TTSError(
            code="MISSING_CREDENTIALS",
            message="API key not found for provider 'openai'; set OPENAI_API_KEY or configure in tool_config.yaml",
            details={"provider": "openai", "env_var": "OPENAI_API_KEY"},
        )
    return str(key)


def _resolve_output_path(output: str | None) -> Path:
    """Resolve the output file path.

    If output is None, generates a temp file path.

    Args:
        output: Explicit output path or None.

    Returns:
        The resolved output Path.
    """
    if output is not None:
        return Path(output)

    tmp_dir = Path(tempfile.gettempdir()) / "tts_tool"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(suffix=".mp3", dir=str(tmp_dir))
    # Close the fd; the engine will write to the path.
    import os

    os.close(fd)
    return Path(tmp_path)


def speak_text(
    text: str,
    output: str | None = None,
    provider: str | None = None,
    voice: str | None = None,
    config_path: str | None = None,
) -> SpeakResult:
    """Convert text to speech using the configured provider.

    Args:
        text: The text to convert to speech.
        output: Optional output file path. If None, a temp file is created.
        provider: Explicit provider override (edge or openai).
        voice: Explicit voice override.
        config_path: Optional config file path override.

    Returns:
        SpeakResult with file_path, provider, and voice.

    Raises:
        TTSError: On invalid input, missing credentials, or API errors.
    """
    # Validate input text.
    _validate_text(text)

    # Determine provider.
    if provider is not None:
        if provider not in VALID_PROVIDERS:
            raise TTSError(
                code="INVALID_INPUT",
                message=f"Unknown provider '{provider}'; choose from: {', '.join(VALID_PROVIDERS)}",
                details={"provider": provider},
            )
        resolved_provider = provider
    else:
        resolved_provider = _resolve_provider(config_path=config_path)

    # Resolve voice.
    resolved_voice = _resolve_voice(resolved_provider, voice=voice, config_path=config_path)

    # Resolve output path.
    output_path = _resolve_output_path(output)

    # Dispatch to engine.
    if resolved_provider == "edge":
        used_voice = edge.speak(text, output_path, voice=resolved_voice)
    else:
        api_key = _get_api_key(config_path=config_path)
        used_voice = openai.speak(text, output_path, api_key=api_key, voice=resolved_voice)

    return SpeakResult(
        file_path=str(output_path),
        provider=resolved_provider,
        voice=used_voice,
    )
