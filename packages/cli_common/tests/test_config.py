"""Tests for cli_common.config — config cascade loader."""

from pathlib import Path

import pytest

from cli_common.config import clear_cache, load_config
from cli_common.errors import ToolException


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    """Clear the config cache before each test."""
    clear_cache()


def test_config_file_present_with_matching_key(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("vision:\n  provider: gemini\n")
    result = load_config("vision", "provider", "VISION_PROVIDER", config_path=cfg)
    assert result == "gemini"


def test_config_file_present_key_missing_falls_back_to_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("vision:\n  provider: gemini\n")
    monkeypatch.setenv("GOOGLE_API_KEY", "from-env")
    result = load_config("vision", "google_api_key", "GOOGLE_API_KEY", config_path=cfg)
    assert result == "from-env"


def test_config_file_absent_falls_back_to_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VISION_PROVIDER", "openai")
    result = load_config(
        "vision",
        "provider",
        "VISION_PROVIDER",
        config_path="/nonexistent/path/config.yaml",
    )
    assert result == "openai"


def test_env_var_present_without_config_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TTS_VOICE", "en-US-AriaNeural")
    result = load_config(
        "tts",
        "voice",
        "TTS_VOICE",
        config_path="/nonexistent/path/config.yaml",
    )
    assert result == "en-US-AriaNeural"


def test_neither_config_nor_env_returns_default() -> None:
    result = load_config(
        "tts",
        "voice",
        "TTS_VOICE_NONEXISTENT_FOR_TEST",
        default="en-US-AriaNeural",
        config_path="/nonexistent/path/config.yaml",
    )
    assert result == "en-US-AriaNeural"


def test_neither_config_nor_env_nor_default_returns_none() -> None:
    result = load_config(
        "tts",
        "voice",
        "TTS_VOICE_NONEXISTENT_FOR_TEST",
        config_path="/nonexistent/path/config.yaml",
    )
    assert result is None


def test_invalid_yaml_raises_invalid_config(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(":\n  - :\n  bad: [unclosed\n")
    with pytest.raises(ToolException) as exc_info:
        load_config("vision", "provider", "VISION_PROVIDER", config_path=cfg)
    assert exc_info.value.code == "INVALID_CONFIG"
    assert "path" in exc_info.value.details


def test_config_file_overrides_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("vision:\n  provider: gemini\n")
    monkeypatch.setenv("VISION_PROVIDER", "openai")
    result = load_config("vision", "provider", "VISION_PROVIDER", config_path=cfg)
    assert result == "gemini"


def test_config_is_cached(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("vision:\n  provider: gemini\n")
    load_config("vision", "provider", "VISION_PROVIDER", config_path=cfg)
    # Overwrite the file — cached value should still be returned
    cfg.write_text("vision:\n  provider: openai\n")
    result = load_config("vision", "provider", "VISION_PROVIDER", config_path=cfg)
    assert result == "gemini"


def test_tool_config_path_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("transcription:\n  provider: groq\n")
    monkeypatch.setenv("TOOL_CONFIG_PATH", str(cfg))
    result = load_config("transcription", "provider", "TRANSCRIPTION_PROVIDER")
    assert result == "groq"


def test_non_dict_yaml_raises_invalid_config(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("- item1\n- item2\n")
    with pytest.raises(ToolException) as exc_info:
        load_config("vision", "provider", "VISION_PROVIDER", config_path=cfg)
    assert exc_info.value.code == "INVALID_CONFIG"


def test_tool_section_not_a_dict_falls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("vision: not-a-dict\n")
    monkeypatch.setenv("VISION_PROVIDER", "openai")
    result = load_config("vision", "provider", "VISION_PROVIDER", config_path=cfg)
    assert result == "openai"
