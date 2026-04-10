# Plan: Add More CLI Tools

## Summary

Implement six new CLI tool packages (`file_tool`, `todo_tool`, `vision_tool`,
`transcription_tool`, `tts_tool`, `skill_tool`) following the established
patterns in this monorepo. Each package is standalone, independently-installable
under `packages/`, outputs JSON via `cli_common`, uses typer for CLI and pydantic
for models. The `cli_common` config cascade loader (US-000) is already landed, so
provider-based tools can use it immediately.

## Approach

### Package scaffold (identical for every tool)

1. Create `packages/<name>/pyproject.toml` — depends on `cli-common`, `pydantic>=2.0`,
   `typer>=0.9`, plus any tool-specific deps.
2. Create `src/<name>/` with `__init__.py`, `cli.py`, `models.py`, `service.py`,
   `errors.py`.
3. Create `tests/` with `__init__.py`, `test_cli.py`, `test_service.py`.
4. Wire entry point: `[project.scripts] <tool-name> = "<tool_name>.cli:app"`.

### Architecture per tool

- **cli.py**: Thin wiring. Parses args via typer `Option`s, calls service function,
  emits JSON via `emit_success`/`emit_error`. Input validation at boundary.
- **service.py**: All business logic. Pure functions with type hints. Raises
  tool-specific exceptions. No stdout writes.
- **models.py**: Pydantic `BaseModel` with `Field(description=...)` on every field.
- **errors.py**: Single `<Tool>Error(ToolException)` subclass with structured codes.

### Multi-provider tools (vision, transcription, tts)

Use the existing `cli_common.config.load_config()` three-tier cascade
(tool_config.yaml > env var > default) for provider selection and API keys.
Each provider lives in an `engines/` subpackage as a standalone module.
The service dispatcher selects the engine based on config, with fallback logic
when the preferred engine lacks credentials and the user didn't explicitly
choose it.

### Implementation order

1. **file_tool** — foundational, no external deps, exercises safety-guard patterns
2. **todo_tool** — simple CRUD, validates the JSON-file persistence pattern
3. **vision_tool** — first multi-provider tool with external APIs
4. **transcription_tool** — same provider pattern, OpenAI-compatible API
5. **tts_tool** — introduces `edge-tts` (free) + OpenAI TTS
6. **skill_tool** — most complex: YAML frontmatter + CRUD + filesystem structure

Each tool is fully independent. The order is progressive complexity, not a
hard dependency chain.

## Constraints

- **No package-to-package dependencies.** Tools only depend on `cli_common`.
- **No interactive prompts.** Agent-first: JSON in, JSON out.
- **No decorative output.** No emojis, colors, or banners on stdout.
- **Local-only for file_tool, todo_tool, skill_tool.** No remote backend abstraction.
- **Skip heavyweight local providers.** No faster-whisper, no local NeuTTS.
- **Do not modify existing packages.** This is additive work only.
- **Minimal cli_common changes.** The config cascade is already landed. Only add
  shared utilities if genuinely reused by multiple new tools.
- **Follow existing conventions exactly.** Match the patterns in bash_tool, ocr_tool,
  web_search_tool for CLI wiring, error handling, and test structure.

## Dependencies

- All new tools depend on `cli_common` (exists).
- `vision_tool`: `httpx`, `google-generativeai` (optional), `openai` (optional).
- `transcription_tool`: `httpx`, `openai`.
- `tts_tool`: `edge-tts`, `openai`.
- `skill_tool`: `pyyaml>=6.0`.
- `file_tool`, `todo_tool`: no deps beyond `cli_common`/`typer`/`pydantic`.

## Risks

| Risk | Mitigation |
|------|------------|
| file_tool safety guards are security-sensitive | Use `os.path.realpath()` for all resolution; maintain explicit deny-lists; test every safety path |
| Edge TTS is unofficial Microsoft API | Keep as one option; OpenAI TTS is the paid fallback |
| Provider SDK version conflicts | Pin conservatively in each tool's pyproject.toml |
| skill_tool YAML parsing fragility | `yaml.safe_load()` only; validate required fields; test malformed input |
| Large scope (6 tools) may drift from conventions | Each story's AC requires lint + type-check + tests passing before moving on |
| todo_tool persistence dir may not exist | Create parent dirs on first write; accept `--data-dir` override |
