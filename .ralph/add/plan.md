# Plan: Add Google Cloud Vision OCR Engine with PDF Support

## Summary

Replace the low-quality local OCR (easyocr) and expensive LLM-based OCR with Google Cloud Vision API as the primary OCR engine. The Google Cloud Vision API provides high-quality text extraction at reasonable cost and natively supports both images and PDFs through the same SDK (`google-cloud-vision`). The CLI mode literal and models need to expand to accommodate the new `google` engine, and PDF input needs to be handled as a new file type.

## Approach

1. **Add a new engine module** at `packages/ocr_tool/src/ocr_tool/engines/google.py` that wraps the `google-cloud-vision` Python SDK. Use `document_text_detection` for images and `batch_annotate_files` for PDFs (inline content, up to 5 pages synchronously — sufficient for a CLI tool).

2. **Expand the mode literal** in `OcrRequest` from `Literal["local", "llm"]` to `Literal["local", "llm", "google"]` so the CLI can route to the new engine.

3. **Handle PDF input**: The current code assumes image input (validates with `PIL.Image.open`). The google engine should accept both images and PDFs. The service layer needs to detect file type and call the appropriate Vision API method. The `image_path` field semantics expand to "input file path" (images + PDFs). Consider renaming to `input_path` or keeping as-is with documentation.

4. **Authentication**: Support API key authentication first, then fall back to Application Default Credentials (ADC). The engine should check for API keys in this order: `GOOGLE_API_KEY`, `GOOGLE_PLACES_API_KEY`, `GEMINI_API_KEY`. If any is found, create the `ImageAnnotatorClient` with `client_options={"api_key": key}`. If no API key is found, fall back to ADC (`GOOGLE_APPLICATION_CREDENTIALS` or `google.auth.default()`). Raise `OcrError` with code `MISSING_CREDENTIALS` only if all methods fail.

5. **Keep existing engines intact**: local and llm modes remain unchanged. Google is additive.

## Implementation Notes

- `google-cloud-vision>=3.7` is already in `packages/ocr_tool/pyproject.toml` and `engines/google.py` already exists with a basic ADC-only implementation. US-001 must update this file to add API key auth support and tests.
- The existing `engines/google.py` creates `ImageAnnotatorClient()` without client options. US-001 must refactor client creation to check API key env vars first.

## Constraints

- Do NOT remove or modify the existing `local` or `llm` engines — they stay as-is.
- Do NOT require Google Cloud Storage (GCS) — use inline content for PDFs (up to 5 pages per request via `batch_annotate_files`). This is a CLI tool, not a batch pipeline.
- Do NOT add interactive authentication flows. Credentials come from env vars only.
- PDF support is only for the `google` engine. Local (easyocr) and LLM engines remain image-only.
- Keep the `google-cloud-vision` dependency scoped — it should be a regular dependency in `pyproject.toml`, not optional.

## Dependencies (story ordering)

- US-001 (engine with API key auth + tests) must come first — everything else builds on it.
- US-002 (model/service integration) depends on US-001.
- US-003 (PDF support) depends on US-002.
- US-004 (CLI update) depends on US-002.
- US-005 (tests) can be done alongside or after US-002–US-004.

## Risks

1. **Google Cloud Vision SDK version compatibility**: The `google-cloud-vision` package pulls in many transitive dependencies (grpc, protobuf, google-auth). This may conflict with existing deps. Mitigate by running `uv lock` early and resolving conflicts in the first story.

2. **PDF page limit**: Inline `batch_annotate_files` supports up to 5 pages. For longer PDFs, you'd need GCS-based async processing. For now, raise a clear error if the PDF exceeds 5 pages. Document this limitation.

3. **API key compatibility**: Not all Google API keys may have the Cloud Vision API enabled. `GEMINI_API_KEY` (Google AI Studio) and `GOOGLE_PLACES_API_KEY` may be scoped to different APIs. If the Vision API is not enabled for the key's project, the API will return a clear permission error. The engine should surface this error message to the user.

4. **Mypy and type stubs**: `google-cloud-vision` has generated protobuf types that may not play perfectly with mypy. The implementer may need `# type: ignore` on specific imports or a mypy plugin config. This is acceptable.

## Changes

- **Authentication strategy revised** (reviewer feedback round 1): The original plan required `GOOGLE_APPLICATION_CREDENTIALS` or ADC. The reviewer has existing API keys (`GOOGLE_API_KEY`, `GOOGLE_PLACES_API_KEY`, `GEMINI_API_KEY`) and wants to reuse them. The plan now checks for these API keys first (in priority order) and creates the client with `client_options={"api_key": key}`. ADC remains as a fallback. This is simpler for users who already have Google API keys configured.
- **US-001 acceptance criteria updated** to reflect API key auth support and the env var lookup order.
- **Risk #3 updated** from "credential setup friction" to "API key compatibility" since the main auth path is now API keys.
- **Re-review refinements** (round 2): Added implementation notes section clarifying that `google-cloud-vision` dep and a basic `engines/google.py` already exist from a partial US-001 implementation — US-001 must update (not create from scratch) the engine to add API key auth. Updated US-003 notes to recommend `pypdf` instead of deprecated `PyPDF2`.
