# ocr-tool

A CLI tool for extracting text from images using OCR. Supports two engine modes: a local offline engine powered by [EasyOCR](https://github.com/JaidedAI/EasyOCR), and an LLM-based engine that uses the Anthropic vision API for higher-accuracy extraction.

## Architecture

The tool follows a layered design:

- **CLI layer** (`cli.py`) — Typer-based command interface that accepts options and emits structured JSON output via `cli_common`.
- **Service layer** (`service.py`) — Orchestrates engine selection, runs extraction, and writes results to disk.
- **Engine layer** (`engines/`) — Pluggable OCR backends:
  - `engines/local.py` — Uses EasyOCR to run inference locally. No network access required.
  - `engines/llm.py` — Sends the image to the Anthropic Messages API (Claude) with a text-extraction prompt. Requires an `ANTHROPIC_API_KEY` environment variable.
- **Models** (`models.py`) — Pydantic schemas for `OcrRequest` and `OcrResult`.
- **Errors** (`errors.py`) — `OcrError` exception extending `cli_common.errors.ToolException` with structured error codes.

## Installation

From the repository root, install with `uv`:

```bash
uv sync
```

Or install just this package in development mode:

```bash
uv pip install -e packages/ocr_tool
```

## Usage

```bash
ocr-tool extract --image <path-to-image> [OPTIONS]
```

### Options

| Option     | Type   | Default                  | Description                                      |
|------------|--------|--------------------------|--------------------------------------------------|
| `--image`  | PATH   | *(required)*             | Path to the input image file                     |
| `--output` | PATH   | `<image_stem>.txt`       | Path for the output text file                    |
| `--mode`   | STRING | `local`                  | OCR engine mode: `local` or `llm`                |
| `--model`  | STRING | engine default           | Model name override for the selected engine      |

### Examples

Extract text using the local EasyOCR engine (default):

```bash
ocr-tool extract --image screenshot.png
```

Extract text using the LLM engine:

```bash
export ANTHROPIC_API_KEY="sk-..."
ocr-tool extract --image screenshot.png --mode llm
```

Specify a custom output path:

```bash
ocr-tool extract --image photo.jpg --output result.txt
```

### Output

On success, the tool prints a JSON object to stdout:

```json
{
  "text": "extracted text content",
  "source_image": "screenshot.png",
  "output_path": "screenshot.txt",
  "mode": "local",
  "model_used": "easyocr"
}
```

On error, a structured error JSON is emitted:

```json
{
  "error": {
    "code": "IMAGE_NOT_FOUND",
    "message": "Image file not found: missing.png"
  }
}
```

## Engine Details

### Local (`--mode local`)

- Uses [EasyOCR](https://github.com/JaidedAI/EasyOCR) with English language support.
- Runs entirely offline — no API keys or network access needed.
- Default model identifier: `easyocr`.

### LLM (`--mode llm`)

- Sends the image as a base64-encoded payload to the Anthropic Messages API.
- Requires the `ANTHROPIC_API_KEY` environment variable.
- Default model: `claude-sonnet-4-20250514` (override with `--model`).
- Prompts the model to extract and return text while preserving original layout.
