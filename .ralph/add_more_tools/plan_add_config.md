# Plan: Add More CLI Tools

## Summary

Implement six new CLI tool packages (`file_tool`, `todo_tool`, `vision_tool`,
`transcription_tool`, `tts_tool`, `skill_tool`) following the established
patterns in this monorepo. Each tool is a standalone, independently-installable
package under `packages/` that outputs JSON, uses typer for CLI, pydantic for
models, and integrates with `cli_common` for shared error/response handling.

Additionally, add a shared config-file loading utility to `cli_common` so that
tools with external providers resolve configuration via a three-tier cascade:
**tool_config.yaml > environment variable > hardcoded default**.

## Approach

Each tool follows the same implementation pattern:

1. **Scaffold** the package directory: `pyproject.toml`, `src/<name>/`, `tests/`
2. **Define models** (pydantic) for all inputs/outputs
3. **Implement service layer** with pure functions, raising `ToolException` subclasses
4. **Wire CLI** via typer commands that call service functions and emit JSON
5. **Write tests**: unit tests for service, CLI smoke tests, and e2e tests
6. **Register** the package in root `pyproject.toml` dev dependencies and `uv.sources`

### Architecture per tool

- `cli.py`: Thin wiring layer. Parses args via typer, calls service, emits JSON via `emit_success`/`emit_error`.
- `service.py`: All business logic. Pure functions with type hints. Raises tool-specific exceptions.
- `models.py`: Pydantic `BaseModel` classes with `Field(description=...)` on every field.
- `errors.py`: Subclass of `cli_common.errors.ToolException` with structured error codes.

### Configuration cascade (vision, transcription, tts)

Tools that call external APIs resolve every configurable value through a
three-tier cascade implemented in `cli_common`:

1. **Config file** (`tool_config.yaml`): Looked up at a well-known path
   (`~/.config/agent-cli-tools/tool_config.yaml`). The file is optional; if it
   does not exist, the loader silently moves to the next tier. The file is
   standard YAML with top-level keys per tool:

   ```yaml
   vision:
     provider: gemini
     google_api_key: sk-...
     openai_api_key: sk-...
   transcription:
     provider: groq
     groq_api_key: gsk_...
     openai_api_key: sk-...
   tts:
     provider: edge
     openai_api_key: sk-...
     voice: en-US-AriaNeural
   ```

2. **Environment variable**: If the attribute is not present in the config file
   (or the file itself is absent), fall back to the corresponding env var
   (e.g., `VISION_PROVIDER`, `GOOGLE_API_KEY`).

3. **Hardcoded default**: If neither the config file nor the env var provides a
   value, use the tool's built-in default (e.g., `gemini` for vision, `edge`
   for TTS). API keys have no default -- a missing key at all tiers raises
   `MISSING_CREDENTIALS`.

The cascade is implemented as a shared helper in `cli_common` so every
provider-based tool uses the exact same resolution logic. This avoids
duplicating config-loading code across vision, transcription, and TTS tools.

The `--config` CLI option can override the config file path for testing.

### Implementation order

1. **cli_common config** -- add `config.py` to `cli_common` with the cascade loader (prerequisite for provider tools)
2. **file_tool** -- foundational filesystem operations, no external deps
3. **todo_tool** -- simple JSON-file-backed CRUD, validates pattern adherence
4. **vision_tool** -- first tool with multi-provider external API integration (uses config cascade)
5. **transcription_tool** -- similar provider pattern to vision
6. **tts_tool** -- introduces edge-tts (free, no API key) + OpenAI TTS
7. **skill_tool** -- most complex: CRUD + YAML frontmatter + filesystem structure

Each tool is fully independent (no cross-tool dependencies), so the order is
a recommendation for progressive complexity, not a hard dependency chain.
The cli_common config addition must land first since provider tools depend on it.

## Constraints

- **No package-to-package dependencies.** Tools only depend on `cli_common`.
- **Config via cascade.** Provider tools read `tool_config.yaml` first, then env vars, then defaults. Non-provider tools (file, todo, skill) use env vars or CLI options only.
- **No interactive prompts.** Agent-first: JSON in, JSON out.
- **No decorative output.** No emojis, colors, or banners on stdout.
- **Local-only for file_tool, todo_tool, skill_tool.** No remote backend abstraction.
- **Skip local/heavyweight providers.** No faster-whisper (model download), no local NeuTTS. Stick to API-based and edge-tts.
- **Minimal cli_common changes.** Only add the config cascade loader (`config.py`) and its tests. Do not modify existing cli_common modules.
- **Do not modify existing packages.** This is additive work only.

## Dependencies

- All tools depend on `cli_common` (already exists).
- `cli_common` needs `pyyaml>=6.0` added as a dependency (for the config loader).
- `vision_tool` needs `httpx` (already in workspace via `web_search_tool`) and optionally `google-generativeai` SDK.
- `transcription_tool` needs `httpx` and `openai` SDK.
- `tts_tool` needs `edge-tts` package and `openai` SDK.
- `skill_tool` needs `pyyaml>=6.0` (already available transitively via cli_common, but declared explicitly).
- No tool depends on another new tool.

## Risks

| Risk | Mitigation |
|------|------------|
| file_tool safety guards are security-sensitive (path traversal, device paths) | Use `os.path.realpath()` for all path resolution; maintain explicit deny-lists; test all safety paths |
| Edge TTS is an unofficial Microsoft API; may break | Keep it as one provider option, not the only one; OpenAI TTS is the paid fallback |
| Vision/transcription provider SDKs may have version conflicts | Pin SDK versions conservatively in each tool's pyproject.toml; workspace constraints handle conflicts |
| skill_tool YAML frontmatter parsing can be fragile | Use `yaml.safe_load()` only; validate required fields explicitly; test malformed YAML |
| Large scope (6 tools + cli_common change) may lead to inconsistency | Implement in order; each tool's tests must pass before starting the next; follow existing patterns exactly |
| todo_tool persistence file location (`~/.local/share/`) may not exist on all systems | Create parent directories on first write; accept `--data-dir` override for testing |
| Config file adds a new shared dependency (pyyaml) to cli_common | pyyaml is stable and widely used; pin `>=6.0`; use `yaml.safe_load()` only (no unsafe load) |
| Config file may contain secrets (API keys) | Document that the file should have restrictive permissions; do not log config values; do not include in JSON output |

## Changes

- **Added config cascade pattern.** Per reviewer feedback, provider tools now resolve config through `tool_config.yaml` > env var > default, instead of env vars only. Added a new `config.py` module to `cli_common` as the shared implementation.
- **Removed "No config files" constraint.** Replaced with "Config via cascade" to reflect the new pattern.
- **Updated implementation order.** `cli_common` config addition is now step 1 (prerequisite for provider tools).
- **Added pyyaml dependency.** `cli_common` now depends on `pyyaml>=6.0` for YAML parsing of the config file.
- **Config file location.** `~/.config/agent-cli-tools/tool_config.yaml` (follows XDG conventions). Overridable via `--config` CLI option for testing.
- **Updated dependencies section** to reflect the new pyyaml requirement in cli_common.
- **Added risk entry** for secrets in config file and pyyaml dependency.
