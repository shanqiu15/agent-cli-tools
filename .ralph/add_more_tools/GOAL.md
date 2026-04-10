# Goal

# Tool Implementation Goals

Survey of hermes-agent tools and implementation plan for agent-cli-tools.

---

## 1. file_tool

### How hermes-agent does it
- `file_tools.py`: read, write, list, search files with safety guards (blocked device paths, binary detection, read-size caps at 100K chars, sensitive path deny-list for writes like `~/.ssh`, `/etc/shadow`)
- `file_operations.py`: abstraction layer (`ShellFileOperations`) that works across local/docker/ssh/modal backends by expressing all ops as shell commands. Supports read, write, patch (find-and-replace), search (grep), and unified diff generation.
- Two modules because file_tools is the agent-facing tool layer; file_operations is the backend-agnostic execution layer.

### Code references (~/workspace/hermes-agent/)
- `tools/file_tools.py`
  - L62-71: `_BLOCKED_DEVICE_PATHS` -- device path blocklist (`/dev/zero`, `/dev/urandom`, etc.)
  - L74-97: `_is_blocked_device()` -- device path check logic
  - L99-117: `_check_sensitive_path()` -- deny writes to `~/.ssh`, `/etc/shadow`, etc.
  - L280-448: `read_file_tool()` -- full read implementation with offset/limit, binary detection, staleness check, dedup tracking
  - L571-593: `write_file_tool()` -- write with sensitive path guard, error classification
  - L595-650: `patch_tool()` -- find-and-replace with `mode="replace"` and `mode="patch"` (V4A multi-file)
  - L652-726: `search_tool()` -- content search and file-name search with glob, offset/limit, context lines
  - L27-56: read-size guard config (`_DEFAULT_MAX_READ_CHARS = 100_000`, `_LARGE_FILE_HINT_BYTES = 512_000`)
- `tools/file_operations.py`
  - L41-78: `WRITE_DENIED_PATHS` and `WRITE_DENIED_PREFIXES` -- sensitive path deny-lists
  - L99-122: `_is_write_denied()` -- path checking with `os.path.realpath`
  - L124-247: dataclasses `ReadResult`, `WriteResult`, `PatchResult`, `SearchMatch`, `SearchResult`
  - L248-300: `FileOperations` ABC -- abstract interface for read/write/patch/search
  - L302+: `ShellFileOperations` -- concrete implementation via shell commands
- `tools/binary_extensions.py`
  - L1-42: `BINARY_EXTENSIONS` frozenset and `has_binary_extension()` helper

### Proposal
- **Subcommands**: `read`, `write`, `patch`, `search`, `list`, `tree`
- `read`: read file with `--offset` / `--limit` (1-indexed lines), cap output at 100K chars
- `write`: write/overwrite a file, deny writes to sensitive paths (`~/.ssh`, `/etc/shadow`, etc.)
- `patch`: targeted find-and-replace (`--old` / `--new` / `--replace-all`)
- `search`: ripgrep-style content search with glob filter, context lines, offset/limit
- `list` / `tree`: directory listing with depth control
- Safety: block device paths (`/dev/zero`, `/dev/urandom`), binary file detection by extension + magic bytes, path traversal prevention
- No remote backend abstraction needed (keep it local-only, simple)

### Providers
- N/A (pure local, no external API)

### E2E testing
- Create temp directory with sample files, run each subcommand, assert stdout JSON
- Test safety guards: attempt to read `/dev/zero`, write to `~/.ssh/id_rsa`, read a binary file
- Test patch with unique and non-unique matches
- Test search with glob filters and context lines

---

## 2. vision_tool

### How hermes-agent does it
- Downloads image from URL (with SSRF protection, redirect guards, retry logic) or reads local file
- Detects MIME type via magic bytes
- Converts to base64 data URL
- Sends to a configurable vision LLM via OpenAI-compatible API (Gemini Flash, Anthropic, OpenRouter, etc.)
- Returns `{success, analysis}` JSON

### Code references (~/workspace/hermes-agent/)
- `tools/vision_tools.py`
  - L71-99: `_validate_image_url()` -- URL validation + SSRF check via `is_safe_url()`
  - L102-121: `_detect_image_mime_type()` -- magic bytes detection (PNG, JPEG, GIF, BMP, WebP, SVG)
  - L124-212: `_download_image()` -- async httpx download with retry (3x), SSRF redirect guard via `event_hooks`, website policy check
  - L238-261: `_image_to_base64_data_url()` -- base64 data URL conversion
  - L264-483: `vision_analyze_tool()` -- main entry: local vs URL dispatch, base64 encode, build multimodal message, call LLM, retry on empty, cleanup temp files in `finally`
  - L576-604: `VISION_ANALYZE_SCHEMA` + `_handle_vision_analyze()` -- tool schema and prompt wrapper ("Fully describe and explain everything about this image, then answer...")
