# Test Guide: add_more_tools

## Setup

```bash
# From repo root. Installs all workspace packages in editable mode.
uv sync
```

If a specific package fails to install (e.g., new dependencies), run:

```bash
uv pip install -e packages/<tool_name>
```

## Test Commands

### Run all tests for a specific tool

```bash
pytest packages/<tool_name>/tests -q
```

Replace `<tool_name>` with: `file_tool`, `todo_tool`, `vision_tool`,
`transcription_tool`, `tts_tool`, `skill_tool`.

### Run all new tool tests at once

```bash
pytest packages/file_tool packages/todo_tool packages/vision_tool packages/transcription_tool packages/tts_tool packages/skill_tool -q
```

### Run tests with external services (requires API keys)

```bash
pytest packages/<tool_name>/tests -q --all
```

The `--all` flag enables tests marked with `@pytest.mark.external` that hit
real APIs. Without it, those tests are automatically skipped.

## Lint and Type Checking

### Ruff (lint + format check)

```bash
# Lint a single package
ruff check packages/<tool_name>

# Lint all new packages
ruff check packages/file_tool packages/todo_tool packages/vision_tool packages/transcription_tool packages/tts_tool packages/skill_tool
```

Exit code 0 = pass. Any non-zero exit code means lint violations exist.

### Mypy (type checking)

```bash
# Type-check a single package
mypy packages/<tool_name>/src

# Type-check all new packages
mypy packages/file_tool/src packages/todo_tool/src packages/vision_tool/src packages/transcription_tool/src packages/tts_tool/src packages/skill_tool/src
```

Exit code 0 = pass. Mypy may report import errors for `cli_common` — these
are expected and suppressed by each package's `[tool.mypy.overrides]` in
`pyproject.toml` (set `ignore_missing_imports = true` for `cli_common.*`).

## CLI Smoke Tests

Each tool should respond to `--help`:

```bash
file-tool --help
todo-tool --help
vision-tool --help
transcription-tool --help
tts-tool --help
skill-tool --help
```

Exit code 0 and usage text printed = pass.

## How to Interpret Pass/Fail

### pytest

- **Exit code 0**: All tests passed.
- **Exit code 1**: One or more tests failed. Read the `FAILED` lines for
  specifics.
- **Exit code 5**: No tests were collected (missing test files or wrong path).
- Look for the summary line: `X passed, Y failed` at the end of output.

### ruff

- **Exit code 0**: No lint violations.
- **Non-zero**: Lists file:line violations. Fix them before proceeding.

### mypy

- **Exit code 0**: No type errors.
- **Non-zero**: Lists file:line type errors. Fix them before proceeding.
- Ignore notes about `cli_common` imports if the override is configured.

## Per-Story Verification

| Story | Command | Expected |
|-------|---------|----------|
| US-001 (file_tool) | `pytest packages/file_tool/tests -q` | >= 15 tests pass |
| US-001 (file_tool) | `ruff check packages/file_tool && mypy packages/file_tool/src` | Exit 0 |
| US-002 (todo_tool) | `pytest packages/todo_tool/tests -q` | >= 10 tests pass |
| US-002 (todo_tool) | `ruff check packages/todo_tool && mypy packages/todo_tool/src` | Exit 0 |
| US-003 (vision_tool) | `pytest packages/vision_tool/tests -q` | >= 10 tests pass |
| US-003 (vision_tool) | `ruff check packages/vision_tool && mypy packages/vision_tool/src` | Exit 0 |
| US-004 (transcription_tool) | `pytest packages/transcription_tool/tests -q` | >= 10 tests pass |
| US-004 (transcription_tool) | `ruff check packages/transcription_tool && mypy packages/transcription_tool/src` | Exit 0 |
| US-005 (tts_tool) | `pytest packages/tts_tool/tests -q` | >= 10 tests pass |
| US-005 (tts_tool) | `ruff check packages/tts_tool && mypy packages/tts_tool/src` | Exit 0 |
| US-006 (skill_tool) | `pytest packages/skill_tool/tests -q` | >= 15 tests pass |
| US-006 (skill_tool) | `ruff check packages/skill_tool && mypy packages/skill_tool/src` | Exit 0 |

## Environment Variables for External Tests

Tests marked `@pytest.mark.external` require these env vars:

| Tool | Env Vars Needed |
|------|----------------|
| vision_tool | `GOOGLE_API_KEY` (Gemini) or `OPENAI_API_KEY` (OpenAI) |
| transcription_tool | `GROQ_API_KEY` (Groq) or `OPENAI_API_KEY` (OpenAI) |
| tts_tool | `OPENAI_API_KEY` (OpenAI engine only; Edge TTS needs no key) |

Unit tests (default) mock all API calls and require no env vars.
