# Plan: Add Google Cloud Vision OCR Engine with PDF Support

## Summary

Replace the low-quality local OCR (easyocr) and expensive LLM-based OCR with Google Cloud Vision API as the primary OCR engine. The Google Cloud Vision API provides high-quality text extraction at reasonable cost and natively supports both images and PDFs through the same SDK (`google-cloud-vision`). The CLI mode literal and models need to expand to accommodate the new `google` engine, and PDF input needs to be handled as a new file type.

## Current State

The following already exists from a partial implementation:
- `packages/ocr_tool/src/ocr_tool/engines/google.py` — basic ADC-only implementation using `document_text_detection`. Creates `ImageAnnotatorClient()` without client options (line 50). Needs to switch to API key auth.
- `packages/ocr_tool/pyproject.toml` — already includes `google-cloud-vision>=3.7` dependency.
- `packages/ocr_tool/tests/test_engines/test_google.py` — 4 tests covering ADC-only credential check, missing file, successful extraction, and empty result. Needs to be updated for API key auth.
- Models use `Literal["local", "llm"]` — needs `"google"` added.
- Service dispatches only to local/llm — needs google branch.
- CLI validates only `("local", "llm")` on line 39 of `cli.py` — needs `"google"` added.

## Approach

1. **Update the existing engine** at `packages/ocr_tool/src/ocr_tool/engines/google.py` to use `GOOGLE_API_KEY` for authentication. Replace the existing ADC credential check (currently lines 25-38) with a simple `GOOGLE_API_KEY` env var lookup. Replace client creation (currently line 50) with `ImageAnnotatorClient(client_options={"api_key": key})`.

2. **Expand the mode literal** in `OcrRequest.mode` and `OcrResult.mode` from `Literal["local", "llm"]` to `Literal["local", "llm", "google"]`.

3. **Handle PDF input**: The google engine should accept both images and PDFs. Use `document_text_detection` for images and `batch_annotate_files` with inline content for PDFs (up to 5 pages synchronously). Detect file type by extension. Update the `image_path` field description to mention PDF support.

4. **Authentication**: Read `GOOGLE_API_KEY` from the environment. If not set, raise `OcrError` with code `MISSING_CREDENTIALS`. No ADC fallback — the team already has a key with the correct permissions.

5. **Keep existing engines intact**: local and llm modes remain unchanged. Google is additive.

## Constraints

- Do NOT remove or modify the existing `local` or `llm` engines — they stay as-is.
- Do NOT require Google Cloud Storage (GCS) — use inline content for PDFs (up to 5 pages per request via `batch_annotate_files`). This is a CLI tool, not a batch pipeline.
- Do NOT add interactive authentication flows or ADC fallback. The only credential source is the `GOOGLE_API_KEY` env var.
- PDF support is only for the `google` engine. Local (easyocr) and LLM engines remain image-only.
- The `google-cloud-vision` dependency is already a regular dependency in `pyproject.toml` — keep it that way.

## Dependencies (story ordering)

- US-001 (engine with API key auth + tests) must come first — everything else builds on it.
- US-002 (model/service integration) depends on US-001.
- US-003 (PDF support) depends on US-002.
- US-004 (CLI update) depends on US-002.
- US-005 (full quality gate) runs after US-002–US-004.

## Risks

1. **Google Cloud Vision SDK version compatibility**: The `google-cloud-vision` package pulls in many transitive dependencies (grpc, protobuf, google-auth). This may conflict with existing deps. Mitigate by running `uv lock` early and resolving conflicts in the first story.

2. **PDF page limit**: Inline `batch_annotate_files` supports up to 5 pages. For longer PDFs, you'd need GCS-based async processing. For now, raise a clear error if the PDF exceeds 5 pages. Document this limitation.

3. **API key permissions**: The `GOOGLE_API_KEY` must belong to a GCP project with the Cloud Vision API enabled. If the API is not enabled for the key's project, the API will return a clear permission error. The engine should surface this error message to the user.

4. **Mypy and type stubs**: `google-cloud-vision` has generated protobuf types that may not play perfectly with mypy. The existing `engines/google.py` already uses `# type: ignore[import-untyped]` on the vision import. Additional `type: ignore` comments may be needed and are acceptable.

## Changes

- **Round 1**: Authentication strategy revised from ADC-only to API key first with ADC fallback.
- **Round 2**: Added implementation notes clarifying existing files. Updated US-003 to recommend `pypdf` over deprecated `PyPDF2`.
- **Round 3**: Promoted implementation notes to a "Current State" section with specific line numbers from the actual code. Updated approach steps to reference exact locations that need changing. Tightened risk #4 to note existing `type: ignore` pattern. No structural changes to stories — reviewer confirmed plan is acceptable.
- **Round 4**: Reviewer approved plan with no further changes. Re-verified all line references against current codebase — confirmed accurate. Plan finalized.
- **Round 5**: Simplified authentication per reviewer feedback. Removed ADC fallback and multi-key chain (`GOOGLE_PLACES_API_KEY`, `GEMINI_API_KEY`). The only credential source is now `GOOGLE_API_KEY` — the team already has a key with the right API permissions. This simplifies the engine code, tests, and documentation. Removed risk #3 about API key compatibility across different key types (no longer relevant with a single key source).
