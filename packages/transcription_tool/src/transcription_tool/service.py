"""Business logic for audio transcription."""

from pathlib import Path

from cli_common.config import load_config

from transcription_tool.engines import groq, openai
from transcription_tool.errors import TranscriptionError
from transcription_tool.models import TranscribeResult

DEFAULT_PROVIDER = "groq"
VALID_PROVIDERS = ("groq", "openai")
VALID_EXTENSIONS = {"mp3", "wav", "ogg", "m4a", "webm", "flac"}
MAX_FILE_BYTES = 25 * 1024 * 1024  # 25 MB


def _validate_audio_file(file_path: Path) -> None:
    """Validate that the audio file exists, is a file, has a valid extension, and is under size limit.

    Args:
        file_path: Path to the audio file.

    Raises:
        TranscriptionError: On validation failure.
    """
    if not file_path.exists():
        raise TranscriptionError(
            code="FILE_NOT_FOUND",
            message=f"Audio file not found: {file_path}",
            details={"path": str(file_path)},
        )

    if not file_path.is_file():
        raise TranscriptionError(
            code="INVALID_INPUT",
            message=f"Path is not a file: {file_path}",
            details={"path": str(file_path)},
        )

    ext = file_path.suffix.lstrip(".").lower()
    if ext not in VALID_EXTENSIONS:
        raise TranscriptionError(
            code="INVALID_INPUT",
            message=f"Unsupported audio format '.{ext}'; expected one of: {', '.join(sorted(VALID_EXTENSIONS))}",
            details={"path": str(file_path), "extension": ext},
        )

    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_BYTES:
        raise TranscriptionError(
            code="FILE_TOO_LARGE",
            message=f"Audio file exceeds {MAX_FILE_BYTES // (1024 * 1024)}MB size limit",
            details={"path": str(file_path), "size_bytes": file_size},
        )


def _resolve_provider(config_path: str | None = None) -> str:
    """Resolve which provider to use via the config cascade."""
    provider = load_config(
        tool_name="transcription",
        key="provider",
        env_var="TRANSCRIPTION_PROVIDER",
        default=DEFAULT_PROVIDER,
        config_path=config_path,
    )
    if provider not in VALID_PROVIDERS:
        raise TranscriptionError(
            code="INVALID_INPUT",
            message=f"Unknown provider '{provider}'; choose from: {', '.join(VALID_PROVIDERS)}",
            details={"provider": provider},
        )
    return str(provider)


def _get_api_key(provider: str, config_path: str | None = None) -> str:
    """Get the API key for the given provider.

    Args:
        provider: Provider name (groq or openai).
        config_path: Optional config file path override.

    Returns:
        The API key string.

    Raises:
        TranscriptionError: If the key is not found.
    """
    if provider == "groq":
        key = load_config(
            tool_name="transcription",
            key="groq_api_key",
            env_var="GROQ_API_KEY",
            config_path=config_path,
        )
        env_name = "GROQ_API_KEY"
    else:
        key = load_config(
            tool_name="transcription",
            key="openai_api_key",
            env_var="OPENAI_API_KEY",
            config_path=config_path,
        )
        env_name = "OPENAI_API_KEY"

    if not key:
        raise TranscriptionError(
            code="MISSING_CREDENTIALS",
            message=f"API key not found for provider '{provider}'; set {env_name} or configure in tool_config.yaml",
            details={"provider": provider, "env_var": env_name},
        )
    return str(key)


def transcribe_audio(
    file: str,
    provider: str | None = None,
    config_path: str | None = None,
) -> TranscribeResult:
    """Transcribe an audio file using a speech-to-text provider.

    Args:
        file: Path to the audio file.
        provider: Explicit provider override (groq or openai).
        config_path: Optional config file path override.

    Returns:
        TranscribeResult with transcript text, provider, and model.

    Raises:
        TranscriptionError: On invalid input, missing credentials, or API errors.
    """
    file_path = Path(file)

    # Validate the audio file.
    _validate_audio_file(file_path)

    # Determine provider.
    if provider is not None:
        if provider not in VALID_PROVIDERS:
            raise TranscriptionError(
                code="INVALID_INPUT",
                message=f"Unknown provider '{provider}'; choose from: {', '.join(VALID_PROVIDERS)}",
                details={"provider": provider},
            )
        resolved_provider = provider
    else:
        resolved_provider = _resolve_provider(config_path=config_path)

    # Get API key.
    api_key = _get_api_key(resolved_provider, config_path=config_path)

    # Dispatch to engine.
    if resolved_provider == "groq":
        transcript_text, model_name = groq.transcribe(file_path, api_key)
    else:
        transcript_text, model_name = openai.transcribe(file_path, api_key)

    return TranscribeResult(
        transcript=transcript_text,
        provider=resolved_provider,
        model=model_name,
    )
