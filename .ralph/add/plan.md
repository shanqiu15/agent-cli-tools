# Plan: Add Google Cloud Vision OCR Engine with PDF Support

## Summary

Replace the low-quality local OCR (easyocr) with Google Cloud Vision API as the default OCR engine. Remove the LLM-based OCR engine entirely — LLM agents can already do their own OCR, so a dedicated LLM engine is redundant. The mode literal narrows from `Literal["local", "llm"]` to `Literal["local", "google"]`, with `google` as the default. When `GOOGLE_API_KEY` is not set, the tool automatically falls back to `local` mode. The response clearly indicates which OCR source was used. PDF input is supported via the Google engine.

## Current State

The following already exists from a partial implementation:
- `packages/ocr_tool/src/ocr_tool/engines/google.py` — basic ADC-only implementation using `document_text_detection`. Creates `ImageAnnotatorClient()` without client options (line 50). Needs to switch to API key auth.
- `packages/ocr_tool/src/ocr_tool/engines/llm.py` — Anthropic-based LLM engine. **To be removed.**
- `packages/ocr_tool/pyproject.toml` — already includes `google-cloud-vision>=3.7` dependency, also has `anthropic>=0.39.0` (to be removed).
- `packages/ocr_tool/tests/test_engines/test_google.py` — 4 tests covering ADC-only credential check, missing file, successful extraction, and empty result. Needs to be updated for API key auth.
- `packages/ocr_tool/tests/test_engines/test_llm.py` — 5 tests for LLM engine. **To be removed.**
- Models use `Literal["local", "llm"]` (models.py lines 17, 35) — needs to become `Literal["local", "google"]`.
- Service dispatches only to local/llm (service.py lines 27-32) — needs google branch, llm branch removed.
- CLI validates only `("local", "llm")` on line 39 of `cli.py` — needs to become `("local", "google")` with default changed to `"google"`.

## Approach

1. **Update the existing Google engine** at `packages/ocr_tool/src/ocr_tool/engines/google.py` to use `GOOGLE_API_KEY` for authentication. Replace the existing ADC credential check (currently lines 25-38) with a simple `GOOGLE_API_KEY` env var lookup. Replace client creation (currently line 50) with `ImageAnnotatorClient(client_options={"api_key": key})`.

2. **Remove the LLM engine**: Delete `engines/llm.py` and `tests/test_engines/test_llm.py`. Remove `anthropic>=0.39.0` from `pyproject.toml` dependencies. Remove the llm import and dispatch branch from `service.py`. Remove any llm-related integration tests.

3. **Change the mode literal** in `OcrRequest.mode` and `OcrResult.mode` from `Literal["local", "llm"]` to `Literal["local", "google"]`. Change the default mode from `"local"` to `"google"`.

4. **Implement auto-fallback**: When the user does not specify a mode (uses the default `"google"`), if `GOOGLE_API_KEY` is not set, automatically fall back to `"local"` mode. The `OcrResult.mode` field must reflect the **actual** engine used (e.g. `"local"` if fallback occurred), not the requested mode. This gives clear visibility into which OCR source produced the result.

5. **Clearly show OCR source**: The `OcrResult` already has `mode` and `model_used` fields. Ensure `mode` always reflects the actual engine used (especially after fallback). The `model_used` field should be `"google-cloud-vision"` for google or `"easyocr"` for local. The CLI JSON output naturally includes these fields, making the OCR source visible to the caller.

6. **Handle PDF input**: The google engine should accept both images and PDFs. Use `document_text_detection` for images and `batch_annotate_files` with inline content for PDFs (up to 5 pages synchronously). Detect file type by extension. Update the `image_path` field description to mention PDF support.

7. **Authentication**: Read `GOOGLE_API_KEY` from the environment. If not set and mode was explicitly `"google"`, raise `OcrError` with code `MISSING_CREDENTIALS`. If not set and mode was the default, silently fall back to local.

## Constraints

- Do NOT keep the `llm` engine — remove it entirely (engine file, tests, dependency, dispatch branch).
- Do NOT remove or modify the existing `local` engine — it stays as the fallback.
- Do NOT require Google Cloud Storage (GCS) — use inline content for PDFs (up to 5 pages per request via `batch_annotate_files`). This is a CLI tool, not a batch pipeline.
- Do NOT add interactive authentication flows or ADC fallback. The only Google credential source is the `GOOGLE_API_KEY` env var.
- PDF support is only for the `google` engine. Local (easyocr) remains image-only.
- The `google-cloud-vision` dependency is already a regular dependency in `pyproject.toml` — keep it that way.

## Dependencies (story ordering)

- US-001 (Google engine with API key auth + tests) must come first — everything else builds on it.
- US-002 (remove LLM engine, update models/service for google + fallback) depends on US-001.
- US-003 (PDF support) depends on US-002.
- US-004 (CLI update) depends on US-002.
- US-005 (full quality gate) runs after US-002–US-004.

## Risks

1. **Google Cloud Vision SDK version compatibility**: The `google-cloud-vision` package pulls in many transitive dependencies (grpc, protobuf, google-auth). This may conflict with existing deps. Mitigate by running `uv lock` early and resolving conflicts in the first story.

2. **PDF page limit**: Inline `batch_annotate_files` supports up to 5 pages. For longer PDFs, you'd need GCS-based async processing. For now, raise a clear error if the PDF exceeds 5 pages. Document this limitation.

3. **API key permissions**: The `GOOGLE_API_KEY` must belong to a GCP project with the Cloud Vision API enabled. If the API is not enabled for the key's project, the API will return a clear permission error. The engine should surface this error message to the user.

4. **Mypy and type stubs**: `google-cloud-vision` has generated protobuf types that may not play perfectly with mypy. The existing `engines/google.py` already uses `# type: ignore[import-untyped]` on the vision import. Additional `type: ignore` comments may be needed and are acceptable.

5. **Removing anthropic dependency**: Removing `anthropic>=0.39.0` from pyproject.toml will change the lock file. Run `uv lock` after removal and verify no other package depends on it.

## Changes

- **Round 1**: Authentication strategy revised from ADC-only to API key first with ADC fallback.
- **Round 2**: Added implementation notes clarifying existing files. Updated US-003 to recommend `pypdf` over deprecated `PyPDF2`.
- **Round 3**: Promoted implementation notes to a "Current State" section with specific line numbers from the actual code. Updated approach steps to reference exact locations that need changing. Tightened risk #4 to note existing `type: ignore` pattern. No structural changes to stories — reviewer confirmed plan is acceptable.
- **Round 4**: Reviewer approved plan with no further changes. Re-verified all line references against current codebase — confirmed accurate. Plan finalized.
- **Round 5**: Simplified authentication per reviewer feedback. Removed ADC fallback and multi-key chain. The only credential source is now `GOOGLE_API_KEY`.
- **Round 6**: Major revision per reviewer feedback:
  - **Removed LLM engine entirely** — LLM agents can do their own OCR, so a dedicated LLM tool is redundant. This means deleting `engines/llm.py`, `test_llm.py`, removing the `anthropic` dependency, and removing all llm dispatch/validation code.
  - **Made Google the default mode** — mode default changes from `"local"` to `"google"`. When `GOOGLE_API_KEY` is not available and no explicit mode was requested, automatically fall back to `"local"`.
  - **OCR source visibility** — `OcrResult.mode` now reflects the actual engine used (important when fallback occurs). Combined with `model_used`, the caller always knows which OCR source produced the result.
  - Restructured US-002 to cover both LLM removal and google/fallback integration. Updated all stories and acceptance criteria accordingly.
