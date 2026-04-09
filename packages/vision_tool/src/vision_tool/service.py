"""Business logic for vision analysis."""

import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx

from cli_common.config import load_config

from vision_tool.engines import gemini, openai
from vision_tool.errors import VisionError
from vision_tool.models import AnalyzeResult

DEFAULT_PROVIDER = "gemini"
VALID_PROVIDERS = ("gemini", "openai")
MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

# Magic byte signatures for supported image formats.
_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"RIFF", "image/webp"),  # WebP starts with RIFF...WEBP; checked further below
]


def _detect_mime(data: bytes) -> str:
    """Detect MIME type from magic bytes.

    Args:
        data: Raw image bytes (at least first 12 bytes needed).

    Returns:
        MIME type string.

    Raises:
        VisionError: If the format is not supported.
    """
    if len(data) < 4:
        raise VisionError(
            code="INVALID_INPUT",
            message="Image data too small to detect format",
        )

    for magic, mime in _MAGIC_SIGNATURES:
        if data[: len(magic)] == magic:
            # Extra check for WebP: bytes 8-12 must be "WEBP"
            if mime == "image/webp":
                if len(data) >= 12 and data[8:12] == b"WEBP":
                    return mime
                continue
            return mime

    raise VisionError(
        code="INVALID_INPUT",
        message="Unsupported image format; expected PNG, JPEG, GIF, or WebP",
    )


def _is_private_ip(hostname: str) -> bool:
    """Check if a hostname resolves to a private, loopback, or link-local IP.

    Args:
        hostname: The hostname to check.

    Returns:
        True if the resolved IP is private/loopback/link-local.
    """
    try:
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return False  # Let httpx handle DNS failures

    for family, _, _, _, sockaddr in results:
        ip_str = sockaddr[0]
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            return True
    return False


def _download_image(url: str) -> bytes:
    """Download an image from a URL with SSRF protection and size limit.

    Args:
        url: The URL to download.

    Returns:
        Raw image bytes.

    Raises:
        VisionError: On SSRF, size limit, or download errors.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise VisionError(
            code="INVALID_INPUT",
            message="Invalid URL: no hostname",
            details={"url": url},
        )

    if _is_private_ip(hostname):
        raise VisionError(
            code="SSRF_BLOCKED",
            message="URL points to a private, loopback, or link-local address",
            details={"url": url, "hostname": hostname},
        )

    try:
        with httpx.stream("GET", url, timeout=30.0, follow_redirects=True) as response:
            response.raise_for_status()

            # Check Content-Length header first if available.
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                raise VisionError(
                    code="INVALID_INPUT",
                    message=f"Image exceeds {MAX_DOWNLOAD_BYTES // (1024 * 1024)}MB size limit",
                    details={"url": url, "content_length": int(content_length)},
                )

            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes(chunk_size=65536):
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise VisionError(
                        code="INVALID_INPUT",
                        message=f"Image exceeds {MAX_DOWNLOAD_BYTES // (1024 * 1024)}MB size limit",
                        details={"url": url},
                    )
                chunks.append(chunk)

    except VisionError:
        raise
    except httpx.TimeoutException as exc:
        raise VisionError(
            code="TIMEOUT",
            message=f"Timed out downloading image from {url}",
            details={"url": url},
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise VisionError(
            code="HTTP_ERROR",
            message=f"HTTP {exc.response.status_code} downloading {url}",
            details={"url": url, "status_code": exc.response.status_code},
        ) from exc
    except httpx.HTTPError as exc:
        raise VisionError(
            code="HTTP_ERROR",
            message=f"Error downloading image: {exc}",
            details={"url": url},
        ) from exc

    return b"".join(chunks)


def _resolve_provider(config_path: str | None = None) -> str:
    """Resolve which provider to use via the config cascade."""
    provider = load_config(
        tool_name="vision",
        key="provider",
        env_var="VISION_PROVIDER",
        default=DEFAULT_PROVIDER,
        config_path=config_path,
    )
    if provider not in VALID_PROVIDERS:
        raise VisionError(
            code="INVALID_INPUT",
            message=f"Unknown provider '{provider}'; choose from: {', '.join(VALID_PROVIDERS)}",
            details={"provider": provider},
        )
    return str(provider)


def _get_api_key(provider: str, config_path: str | None = None) -> str:
    """Get the API key for the given provider.

    Args:
        provider: Provider name (gemini or openai).
        config_path: Optional config file path override.

    Returns:
        The API key string.

    Raises:
        VisionError: If the key is not found.
    """
    if provider == "gemini":
        key = load_config(
            tool_name="vision",
            key="google_api_key",
            env_var="GOOGLE_API_KEY",
            config_path=config_path,
        )
        env_name = "GOOGLE_API_KEY"
    else:
        key = load_config(
            tool_name="vision",
            key="openai_api_key",
            env_var="OPENAI_API_KEY",
            config_path=config_path,
        )
        env_name = "OPENAI_API_KEY"

    if not key:
        raise VisionError(
            code="MISSING_CREDENTIALS",
            message=f"API key not found for provider '{provider}'; set {env_name} or configure in tool_config.yaml",
            details={"provider": provider, "env_var": env_name},
        )
    return str(key)


def analyze_image(
    image: str,
    prompt: str,
    provider: str | None = None,
    config_path: str | None = None,
) -> AnalyzeResult:
    """Analyze an image using a vision model.

    Args:
        image: Local file path or URL to an image.
        prompt: Question or instruction for the vision model.
        provider: Explicit provider override (gemini or openai).
        config_path: Optional config file path override.

    Returns:
        AnalyzeResult with analysis text, provider, and model.

    Raises:
        VisionError: On invalid input, missing credentials, or API errors.
    """
    # Determine provider.
    if provider is not None:
        if provider not in VALID_PROVIDERS:
            raise VisionError(
                code="INVALID_INPUT",
                message=f"Unknown provider '{provider}'; choose from: {', '.join(VALID_PROVIDERS)}",
                details={"provider": provider},
            )
        resolved_provider = provider
    else:
        resolved_provider = _resolve_provider(config_path=config_path)

    # Load image bytes.
    is_url = image.startswith("http://") or image.startswith("https://")
    if is_url:
        image_bytes = _download_image(image)
    else:
        path = Path(image)
        if not path.exists():
            raise VisionError(
                code="FILE_NOT_FOUND",
                message=f"Image file not found: {image}",
                details={"path": image},
            )
        try:
            image_bytes = path.read_bytes()
        except OSError as exc:
            raise VisionError(
                code="FILE_READ_ERROR",
                message=f"Could not read image file: {exc}",
                details={"path": image},
            ) from exc

    # Detect MIME type.
    mime_type = _detect_mime(image_bytes)

    # Get API key.
    api_key = _get_api_key(resolved_provider, config_path=config_path)

    # Dispatch to engine.
    if resolved_provider == "gemini":
        analysis_text, model_name = gemini.analyze(image_bytes, mime_type, prompt, api_key)
    else:
        analysis_text, model_name = openai.analyze(image_bytes, mime_type, prompt, api_key)

    return AnalyzeResult(
        analysis=analysis_text,
        provider=resolved_provider,
        model=model_name,
    )
