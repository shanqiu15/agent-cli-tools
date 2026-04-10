# Progress

## Implementer — US-001 (attempt 1)
- Changed: `packages/ocr_tool/src/ocr_tool/engines/google.py` (replaced ADC auth with GOOGLE_API_KEY env var, client_options={'api_key': key})
- Changed: `packages/ocr_tool/tests/test_engines/test_google.py` (4 tests updated for API key auth: missing key, missing file, successful extraction with API key verification, empty result)
- All 4 tests pass
- Criteria believed met: all 8 (dependency exists, function signature correct, API key auth, MISSING_CREDENTIALS error, IMAGE_NOT_FOUND error, document_text_detection usage, 4 test cases covering required scenarios)
- Blockers: none

## Evaluator — US-001 (attempt 1)
- Verdict: PASS
- Tests: 4/4 passed in 0.70s, ruff check/format clean
- Criterion 1: PASS — google-cloud-vision>=3.7 in pyproject.toml
- Criterion 2: PASS — no dependency changes needed, lock file intact
- Criterion 3: PASS — extract_text_google(file_path: Path, model: str | None = None) -> str exists
- Criterion 4: PASS — reads GOOGLE_API_KEY, passes client_options={'api_key': key}
- Criterion 5: PASS — raises OcrError(code="MISSING_CREDENTIALS")
- Criterion 6: PASS — raises OcrError(code="IMAGE_NOT_FOUND")
- Criterion 7: PASS — uses ImageAnnotatorClient + document_text_detection
- Criterion 8: PASS — 4 tests: missing key, missing file, successful extraction with API key assert, empty result

## Implementer — US-002 (attempt 1)
- Deleted: `packages/ocr_tool/src/ocr_tool/engines/llm.py`
- Deleted: `packages/ocr_tool/tests/test_engines/test_llm.py`
- Changed: `packages/ocr_tool/pyproject.toml` (removed anthropic>=0.39.0 dependency)
- Changed: `packages/ocr_tool/src/ocr_tool/models.py` (mode literal → Literal['local', 'google'], default 'google', added explicit_mode field)
- Changed: `packages/ocr_tool/src/ocr_tool/service.py` (google dispatch, auto-fallback logic, MISSING_CREDENTIALS on explicit mode)
- Changed: `packages/ocr_tool/src/ocr_tool/cli.py` (mode default None → detect explicit, validate 'local'/'google')
- Changed: `packages/ocr_tool/tests/test_service.py` (new tests: google dispatch, auto-fallback, explicit google fails without key)
- Changed: `packages/ocr_tool/tests/test_cli.py`, `test_integration.py`, `test_models.py` (updated for google mode, fixed subcommand invocation)
- All 30 tests pass, uv lock updated
- Criteria believed met: all 13
- Blockers: none

## Evaluator — US-002 (attempt 1)
- Verdict: FAIL
- Tests: 30/30 passed in 4.79s, ruff check clean
- Ruff format: FAIL — `tests/test_integration.py` needs reformatting (1 file would be reformatted)
- Criteria 1-2: PASS — llm.py and test_llm.py deleted
- Criteria 3: PASS — anthropic removed from pyproject.toml
- Criteria 4-5: PASS — mode literal is Literal['local', 'google'], default 'google'
- Criteria 6-10: PASS — service dispatch, fallback, MISSING_CREDENTIALS, actual mode in result, correct model_used
- Criteria 11-12: PASS — no llm/anthropic references, new tests for google dispatch/fallback/explicit fail
- Criteria 13: PASS — pytest exits 0
- Fix needed: run `uv run ruff format tests/test_integration.py` and recommit

## Implementer — US-002 (attempt 2)
- Changed: `packages/ocr_tool/tests/test_integration.py` (ruff format fix — only change needed)
- All 30 tests pass, ruff format clean, ruff check clean
- Criteria believed met: all 13 (1-13 were already met in attempt 1; the only issue was ruff formatting)
- Blockers: none

## Evaluator — US-002 (attempt 2)
- Verdict: PASS
- Tests: 30/30 passed in 3.37s, ruff check clean, ruff format clean (15 files already formatted)
- Criteria 1-2: PASS — llm.py and test_llm.py deleted
- Criteria 3: PASS — anthropic removed from pyproject.toml
- Criteria 4-5: PASS — mode literal is Literal['local', 'google'], default 'google'
- Criteria 6-10: PASS — service imports/dispatches google, fallback works, MISSING_CREDENTIALS on explicit, mode reflects actual engine, correct model_used values
- Criteria 11-12: PASS — no llm/anthropic references, new tests for google dispatch/fallback/explicit fail
- Criteria 13: PASS — pytest exits 0

