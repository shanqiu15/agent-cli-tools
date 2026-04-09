# Testing

## Quick Reference

```bash
uv run pytest                                      # all tests, skip external
uv run pytest --all                                # all tests, include external
uv run pytest packages/bash_tool                   # single package
uv run pytest packages/*/tests/test_e2e_*.py       # all e2e tests only
uv run pytest -k "test_echo"                       # match by name
uv run pytest -v                                   # verbose output
```

## Test Categories

### Unit Tests (`test_service.py`, `test_cli.py`, `test_models.py`)

Test business logic and CLI argument handling using mocks. No network calls, no external dependencies. Always run.

```bash
uv run pytest packages/bash_tool/tests/test_service.py
uv run pytest packages/memory_tool/tests/test_cli.py
```

### E2E Tests (`test_e2e_<tool>.py`)

Test real tool behavior end-to-end through the CLI interface. Split into two groups:

**Local e2e tests** run without any external services:
- `bash_tool` — executes real shell commands
- `memory_tool` — writes/reads real files (uses `tmp_path`)
- `ocr_tool` — runs easyocr against a test image
- `browser_tool` — checks CLI arg handling (full browser tests are external)
- `cron_tool` — validates schedule parsing (HTTP calls are external)
- `image_gen_tool` — validates input (API calls are external)
- `sonar_tool` — validates input (API calls are external)
- `web_search_tool` — validates input (API calls are external)
- `web_crawl_tool` — validates URL format (HTTP calls are external)

**External e2e tests** (`@pytest.mark.external`) call real APIs and are skipped by default:

| Test | Required Env Var |
|------|-----------------|
| `web_search_tool` | `SERPER_API_KEY` |
| `web_crawl_tool` | *(network access)* |
| `sonar_tool` | `PERPLEXITY_API_KEY` |
| `image_gen_tool` | `GOOGLE_API_KEY` |
| `ocr_tool` (google) | `GOOGLE_CLOUD_VISION_API_KEY` |
| `browser_tool` | `playwright-cli` binary in PATH |

To run external tests:

```bash
# All external tests
uv run pytest --all

# Single package with external tests
uv run pytest packages/web_search_tool/tests/test_e2e_web_search_tool.py --all
```

## Running Tests by Package

```bash
uv run pytest packages/bash_tool
uv run pytest packages/browser_tool
uv run pytest packages/cli_common
uv run pytest packages/cron_tool
uv run pytest packages/image_gen_tool
uv run pytest packages/memory_tool
uv run pytest packages/ocr_tool
uv run pytest packages/sonar_tool
uv run pytest packages/web_crawl_tool
uv run pytest packages/web_search_tool
```

## Configuration

- **Root pytest config:** `pyproject.toml` — sets `--import-mode=importlib` for monorepo compatibility
- **`--all` flag:** defined in root `conftest.py`, controls `@pytest.mark.external` skip behavior
- **Marker registration:** `external` marker registered in root `pyproject.toml`

## Linting and Type Checking

```bash
uv run ruff check                # lint
uv run ruff format --check       # format check
uv run mypy                      # type check
```