- `tools/url_safety.py`
  - L38-48: `_is_blocked_ip()` -- blocks private, loopback, link-local, reserved IPs
  - L50-96: `is_safe_url()` -- resolves hostname to IP, checks against blocklist (SSRF prevention)

### Proposal
- **Subcommands**: `analyze`
- Input: `--image` (URL or local file path) + `--prompt` (question about the image)
- Providers:
  - **Free**: Google Gemini Flash via `google-generativeai` SDK (free tier: 15 RPM)
  - **Paid**: OpenAI `gpt-4o-mini` vision via `openai` SDK
- Config via env vars: `VISION_PROVIDER` (gemini|openai), `GOOGLE_API_KEY`, `OPENAI_API_KEY`
- Download URL images to temp file with httpx, SSRF guard (block private IPs), retry 3x
- Detect MIME via magic bytes, convert to base64
- Send multimodal request, return JSON `{success, analysis}`

### E2E testing
- Analyze a small test image (include a 1x1 PNG in test fixtures) with a mock server
- Test with a local file path
- Test with an invalid URL (assert error)
- Test SSRF protection (attempt `http://169.254.169.254`, assert blocked)
- Integration test (requires real API key, mark with `@pytest.mark.integration`): analyze a real image from a public URL

---

## 3. transcription_tool

### How hermes-agent does it
- Multi-provider STT: local faster-whisper (free) > Groq Whisper API (free tier) > OpenAI Whisper API (paid) > Mistral Voxtral
- Validates audio file (format, size <25MB)
- Config-driven provider selection from `config.yaml`
- Local provider: lazy-loads faster-whisper model, singleton pattern
- API providers: use OpenAI SDK pointed at different base URLs

### Code references (~/workspace/hermes-agent/)
- `tools/transcription_tools.py`
  - L64-81: constants -- `SUPPORTED_FORMATS`, `MAX_FILE_SIZE` (25MB), default models per provider
  - L178-258: `_get_provider()` -- provider auto-detection cascade: local > local_command > groq > openai > mistral
  - L265-290: `_validate_audio_file()` -- checks existence, is_file, extension, size
  - L297-334: `_transcribe_local()` -- faster-whisper with singleton model loading, language config
  - L359-422: `_transcribe_local_command()` -- CLI whisper via subprocess, ffmpeg audio conversion
  - L429-474: `_transcribe_groq()` -- Groq Whisper API using OpenAI SDK with `base_url=GROQ_BASE_URL`, auto-corrects model names
  - L481-531: `_transcribe_openai()` -- OpenAI Whisper API with managed gateway fallback
  - L538-569: `_transcribe_mistral()` -- Mistral Voxtral via `mistralai` SDK
  - L577-649: `transcribe_audio()` -- main entry point: validate → pick provider → dispatch
  - L677-692: `_extract_transcript_text()` -- normalizes response objects/dicts/strings to plain text

### Proposal
- **Subcommands**: `transcribe`
- Input: `--file` (path to audio file)
- Supported formats: mp3, wav, ogg, m4a, webm, flac
- Max file size: 25MB
- Providers:
  - **Free**: Groq Whisper API (`whisper-large-v3-turbo`) -- free tier, requires `GROQ_API_KEY`
  - **Paid**: OpenAI Whisper API (`whisper-1`) -- requires `OPENAI_API_KEY`
- Config via env vars: `TRANSCRIPTION_PROVIDER` (groq|openai), respective API keys
- Returns JSON `{success, transcript, provider}`
- Skip local faster-whisper for now (heavy dependency, model download) -- can add later

### E2E testing
- Test file validation: unsupported format, oversized file, missing file
- Mock server test: mock the OpenAI-compatible `/audio/transcriptions` endpoint, assert correct request/response
- Integration test (`@pytest.mark.integration`): transcribe a short test audio file (include a 2-second WAV in fixtures)

---

## 4. tts_tool

### How hermes-agent does it
- 5 providers: Edge TTS (free, default), ElevenLabs (premium), OpenAI TTS, MiniMax, NeuTTS (local)
- Edge TTS uses `edge_tts` Python package (Microsoft neural voices, async)
- Optional ffmpeg conversion to Opus/OGG for Telegram
- Config from `config.yaml`, output to cache directory

