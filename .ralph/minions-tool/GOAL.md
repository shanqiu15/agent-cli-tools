# Goal

implement all the tools from gpt-minions into this repo as python cli tools. gpt-minions Tool Inventory

  The project is a TypeScript multi-agent system with these standalone tools:

  ┌─────────────────────────┬───────────────────────────────────┬──────────────┐
  │          Tool           │            Description            │  Complexity  │
  ├─────────────────────────┼───────────────────────────────────┼──────────────┤
  │ bash                    │ Execute shell commands            │ Low          │
  │                         │                                   │ (trivial)    │
  ├─────────────────────────┼───────────────────────────────────┼──────────────┤
  │ web_search              │ Google search via Serper API      │ Low          │
  ├─────────────────────────┼───────────────────────────────────┼──────────────┤
  │ web_crawl               │ Crawl web pages via crawl4ai      │ Low-Med      │
  ├─────────────────────────┼───────────────────────────────────┼──────────────┤
  │ browser                 │ Playwright browser automation (12 │ High         │
  │                         │  actions)                         │              │
  ├─────────────────────────┼───────────────────────────────────┼──────────────┤
  │ sonar_search            │ Perplexity Sonar search with      │ Low          │
  │                         │ citations                         │              │
  ├─────────────────────────┼───────────────────────────────────┼──────────────┤
  │ generate_image          │ Image gen via Gemini              │ Low          │
  ├─────────────────────────┼───────────────────────────────────┼──────────────┤
  │ memory_search/get/write │ File-based agent memory system    │ Medium       │
  ├─────────────────────────┼───────────────────────────────────┼──────────────┤
  │ cron_schedule           │ Cron job scheduling               │ Medium       │
  ├─────────────────────────┼───────────────────────────────────┼──────────────┤
  │ coding_agent            │ Run Claude Code with a spec file  │ Low          │
  ├─────────────────────────┼───────────────────────────────────┼──────────────┤
  │ minions_cli             │ System introspection (meta-tool)  │ Skip         │
  ├─────────────────────────┼───────────────────────────────────┼──────────────┤
  │ langfuse_tools          │ Observability trace inspection    │ Low-Med      │
  └─────────────────────────┴───────────────────────────────────┴──────────────┘

  Proposed Plan

  Rewrite as Python CLI tools in packages/, reusing cli_common. Prioritized by
  usefulness as standalone agent tools:

  Phase 1 — High-value, lower complexity

  1. web_search_tool — Google search via Serper API (SERPER_API_KEY)
  2. web_crawl_tool — Fetch & extract page content (use httpx + readability-lxml or
   crawl4ai)
  3. bash_tool — Sandboxed shell execution with timeout & output limits

  Phase 2 — High-value, higher complexity

  4. browser_tool — Playwright automation (navigate, snapshot, click, fill,
  screenshot, tabs)
  5. memory_tool — File-based memory with search/read/write subcommands

  Phase 3 — Nice to have

  6. sonar_tool — Perplexity search with citations
  7. image_gen_tool — Image generation via Gemini API
  8. cron_tool — Job scheduling with cron/interval/one-shot support

  Skip

  - minions_cli — meta-tool, not portable
  - langfuse_tools — tightly coupled to Langfuse setup
  - coding_agent — thin wrapper around claude -p
