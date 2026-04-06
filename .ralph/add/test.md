# Test Verification Guide

## Setup

From the repo root, ensure dependencies are installed:

```bash
cd /Users/haochen/workspace/agent-cli-tools
uv sync
```

If only the ocr_tool package needs updating:

```bash
cd packages/ocr_tool
uv sync
```

## Test Command

Run the full test suite for the ocr_tool package:

```bash
cd /Users/haochen/workspace/agent-cli-tools/packages/ocr_tool
uv run pytest -q
```

**Pass criteria**: Exit code 0, all tests pass, no failures or errors.

To run specific test files:

```bash
uv run pytest tests/test_engines/test_google.py -q    # Google engine tests
uv run pytest tests/test_service.py -q                 # Service layer tests
uv run pytest tests/test_cli.py -q                     # CLI tests
uv run pytest tests/test_models.py -q                  # Model tests
```

## Lint and Format Check

```bash
cd /Users/haochen/workspace/agent-cli-tools/packages/ocr_tool
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

**Pass criteria**: Both commands exit 0 with no output (no violations).

## Type Check

```bash
cd /Users/haochen/workspace/agent-cli-tools/packages/ocr_tool
uv run mypy src/
```

**Pass criteria**: Exit 0. Warnings about missing stubs for `google.cloud.vision` or `easyocr` are acceptable (these are pre-existing). No new type errors in ocr_tool source code.

## How to Interpret Results

- **pytest**: Look for the summary line at the end. `X passed` = success. Any `FAILED` or `ERROR` lines indicate problems. The `-q` flag keeps output compact.
- **ruff check**: Silence = success. Any output line indicates a lint violation that must be fixed.
- **ruff format**: Silence = success. Any output indicates files that need reformatting.
- **mypy**: `Success: no issues found` is ideal. Lines with `error:` indicate type issues to fix. Lines with `note:` are informational.

## Dependency Resolution

After adding `google-cloud-vision` to pyproject.toml:

```bash
cd /Users/haochen/workspace/agent-cli-tools
uv lock
```

**Pass criteria**: Exit 0, uv.lock is updated without conflicts.

## API Key Authentication Testing

The Google engine supports API key auth via environment variables. To verify auth works in tests, the test suite mocks the client creation. To verify manually:

```bash
# Set one of these env vars (checked in this order):
export GOOGLE_API_KEY="your-key"
# or: export GOOGLE_PLACES_API_KEY="your-key"
# or: export GEMINI_API_KEY="your-key"
# Fallback: GOOGLE_APPLICATION_CREDENTIALS or gcloud ADC

# Then run:
cd packages/ocr_tool
uv run ocr-tool extract --image test.png --mode google
```

**Note**: The API key must belong to a GCP project with the Cloud Vision API enabled. If the API is not enabled for the key's project, the API will return a permission error.