### Code references (~/workspace/hermes-agent/)
- `tools/tts_tool.py`
  - L50-67: lazy imports -- `_import_edge_tts()`, `_import_elevenlabs()`, `_import_openai_client()`, `_import_sounddevice()` (avoids crashes in headless environments)
  - L71-91: defaults -- `DEFAULT_EDGE_VOICE = "en-US-AriaNeural"`, `DEFAULT_OPENAI_VOICE = "alloy"`, `DEFAULT_OPENAI_MODEL = "gpt-4o-mini-tts"`, `MAX_TEXT_LENGTH = 4000`
  - L97-119: `_load_tts_config()` / `_get_provider()` -- config loading and provider selection
  - L124-161: `_convert_to_opus()` -- ffmpeg MP3→OGG Opus conversion for Telegram voice
  - L167-186: `_generate_edge_tts()` -- async Edge TTS generation via `edge_tts.Communicate`
  - L191-231: `_generate_elevenlabs()` -- ElevenLabs streaming chunks to file
  - L237-282: `_generate_openai_tts()` -- OpenAI TTS via `client.audio.speech.create()`, streams to file
  - L284-370: `_generate_minimax_tts()` -- MiniMax TTS via REST API with hex audio decoding
  - L391-445: `_generate_neutts()` -- local NeuTTS via subprocess CLI
  - L447-624: `text_to_speech_tool()` -- main entry: validate text, pick provider, generate audio, convert format, return file path
  - L660-676: `_resolve_openai_audio_client_config()` -- resolves API key from config/env/managed gateway
  - L702-715: `_strip_markdown_for_tts()` -- strips markdown formatting before speech synthesis

### Proposal
- **Subcommands**: `speak`
- Input: `--text` (string, max 4000 chars) + `--output` (file path, default stdout path) + `--format` (mp3|wav)
- Providers:
  - **Free**: Edge TTS via `edge-tts` package (no API key needed)
  - **Paid**: OpenAI TTS (`tts-1` model) via `openai` SDK -- requires `OPENAI_API_KEY`
- Config via env vars: `TTS_PROVIDER` (edge|openai), `TTS_VOICE` (provider-specific voice name)
- Default voices: Edge=`en-US-AriaNeural`, OpenAI=`alloy`
- Returns JSON `{success, file_path, provider, duration_hint}`

### E2E testing
- Test text validation: empty text, text exceeding 4000 chars
- Mock test for OpenAI: mock `/audio/speech` endpoint
- Edge TTS test: generate a small audio file, assert file exists and is valid MP3 (check magic bytes)
- Integration test (`@pytest.mark.integration`): generate real audio, verify file is playable

---

## 5. todo_tool

### How hermes-agent does it
- In-memory `TodoStore` class: ordered list of `{id, content, status}` items
- Single tool entry point: pass `todos` to write, omit to read
- Two write modes: replace (full rewrite) or merge (update by id, append new)
- Statuses: pending, in_progress, completed, cancelled
- `format_for_injection()` renders active items for post-compression re-injection
- Purely in-memory, one instance per agent session

### Code references (~/workspace/hermes-agent/)
- `tools/todo_tool.py`
  - L20: `VALID_STATUSES` -- `{"pending", "in_progress", "completed", "cancelled"}`
  - L25-84: `TodoStore` class
    - L38-80: `write()` -- replace mode (default) or merge mode (update by id, append new, preserve order)
    - L82-84: `read()` -- returns copy of items list
    - L90-122: `format_for_injection()` -- renders only active (pending/in_progress) items for context re-injection after compression
    - L124-144: `_validate()` -- normalizes item fields, defaults invalid status to "pending"
  - L147-186: `todo_tool()` -- main entry: read or write, returns JSON with items + summary counts
  - L200-254: `TODO_SCHEMA` -- OpenAI function-calling schema with behavioral guidance baked into description (e.g. "Only ONE item in_progress at a time")

### Proposal
- **Subcommands**: `list`, `write`, `clear`
- `list`: read current todos, returns JSON array
- `write`: accepts JSON array of `{id, content, status}` items via stdin or `--items` flag
  - `--merge` flag: update existing by id, append new. Default: replace entire list
- `clear`: remove all items
- Statuses: pending, in_progress, completed, cancelled
- Storage: JSON file at `~/.local/share/agent-cli-tools/todos.json` (persistent across invocations, unlike hermes which is in-memory)
- Returns summary: `{todos: [...], summary: {total, pending, in_progress, completed, cancelled}}`

### E2E testing
- Write items, list them back, assert match
- Test merge mode: write initial list, merge update, assert correct state
- Test status validation: invalid status defaults to pending
- Test clear: write items, clear, list returns empty
- Test persistence: write items, invoke list in a new process, assert items survive

---

## 6. skill_tool

