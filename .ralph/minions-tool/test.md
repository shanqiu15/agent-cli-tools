# Test & Verification Guide

## Setup

```bash
# From repo root — install all workspace packages in dev mode
uv sync
```

If a new package was added, it must be listed in the root `pyproject.toml` dev dependencies and `[tool.uv.sources]` section, then `uv sync` again.

For `browser_tool`, the `@playwright/cli` Node.js package must be installed:
```bash
npm install -g @playwright/cli@latest
```
This requires Node.js 18+. Verify installation with `playwright-cli --version`.

## Test Commands

### Run all unit tests (skip external API tests)
```bash
uv run pytest -q
```
Exit code 0 = pass. Any non-zero = failure.

### Run all tests including external API tests
```bash
uv run pytest -q --all
```
Requires env vars: `SERPER_API_KEY`, `CRAWL4AI_BASE_URL`, `PERPLEXITY_API_KEY`, `GOOGLE_API_KEY` as applicable.
Requires `playwright-cli` installed globally for browser_tool external tests.

### Run tests for a single package
```bash
uv run pytest packages/<tool_name>/tests/ -q
```

### Lint
```bash
uv run ruff check .
```
Exit code 0 = clean. Non-zero = lint violations found.

### Format check
```bash
uv run ruff format --check .
```
Exit code 0 = formatted. Non-zero = formatting needed.

### Type check
```bash
uv run mypy packages/<tool_name>/src/
```
Exit code 0 = no type errors.

## How to Interpret Pass/Fail

- **pytest**: Look at the summary line at the end. `X passed` means success. Any `FAILED` or `ERROR` lines indicate failure. Tests marked `external` are skipped by default — that's expected.
- **ruff check**: Lists files and line numbers with violations. Zero output = clean.
- **ruff format --check**: Lists files that would be reformatted. Zero output = clean.
- **mypy**: Reports type errors with file:line:col format. `Success: no issues found` = clean.

## Per-Story Verification

Each story's acceptance criteria reference specific commands. The evaluator should:

1. Run `uv sync` from repo root
2. Run `uv run pytest packages/<tool_name>/tests/ -q` for the relevant package
3. Run `uv run ruff check packages/<tool_name>/`
4. Run `uv run ruff format --check packages/<tool_name>/`
5. Run `uv run mypy packages/<tool_name>/src/`
6. Verify the CLI entrypoint works: `uv run <tool-name> --help`
7. Check that JSON output matches the `ToolResponse` envelope format

### browser_tool specific verification

Since `browser_tool` wraps `@playwright/cli` via subprocess (not Playwright Python):
- Unit tests mock `subprocess.run` and pass without Node.js or playwright-cli installed
- External tests (`--all`) require `playwright-cli` in PATH
- Verify the CLI detects missing `playwright-cli` gracefully: unset PATH to playwright-cli and run `uv run browser-tool navigate --url https://example.com` — should emit `PLAYWRIGHT_CLI_NOT_FOUND` error
