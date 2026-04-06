## Purpose

This repository contains composable Python CLI tools for LLM agents. Each package in this monorepo is a standalone CLI tool that exposes a stable, machine-readable interface for agent use.

The repository is optimized for:
- agent-friendly automation
- predictable and deterministic behavior
- typed interfaces
- maintainable package structure
- fast and consistent package bootstrapping

This file tells coding agents how to work in this repository.

---

## What You Are Building

Each package in `packages/` is a single CLI tool capability.

Examples:
- `file_tool`
- `git_tool`
- `browser_tool`

There is also a shared package:

- `cli_common`

`cli_common` contains shared code used by multiple tools, such as:
- common response and error models
- shared exception classes
- JSON IO helpers
- common CLI helper utilities
- validation helpers that are broadly reusable

Do not duplicate shared foundational code across packages. If logic is reused by multiple tools and is generic enough, move it into `cli_common`.

---

## Expected Stack

Use these defaults unless there is a strong reason not to:

- Python 3.12+
- `uv` for package management
- `typer` for CLI
- `pydantic` for schemas
- `pytest` for tests
- `ruff` for lint and formatting
- `mypy` for type checking

---

## Standard Repository Layout

Use this layout:

```text
repo/
  packages/
    cli_common/
      pyproject.toml
      src/cli_common/
        __init__.py
        models.py
        errors.py
        io.py
        utils.py
      tests/
    <tool_name>/
      pyproject.toml
      src/<tool_name>/
        __init__.py
        cli.py
        models.py
        service.py
        errors.py
      tests/
        test_cli.py
        test_service.py
  docs/
  pyproject.toml
  uv.lock
  README.md
  AGENTS.md
  CODING_RULES.md
  PACKAGE_TEMPLATE.md

---
## Coding Rules

@.claude/CODING_RULES.md

---

Commit Message Rules
* No AI attribution in commits

Rules:
- Do NOT include any AI attribution in commit messages
- Specifically:
  - Co-Authored-By: Claude
  - Co-Authored-By: ChatGPT
  - or any similar AI-generated attribution line