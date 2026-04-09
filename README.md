# agent-cli-tools

A monorepo of composable Python CLI tools for LLM agents. Each package provides a standalone capability with a stable, machine-readable JSON interface.

## Quick Start

```bash
# Install all tools
uv sync

# Run any tool
uv run <tool-name> <command> [options]

# Run tests
uv run pytest                  # skip external service tests
uv run pytest --all            # include external service tests
```

## Prerequisites

Most tools only need Python 3.12+ and `uv`. Some tools have additional requirements:

| Tool | Requirement | Install |
|------|------------|---------|
| browser-tool | Node.js + Playwright CLI | `npm install -g @playwright/cli@latest && npx playwright install chromium` |

## Output Format

All tools produce structured JSON on stdout:

**Success (exit 0):**
```json
{
  "ok": true,
  "result": { ... }
}
```

**Error (exit 1):**
```json
{
  "ok": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

---

## Tools

### bash-tool

Execute shell commands with timeout and output limits.

```bash
# Run a command
bash-tool run --command "ls -la"

# With custom timeout and output limit
bash-tool run --command "find / -name '*.log'" --timeout 10 --max-output 5000
```

| Option | Default | Description |
|--------|---------|-------------|
| `--command` | *(required)* | Shell command to execute |
| `--timeout` | `30` | Maximum execution time in seconds |
| `--max-output` | `10000` | Maximum output characters (truncated with indicator) |

**Error codes:** `INVALID_INPUT`, `TIMEOUT`

**Note:** A non-zero exit code from the command is not treated as a tool error. The exit code is returned in the `exit_code` field of the result.

---

### browser-tool

Browser automation via Playwright. Requires `playwright-cli` binary in PATH.

```bash
# Session lifecycle
browser-tool start
browser-tool status
browser-tool stop

# Navigation
browser-tool navigate --url "https://example.com"
browser-tool snapshot
browser-tool screenshot --path ./screenshot.png

# Interaction (use refs from snapshot output)
browser-tool click --ref "s1e3"
browser-tool type --ref "s1e5" --text "hello world"
browser-tool press --key Enter
```

All commands accept `--session NAME` (default: `default`) to manage multiple browser sessions.

| Command | Key Options | Description |
|---------|------------|-------------|
| `start` | `--session` | Launch headless browser |
| `stop` | `--session` | Terminate browser |
| `status` | `--session` | Check if session is active |
| `navigate` | `--url` | Go to URL, return page snapshot |
| `snapshot` | | Get accessibility tree with element refs |
| `screenshot` | `--path` | Save screenshot to file |
| `click` | `--ref` | Click element by accessibility ref |
| `type` | `--ref`, `--text` | Type text into element |
| `press` | `--key` | Press keyboard key (Enter, Tab, Escape, etc.) |

**Error codes:** `PLAYWRIGHT_CLI_NOT_FOUND`, `BROWSER_START_FAILED`, `NAVIGATION_FAILED`, `SNAPSHOT_FAILED`, `SCREENSHOT_FAILED`, `CLICK_FAILED`, `TYPE_FAILED`, `PRESS_FAILED`, `TIMEOUT`

---

### cron-tool

Schedule jobs via an HTTP gateway API.

```bash
# Create a cron job
cron-tool create --name "daily-report" --schedule "0 9 * * *" --command "generate-report"

# Create an interval job
cron-tool create --name "health-check" --schedule "every 5m" --command "ping-service"

# Create a one-shot job
cron-tool create --name "deploy" --schedule "2026-04-10T14:00:00Z" --command "deploy-prod"

# List and delete
cron-tool list
cron-tool delete --job-id "abc123"
```

| Command | Options | Description |
|---------|---------|-------------|
| `create` | `--name`, `--schedule`, `--command`, `--timezone` (default: UTC) | Create a scheduled job |
| `list` | | List all jobs |
| `delete` | `--job-id` | Delete a job by ID |

**Schedule formats:** cron expressions (`0 9 * * *`), intervals (`every 5m`, `every 1h`), or ISO 8601 timestamps.

**Environment variables:**
| Variable | Required | Description |
|----------|----------|-------------|
| `CRON_GATEWAY_URL` | Yes | Base URL of the gateway API |

**Error codes:** `MISSING_CREDENTIALS`, `INVALID_INPUT`

---

### image-gen-tool

Generate images using the Google Gemini Imagen API.

```bash
image-gen-tool generate --prompt "A sunset over mountains" --output-path ./sunset.png

# With custom aspect ratio
image-gen-tool generate --prompt "A banner image" --output-path ./banner.png --aspect-ratio 16:9
```

| Option | Default | Description |
|--------|---------|-------------|
| `--prompt` | *(required)* | Text description of the image |
| `--output-path` | *(required)* | File path to save the generated image |
| `--aspect-ratio` | `1:1` | One of: `1:1`, `16:9`, `9:16`, `4:3`, `3:4` |

**Environment variables:**
| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |

**Error codes:** `MISSING_CREDENTIALS`, `INVALID_INPUT`, `INVALID_OUTPUT_PATH`, `API_ERROR`, `FILE_WRITE_ERROR`

---

### memory-tool

File-based memory system for persistent agent knowledge.

```bash
# Write a memory file
memory-tool write --path "notes.md" --content "Project uses Python 3.12"

