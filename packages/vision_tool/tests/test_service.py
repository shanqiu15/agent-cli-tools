"""Tests for the vision tool service layer."""

from unittest.mock import MagicMock, patch

import pytest

from vision_tool.errors import VisionError
from vision_tool.service import (
    _detect_mime,
    _download_image,
    _is_private_ip,
    analyze_image,
)

# Minimal valid PNG: 8-byte signature.
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 100
GIF_HEADER = b"GIF89a" + b"\x00" * 100
WEBP_HEADER = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 100


# --- MIME detection ---


def test_detect_mime_png() -> None:
    """PNG magic bytes are detected correctly."""
    assert _detect_mime(PNG_HEADER) == "image/png"


def test_detect_mime_jpeg() -> None:
    """JPEG magic bytes are detected correctly."""
    assert _detect_mime(JPEG_HEADER) == "image/jpeg"


def test_detect_mime_gif() -> None:
    """GIF89a magic bytes are detected correctly."""
    assert _detect_mime(GIF_HEADER) == "image/gif"


def test_detect_mime_webp() -> None:
    """WebP RIFF+WEBP magic bytes are detected correctly."""
    assert _detect_mime(WEBP_HEADER) == "image/webp"


def test_detect_mime_unsupported() -> None:
    """Unsupported format raises INVALID_INPUT."""
    with pytest.raises(VisionError) as exc_info:
        _detect_mime(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    assert exc_info.value.code == "INVALID_INPUT"


def test_detect_mime_too_small() -> None:
    """Data too small to detect raises INVALID_INPUT."""
    with pytest.raises(VisionError) as exc_info:
        _detect_mime(b"\x89P")
    assert exc_info.value.code == "INVALID_INPUT"


# --- File not found ---


def test_analyze_file_not_found() -> None:
    """Analyzing a non-existent file raises FILE_NOT_FOUND."""
    with pytest.raises(VisionError) as exc_info:
        analyze_image(
            image="/tmp/nonexistent_image_abc123.png",
            prompt="describe",
        )
    assert exc_info.value.code == "FILE_NOT_FOUND"


# --- Missing credentials ---


def test_analyze_missing_credentials(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing API key raises MISSING_CREDENTIALS."""
    import tempfile
    from pathlib import Path

    d = Path(tempfile.mkdtemp())
    img = d / "test.png"
    img.write_bytes(PNG_HEADER)

    # Clear any existing keys and config cache.
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("VISION_PROVIDER", raising=False)

    from cli_common.config import clear_cache

    clear_cache()

    with pytest.raises(VisionError) as exc_info:
        analyze_image(
            image=str(img),
            prompt="describe",
            provider="gemini",
            config_path="/tmp/nonexistent_config.yaml",
        )
    assert exc_info.value.code == "MISSING_CREDENTIALS"


# --- SSRF protection ---


@patch("vision_tool.service._is_private_ip", return_value=True)
def test_download_ssrf_blocked(mock_ip: MagicMock) -> None:
    """URLs resolving to private IPs are blocked."""
    with pytest.raises(VisionError) as exc_info:
        _download_image("http://169.254.169.254/metadata")
    assert exc_info.value.code == "SSRF_BLOCKED"


def test_is_private_ip_loopback() -> None:
    """Loopback address 127.0.0.1 is detected as private."""
    assert _is_private_ip("localhost") is True


# --- URL download with mocked httpx ---


@patch("vision_tool.service.httpx.stream")
def test_download_image_success(mock_stream: MagicMock) -> None:
    """Successful URL download returns image bytes."""
    mock_response = MagicMock()
    mock_response.headers = {"content-length": "100"}
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_bytes.return_value = [PNG_HEADER]
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_stream.return_value = mock_response

    data = _download_image("https://example.com/image.png")
    assert data == PNG_HEADER


# --- Local file analysis with mocked API ---


@patch("vision_tool.service.gemini.analyze")
def test_analyze_local_file_gemini(mock_gemini: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Local PNG analyzed via Gemini engine returns correct result."""
    import tempfile
    from pathlib import Path

    from cli_common.config import clear_cache

    clear_cache()

    d = Path(tempfile.mkdtemp())
    img = d / "test.png"
    img.write_bytes(PNG_HEADER)

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    monkeypatch.delenv("VISION_PROVIDER", raising=False)

    mock_gemini.return_value = ("A cat sitting on a mat", "gemini-2.0-flash")

    result = analyze_image(
        image=str(img),
        prompt="describe this",
        provider="gemini",
        config_path="/tmp/nonexistent_config.yaml",
    )
    assert result.analysis == "A cat sitting on a mat"
    assert result.provider == "gemini"
    assert result.model == "gemini-2.0-flash"

    mock_gemini.assert_called_once()
    call_args = mock_gemini.call_args
    assert call_args[0][2] == "describe this"
    assert call_args[0][3] == "test-key-123"


@patch("vision_tool.service.openai.analyze")
def test_analyze_local_file_openai(mock_openai: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Local PNG analyzed via OpenAI engine returns correct result."""
    import tempfile
    from pathlib import Path

    from cli_common.config import clear_cache

    clear_cache()

    d = Path(tempfile.mkdtemp())
    img = d / "test.png"
    img.write_bytes(PNG_HEADER)

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")

    mock_openai.return_value = ("A dog in a park", "gpt-4o-mini")

    result = analyze_image(
        image=str(img),
        prompt="what is this",
        provider="openai",
        config_path="/tmp/nonexistent_config.yaml",
    )
    assert result.analysis == "A dog in a park"
    assert result.provider == "openai"
    assert result.model == "gpt-4o-mini"


# --- Provider fallback / config cascade ---


@patch("vision_tool.service.gemini.analyze")
def test_provider_defaults_to_gemini(mock_gemini: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """When no provider is set, defaults to gemini."""
    import tempfile
    from pathlib import Path

    from cli_common.config import clear_cache

    clear_cache()

    d = Path(tempfile.mkdtemp())
    img = d / "test.png"
    img.write_bytes(PNG_HEADER)

    monkeypatch.delenv("VISION_PROVIDER", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    mock_gemini.return_value = ("result", "gemini-2.0-flash")

    result = analyze_image(
        image=str(img),
        prompt="describe",
        config_path="/tmp/nonexistent_config.yaml",
    )
    assert result.provider == "gemini"
    mock_gemini.assert_called_once()


@patch("vision_tool.service.openai.analyze")
def test_provider_env_var_override(mock_openai: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """VISION_PROVIDER env var overrides default."""
    import tempfile
    from pathlib import Path

    from cli_common.config import clear_cache

    clear_cache()

    d = Path(tempfile.mkdtemp())
    img = d / "test.png"
    img.write_bytes(PNG_HEADER)

    monkeypatch.setenv("VISION_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_openai.return_value = ("result", "gpt-4o-mini")

    result = analyze_image(
        image=str(img),
        prompt="describe",
        config_path="/tmp/nonexistent_config.yaml",
    )
    assert result.provider == "openai"
    mock_openai.assert_called_once()