### How hermes-agent does it
- **skills_tool.py**: read-only listing and viewing. Skills are directories with a `SKILL.md` (YAML frontmatter + markdown body). Progressive disclosure: `skills_list` returns metadata only, `skill_view` loads full content. Searches bundled skills, hub-installed skills, and user-created skills.
- **skill_manager_tool.py**: CRUD operations. Create/edit/patch/delete skills in `~/.hermes/skills/`. Validates YAML frontmatter (name, description required). Security scans agent-created skills. Supports supporting files in `references/`, `templates/`, `scripts/`, `assets/` subdirectories.

### Code references (~/workspace/hermes-agent/)
- `tools/skills_tool.py` (read-only listing & viewing)
  - L107-121: `load_env()` -- loads `.env` files for env var prerequisites
  - L134-143: `skill_matches_platform()` -- filters skills by OS platform (macos/linux/windows)
  - L413-448: `_parse_frontmatter()` -- YAML frontmatter extraction from SKILL.md
  - L520-595: `_find_all_skills()` -- scans bundled + hub + user skill directories, parses frontmatter, checks platform/disabled status
  - L640-717: `skills_categories()` -- lists skill categories with counts and descriptions
  - L719-785: `skills_list()` -- lists skills with metadata only (progressive disclosure tier 1)
  - L787-1317: `skill_view()` -- loads full SKILL.md content + supporting files (tier 2-3), handles env var setup prompts
- `tools/skill_manager_tool.py` (CRUD)
  - L80-93: constants -- `SKILLS_DIR`, `MAX_NAME_LENGTH=64`, `MAX_SKILL_CONTENT_CHARS=100_000`, `VALID_NAME_RE`, `ALLOWED_SUBDIRS`
  - L99-110: `_validate_name()` -- lowercase alphanumeric + hyphens/dots/underscores
  - L113-135: `_validate_category()` -- single directory segment validation
  - L138-174: `_validate_frontmatter()` -- YAML parse, requires `name` + `description`, checks body exists
  - L243-277: `_atomic_write_text()` -- atomic file write via tempfile + rename (crash-safe)
  - L279-334: `_create_skill()` -- creates skill dir + SKILL.md, security scan, returns metadata
  - L336-367: `_edit_skill()` -- replaces SKILL.md content with validation
  - L369-453: `_patch_skill()` -- targeted find-and-replace within SKILL.md or supporting files
  - L455-473: `_delete_skill()` -- removes skill directory with shutil.rmtree
  - L475-523: `_write_file()` -- adds supporting files to allowed subdirs (references/templates/scripts/assets)
  - L525-567: `_remove_file()` -- removes supporting files
  - L569-722: `skill_manage()` -- main dispatcher for all CRUD actions

### Proposal
- **Subcommands**: `list`, `view`, `create`, `edit`, `delete`
- `list`: list all skills with metadata (name, description, version) -- no full content
- `view`: load full SKILL.md content for a named skill, optionally a supporting file (`--file references/api.md`)
- `create`: create a new skill directory with SKILL.md (`--name`, `--content` via stdin)
  - Validates YAML frontmatter (name + description required)
  - Creates in `~/.local/share/agent-cli-tools/skills/<name>/`
- `edit`: replace SKILL.md content for an existing skill (`--name`, new content via stdin)
- `delete`: remove a skill directory (`--name`, `--force` to skip confirmation)
- Supporting files: `--write-file <skill>:<subdir>/<filename>` and `--remove-file`
- Allowed subdirs: references, templates, scripts, assets
- Name validation: lowercase alphanumeric + hyphens/dots/underscores, max 64 chars

### Providers
- N/A (pure local filesystem)

### E2E testing
- Create a skill, list it, view it, edit it, delete it (full lifecycle)
- Test frontmatter validation: missing name, missing description, invalid YAML
- Test name validation: special characters, too long
- Test supporting files: write a reference file, view it, remove it
- Test listing with multiple skills across categories

---

## Implementation Order

Recommended order based on dependencies and complexity:

1. **file_tool** -- foundational, no external deps, other tools may use it
2. **todo_tool** -- simple, self-contained, good for validating the package template
3. **vision_tool** -- first tool with external API providers
4. **transcription_tool** -- similar provider pattern to vision
5. **tts_tool** -- similar provider pattern, adds edge-tts dependency
6. **skill_tool** -- most complex (CRUD + validation + filesystem structure)

---

## Shared Patterns

All tools should follow existing conventions in the repo:

- Package layout: `packages/<name>/src/<name>/{cli.py, service.py, models.py, errors.py}`
- CLI framework: typer
- Output: JSON to stdout via cli_common
- Config: env vars (no config.yaml dependency -- keep tools standalone)
- Testing: pytest, fixtures in `tests/`, integration tests marked with `@pytest.mark.integration`
- Each tool is independently installable via `uv pip install -e packages/<name>`
