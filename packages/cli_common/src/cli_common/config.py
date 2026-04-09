"""Shared config-file loading utility for provider-based tools.

Implements a three-tier cascade: tool_config.yaml > environment variable > default.
"""

import os
from pathlib import Path
from typing import Any

import yaml

from cli_common.errors import ToolException

_DEFAULT_CONFIG_PATH = Path.home() / ".config" / "agent-cli-tools" / "tool_config.yaml"

_cached_config: dict[str, Any] | None = None
_cached_config_path: str | None = None


def _resolve_config_path(config_path: str | Path | None = None) -> Path:
    """Determine which config file path to use."""
    if config_path is not None:
        return Path(config_path)
    env_path = os.environ.get("TOOL_CONFIG_PATH")
    if env_path is not None:
        return Path(env_path)
    return _DEFAULT_CONFIG_PATH


def _load_yaml(path: Path) -> dict[str, Any]:
    """Read and parse a YAML config file. Raises on invalid YAML."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ToolException(
            code="INVALID_CONFIG",
            message=f"Invalid YAML in config file: {path}",
            details={"path": str(path), "error": str(exc)},
        ) from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ToolException(
            code="INVALID_CONFIG",
            message=f"Config file must be a YAML mapping, got {type(data).__name__}",
            details={"path": str(path)},
        )
    return data


def _get_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Return the parsed config, caching after the first read."""
    global _cached_config, _cached_config_path  # noqa: PLW0603
    resolved = str(_resolve_config_path(config_path))
    if _cached_config is not None and _cached_config_path == resolved:
        return _cached_config
    path = Path(resolved)
    if not path.exists():
        data: dict[str, Any] = {}
    else:
        data = _load_yaml(path)
    _cached_config = data
    _cached_config_path = resolved
    return data


def load_config(
    tool_name: str,
    key: str,
    env_var: str,
    default: Any = None,
    *,
    config_path: str | Path | None = None,
) -> Any:
    """Resolve a config value through the three-tier cascade.

    1. Look up ``tool_name.key`` in the YAML config file.
    2. Fall back to ``os.environ.get(env_var)``.
    3. Fall back to *default* (may be ``None`` to signal a required value).

    Parameters
    ----------
    tool_name:
        Top-level key in the YAML config (e.g. ``"vision"``).
    key:
        Nested key under *tool_name* (e.g. ``"provider"``).
    env_var:
        Environment variable name to check as tier 2.
    default:
        Hardcoded fallback. ``None`` means the value is required (caller
        should raise ``MISSING_CREDENTIALS`` or similar when appropriate).
    config_path:
        Override the config file path (useful for testing).
    """
    config = _get_config(config_path)
    tool_section = config.get(tool_name)
    if isinstance(tool_section, dict):
        value = tool_section.get(key)
        if value is not None:
            return value

    env_value = os.environ.get(env_var)
    if env_value is not None:
        return env_value

    return default


def clear_cache() -> None:
    """Reset the cached config. Useful for testing."""
    global _cached_config, _cached_config_path  # noqa: PLW0603
    _cached_config = None
    _cached_config_path = None