# Append to existing file
memory-tool write --path "log.md" --content "2026-04-06: deployed v2" --append

# Read a file
memory-tool read --path "notes.md"

# Search across all .md files
memory-tool search --query "Python"

# Use a custom memory directory
memory-tool write --path "notes.md" --content "hello" --memory-dir /tmp/my-memory
```

| Command | Options | Description |
|---------|---------|-------------|
| `write` | `--path`, `--content`, `--append` (default: false), `--memory-dir` | Write or append to a memory file |
| `read` | `--path`, `--memory-dir` | Read a memory file |
| `search` | `--query`, `--memory-dir` | Search .md files (case-insensitive substring match) |

Default `--memory-dir` is `./memory/`. All paths are validated to prevent directory traversal.

**Error codes:** `INVALID_PATH`, `FILE_NOT_FOUND`

---

### ocr-tool

Extract text from images and PDFs using local OCR or Google Cloud Vision.

```bash
# Default mode (Google Cloud Vision, falls back to local if no API key)
ocr-tool extract --image photo.jpg

# Explicit Google mode
ocr-tool extract --image document.pdf --mode google

# Local mode (easyocr, images only)
ocr-tool extract --image photo.jpg --mode local

# Custom output path
ocr-tool extract --image photo.jpg --output result.txt
```

| Option | Default | Description |
|--------|---------|-------------|
| `--image` | *(required)* | Path to image or PDF file |
| `--output` | `<image_stem>.txt` | Output text file path |
| `--mode` | Auto (google with local fallback) | `local` or `google` |
| `--model` | Engine default | Model name override |

**Supported formats:** PNG, JPG, JPEG, GIF, BMP, TIFF, TIF, WebP. PDF supported in Google mode only (up to 5 pages).

**Environment variables:**
| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CLOUD_VISION_API_KEY` | For google mode | Google Cloud Vision API key |

**Error codes:** `MISSING_CREDENTIALS`, `IMAGE_NOT_FOUND`, `INVALID_IMAGE`, `INVALID_FILE`, `UNSUPPORTED_FILE_TYPE`, `API_ERROR`, `PDF_TOO_LARGE`

---

### sonar-tool

AI-powered web search with citations via Perplexity Sonar API.

```bash
sonar-tool search --query "latest Python release"

# Use a more powerful model
sonar-tool search --query "quantum computing advances" --model sonar-pro
```

| Option | Default | Description |
|--------|---------|-------------|
| `--query` | *(required)* | Search query |
| `--model` | `sonar` | One of: `sonar`, `sonar-pro`, `sonar-reasoning-pro`, `sonar-deep-research` |

**Environment variables:**
| Variable | Required | Description |
|----------|----------|-------------|
| `PERPLEXITY_API_KEY` | Yes | Perplexity API key |

**Error codes:** `MISSING_CREDENTIALS`, `INVALID_INPUT`

---

### web-crawl-tool

Fetch and extract readable content from web pages.

```bash
web-crawl-tool crawl --url "https://example.com"

# With custom timeout and max content length
web-crawl-tool crawl --url "https://example.com" --timeout 30 --max-length 5000
```

| Option | Default | Description |
|--------|---------|-------------|
| `--url` | *(required)* | URL to crawl (must be http:// or https://) |
| `--timeout` | `60` | Request timeout in seconds |
| `--max-length` | `20000` | Maximum content length before truncation |

Uses crawl4ai service if available, otherwise falls back to direct fetch with readability-lxml.

**Environment variables:**
| Variable | Required | Description |
|----------|----------|-------------|
| `CRAWL4AI_BASE_URL` | No | Optional crawl4ai service URL |

**Error codes:** `INVALID_URL`, `EXTRACTION_FAILED`, `TIMEOUT`, `HTTP_ERROR`

---

### web-search-tool

Google web search via the Serper API.

```bash
web-search-tool search --query "Python asyncio tutorial"

# Limit results
web-search-tool search --query "best CLI frameworks" --num-results 3
```

| Option | Default | Description |
|--------|---------|-------------|
| `--query` | *(required)* | Search query |
| `--num-results` | `5` | Number of results (1-10) |

**Environment variables:**
| Variable | Required | Description |
|----------|----------|-------------|
| `SERPER_API_KEY` | Yes | Serper API key |

**Error codes:** `MISSING_CREDENTIALS`, `INVALID_INPUT`

---

## Environment Variables Summary

| Variable | Tools | Description |
|----------|-------|-------------|
| `GOOGLE_CLOUD_VISION_API_KEY` | ocr-tool | Google Cloud Vision API key |
| `GOOGLE_API_KEY` | image-gen-tool | Google Gemini API key |
| `PERPLEXITY_API_KEY` | sonar-tool | Perplexity API key |
| `SERPER_API_KEY` | web-search-tool | Serper API key |
| `CRON_GATEWAY_URL` | cron-tool | Gateway API base URL |
| `CRAWL4AI_BASE_URL` | web-crawl-tool | Optional crawl4ai service URL |

## Development

```bash
# Install all packages in dev mode
uv sync

# Run all tests (local only)
uv run pytest

# Run all tests including external services
uv run pytest --all

# Lint and format
uv run ruff check
uv run ruff format

# Type check
uv run mypy
```
