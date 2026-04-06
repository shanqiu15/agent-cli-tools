# OCR Tool — Test & Verification Guide

## Setup

```bash
# From repo root — install all workspace packages
uv sync
```

If `uv` is not installed, install it first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Test Commands

### Run all tests
```bash
uv run pytest packages/ -q
```

### Run tests per package
```bash
# cli_common tests
uv run pytest packages/cli_common/tests/ -q

# ocr_tool tests (all)
uv run pytest packages/ocr_tool/tests/ -q

# ocr_tool tests (by module)
uv run pytest packages/ocr_tool/tests/test_models.py -q
uv run pytest packages/ocr_tool/tests/test_engines/test_local.py -q
uv run pytest packages/ocr_tool/tests/test_engines/test_llm.py -q
uv run pytest packages/ocr_tool/tests/test_service.py -q
uv run pytest packages/ocr_tool/tests/test_cli.py -q
uv run pytest packages/ocr_tool/tests/test_integration.py -q
```

## Lint & Format

```bash
# Check lint
uv run ruff check packages/cli_common/ packages/ocr_tool/

# Check formatting
uv run ruff format --check packages/cli_common/ packages/ocr_tool/

# Auto-fix lint issues
uv run ruff check --fix packages/cli_common/ packages/ocr_tool/

# Auto-format
uv run ruff format packages/cli_common/ packages/ocr_tool/
```

## Type Checking

```bash
uv run mypy packages/cli_common/src/ packages/ocr_tool/src/
```

## How to Interpret Results

- **pytest**: Exit code 0 = all tests pass. Any non-zero exit code means failures. Look at the summary line at the bottom (e.g., `15 passed` or `2 failed, 13 passed`).
- **ruff check**: Exit code 0 = no lint issues. Non-zero = violations found. Each violation is printed with file path, line number, and rule code.
- **ruff format --check**: Exit code 0 = all files formatted. Non-zero = files need reformatting. The output lists files that would be changed.
- **mypy**: Exit code 0 = no type errors. Non-zero = type errors found. Each error shows file, line, and description.

## Quick Smoke Test (CLI)

After full implementation, the CLI should work like this:

```bash
# Should print help text and exit 0
uv run ocr-tool extract --help

# Should output JSON error (image not found) and exit non-zero
uv run ocr-tool extract --image nonexistent.png

# Should perform OCR (requires easyocr models downloaded)
uv run ocr-tool extract --image test_image.png --mode local

# Should perform OCR via LLM (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=sk-... uv run ocr-tool extract --image test_image.png --mode llm
```

## Notes

- Unit tests mock external dependencies (easyocr, Anthropic API). They do NOT require model downloads or API keys.
- Integration tests use mocked engines with a tiny synthetic test image created via Pillow in a pytest fixture.
- No test should make real network calls or require GPU.