## Implementer — US-003 (attempt 1)
- Changed: `packages/ocr_tool/src/ocr_tool/engines/google.py` (added PDF support via batch_annotate_files, file type validation with INVALID_FILE error, PDF_TOO_LARGE error for >5 pages, refactored into _extract_text_from_image and _extract_text_from_pdf helpers)
- Changed: `packages/ocr_tool/src/ocr_tool/models.py` (updated image_path field description to mention PDF support)
- Changed: `packages/ocr_tool/tests/test_engines/test_google.py` (added 3 new tests: successful PDF extraction with batch_annotate_files mock, PDF page limit error, unsupported file type error)
- All 33 tests pass, ruff check and format clean
- Criteria believed met: all 6 (PDF via batch_annotate_files with InputConfig, PDF_TOO_LARGE error, INVALID_FILE error, updated field description, 3 new unit tests, default output_path for PDF is <stem>.txt)
- Blockers: none

## Evaluator — US-003 (attempt 1)
- Verdict: PASS
- Tests: 33/33 passed in 3.54s, ruff check clean, ruff format clean
- Criterion 1: PASS — extract_text_google accepts .pdf, uses batch_annotate_files with InputConfig(mime_type='application/pdf', content=bytes)
- Criterion 2: PASS — raises OcrError(code="PDF_TOO_LARGE") when total_pages > 5, message includes page count and limit
- Criterion 3: PASS — raises OcrError(code="INVALID_FILE") for unsupported extensions, checked against _SUPPORTED_IMAGE_EXTENSIONS set
- Criterion 4: PASS — image_path description updated to "Path to the input image or PDF file"
- Criterion 5: PASS — 3 new tests: successful PDF extraction (mocked batch_annotate_files), PDF page limit error, unsupported file type error
- Criterion 6: PASS — service.py uses .with_suffix(".txt") which produces <stem>.txt for PDFs same as images

## Implementer — US-004 (attempt 1)
- Changed: `packages/ocr_tool/src/ocr_tool/cli.py` (updated --image help text to mention PDF support in google mode)
- Changed: `packages/ocr_tool/src/ocr_tool/service.py` (added UNSUPPORTED_FILE_TYPE check for PDF + local mode)
- Changed: `packages/ocr_tool/tests/test_cli.py` (6 new tests: default google mode, explicit local mode, invalid mode 'llm', PDF with local mode error, PDF with google mode accepted, plus existing tests retained)
- Changed: `packages/ocr_tool/tests/test_service.py` (1 new test: PDF with local mode raises UNSUPPORTED_FILE_TYPE)
- All 39 tests pass, ruff check and format clean
- Criteria believed met: all 10 (default google routing, explicit local routing, mode validation local/google only, llm mode error, help text mentions PDF, PDF accepted with google, PDF rejected with local, mode/model_used in output, no stale llm references, new tests cover all 4 required scenarios)
- Blockers: none

## Evaluator — US-004 (attempt 1)
- Verdict: PASS
- Tests: 39/39 passed in 3.56s, ruff check clean, ruff format clean
- Criterion 1: PASS — test_default_google_mode mocks run_ocr, verifies mode=="google" and explicit_mode==False
- Criterion 2: PASS — test_explicit_local_mode verifies --mode local routing
- Criterion 3: PASS — cli.py validates effective_mode in ("local", "google") only
- Criterion 4: PASS — test_invalid_mode_llm asserts INVALID_MODE error for --mode llm
- Criterion 5: PASS — help text: "Path to the input image or PDF file (PDF supported in google mode only)"
- Criterion 6: PASS — test_pdf_with_google_mode_accepted confirms PDF passes with google mode
- Criterion 7: PASS — service.py raises UNSUPPORTED_FILE_TYPE for PDF+local, tested in both CLI and service tests
- Criterion 8: PASS — OcrResult includes mode and model_used fields, verified in test assertions
- Criterion 9: PASS — only llm references are in test that verifies it's rejected
- Criterion 10: PASS — 4 new CLI tests: default google (mocked), explicit local, PDF+local error, invalid mode llm

## Implementer — US-005 (attempt 1)
- Changed: `packages/ocr_tool/pyproject.toml` (added mypy config with cli_common ignore_missing_imports override)
- All 39 tests pass, ruff check clean, ruff format clean, mypy exits 0 with no errors
- uv lock --check passes
- Only "llm" reference is test_invalid_mode_llm which verifies llm mode is rejected (intentional)
- Criteria believed met: all 7
- Blockers: none

## Evaluator — US-005 (attempt 1)
- Verdict: PASS
- Tests: 39/39 passed in 3.61s
- Criterion 1: PASS — pytest exits 0, 39 passed
- Criterion 2: PASS — ruff check clean
- Criterion 3: PASS — ruff format clean, 15 files already formatted
- Criterion 4: PASS — mypy exits 0, "Success: no issues found in 8 source files"
- Criterion 5: PASS — all Google Vision API calls mocked via @patch and monkeypatch
- Criterion 6: PASS — no llm/anthropic refs in source; only test_invalid_mode_llm (rejection test) in tests
- Criterion 7: PASS — uv lock --check resolves 79 packages cleanly
