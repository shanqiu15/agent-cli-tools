# OCR Tool — Implementation Plan

## Summary

Build an `ocr_tool` package that accepts an image file and extracts text via OCR, writing results to an output file (default `.txt`). The tool supports two modes: a **local mode** using a HuggingFace model (e.g., `easyocr` or `pytesseract` with a HF-hosted model) and an **LLM mode** that sends the image to a multimodal LLM (e.g., Claude or OpenAI vision API) for text extraction. The CLI follows this repo's conventions: JSON-structured output, non-interactive, typer-based.

## Approach

### Architecture

```
packages/
  cli_common/          # shared models, errors, io helpers
  ocr_tool/
    pyproject.toml
    src/ocr_tool/
      __init__.py
      cli.py           # typer app — `extract` command
      models.py         # pydantic models for request/response
      service.py        # orchestration: delegates to the right engine
      engines/
        __init__.py
        local.py        # HuggingFace / easyocr engine
        llm.py          # LLM vision API engine
      errors.py         # tool-specific exceptions
    tests/
      test_cli.py
      test_service.py
      test_engines/
        test_local.py
        test_llm.py
```

- **`cli.py`**: Single `extract` command. Takes `--image` (required path), `--output` (optional, defaults to `<image_stem>.txt`), `--mode` (`local` | `llm`), and `--model` (optional model name override). Outputs JSON to stdout per repo conventions; writes extracted text to the output file.
- **`service.py`**: Validates inputs, picks the engine, calls it, writes the output file, returns structured result.
- **`engines/local.py`**: Uses `easyocr` (pure Python, no Tesseract dependency) for local OCR. Accepts an optional HuggingFace model name for future extensibility.
- **`engines/llm.py`**: Sends the image (base64-encoded) to an LLM with vision capability. Configurable via `--model` and environment variables for API keys. Default provider: Anthropic Claude.
- **`cli_common`**: Bootstrap with shared response envelope (`ToolResponse`), error model (`ToolError`), and JSON output helpers. These will be reused by future tools.

### CLI Interface

```bash
# Local OCR (default mode)
ocr-tool extract --image photo.png

# Local OCR with explicit output
ocr-tool extract --image photo.png --output result.txt --mode local

# LLM-based OCR
ocr-tool extract --image photo.png --mode llm --model claude-sonnet-4-20250514

# JSON output to stdout (always), text file written to --output path
```

## Constraints

- Do NOT build a web server or API — CLI only.
- Do NOT support batch/directory processing in v1 — single image per invocation.
- Do NOT add PDF support — image files only (PNG, JPG, JPEG, TIFF, BMP, WEBP).
- Do NOT add interactive prompts or progress bars.
- The LLM engine must get API keys from environment variables, never hardcoded.
- Keep `cli_common` minimal — only what's needed now plus obvious shared foundations.

## Dependencies

Story ordering is strict:
1. `cli_common` must exist before `ocr_tool` can depend on it.
2. Package scaffolding and models before service logic.
3. Local engine before LLM engine (local is self-contained, easier to test).
4. CLI wiring after service logic is functional.
5. Integration tests after everything is wired.

## Risks

| Risk | Mitigation |
|------|-----------|
| `easyocr` is a large dependency (~200MB with models) | Document this; it downloads models on first run. Tests should mock the heavy inference. |
| LLM API keys missing at runtime | Return a clear structured error with code `MISSING_API_KEY`. Never crash with a raw traceback. |
| Image file formats vary wildly | Use Pillow for image loading/validation before passing to engines. Fail fast on unsupported formats. |
| HuggingFace model download on first use | Document first-run behavior. Tests must not depend on model downloads. |
| No root `pyproject.toml` yet | First story must bootstrap the monorepo workspace config. |
