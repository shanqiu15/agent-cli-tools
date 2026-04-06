# Plan: Port gpt-minions Tools to Python CLI Packages

## Summary

Rewrite 8 standalone tools from the gpt-minions TypeScript multi-agent system as Python CLI packages in this monorepo. Each tool becomes its own package under `packages/`, following the established patterns from `cli_common` and `ocr_tool`: Typer CLI, Pydantic models, structured JSON output, and clean service-layer separation.

## Approach

Each tool package follows the same 3-layer architecture already established:

- **cli.py** — Typer commands, input validation, catches exceptions, emits JSON via `cli_common.io`
- **models.py** — Pydantic request/response models
- **service.py** — Business logic (API calls, subprocess management, file I/O)
- **errors.py** — Package-specific exception inheriting `cli_common.errors.ToolException`

Packages are built in dependency order. Phase 1 tools (web_search, web_crawl, bash) have no cross-dependencies and can be built in any order. Phase 2 tools (browser, memory) are more complex but still independent. Phase 3 tools (sonar, image_gen, cron) are nice-to-haves.

All tools that call external APIs must read credentials from environment variables, never hardcode them, and fail with a clear `MISSING_CREDENTIALS` error if the key is absent.

### Key library choices

| Tool | Key dependency |
|------|---------------|
| web_search_tool | `httpx` (Serper API) |
| web_crawl_tool | `httpx` (crawl4ai service) |
| bash_tool | `subprocess` (stdlib) |
| browser_tool | `playwright` |
| memory_tool | stdlib `pathlib` + `json` |
| sonar_tool | `httpx` (Perplexity API) |
| image_gen_tool | `httpx` (Gemini API) |
| cron_tool | `httpx` (gateway API) |

Since `httpx` is used by multiple tools, it should be added as a dependency of `cli_common` so all packages can share it without each declaring it separately. Alternatively, each package declares it independently — either approach works. The simpler path is each package declares its own `httpx` dependency since `cli_common` should stay minimal.

## Constraints

- **Do not modify `cli_common` unless something is genuinely shared** — e.g., an HTTP client helper used by 3+ packages. Individual API wrappers stay in their own packages.
- **No cross-package imports** — tools must not depend on each other, only on `cli_common`.
- **No interactive behavior** — all input via CLI args or env vars.
- **No AI attribution in commits**.
- **Skip `minions_cli`** (meta-tool, not portable) and **`langfuse_tools`** (tightly coupled to Langfuse).
- **Skip `coding_agent`** — thin wrapper around `claude -p`, not worth a package.
- Tests that hit external APIs must be marked `@pytest.mark.external` and skipped without `--all`.

## Dependencies (story ordering)

```
US-001 (cli_common httpx helper) — no deps
US-002 (web_search_tool) — after US-001
US-003 (web_crawl_tool) — after US-001
US-004 (bash_tool) — no deps (stdlib only)
US-005 (browser_tool) — no deps on other tools
US-006 (memory_tool) — no deps on other tools
US-007 (sonar_tool) — after US-001
US-008 (image_gen_tool) — after US-001
US-009 (cron_tool) — after US-001
```

US-001 is a small enabler that adds a shared `httpx` helper to `cli_common` for making API calls with standard error handling. All API-calling tools benefit from it.

## Risks

1. **crawl4ai dependency** — The original uses a crawl4ai *service* (HTTP endpoint), not the crawl4ai Python library directly. The implementer should use `httpx` to call a crawl4ai service URL from `CRAWL4AI_BASE_URL` env var, matching the original design. If we want a self-contained fallback, `httpx` + `readability-lxml` can extract content from raw HTML.
2. **Playwright installation** — `browser_tool` requires Playwright browsers to be installed (`playwright install chromium`). Tests should mock the browser or skip if not installed.
3. **External API tests** — All API-calling tools need the `@pytest.mark.external` marker on integration tests. Unit tests must mock HTTP calls.
4. **Scope creep on browser_tool** — The original has 12 action types. Start with the core set (navigate, snapshot, click, type, screenshot) and add the rest incrementally within the same story.
5. **Memory tool path safety** — The memory tool writes files to disk. It must validate paths to prevent directory traversal attacks.
