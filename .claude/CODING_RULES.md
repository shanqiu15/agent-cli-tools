## `CODING_RULES.md`

# CODING_RULES.md

## 1. Purpose

This repository contains composable Python CLI tools for LLM agents. Each package is a standalone CLI capability with a stable machine-readable interface.

The codebase is optimized for:
- agent consumption
- reliability
- determinism
- clarity
- maintainability
- reusable shared foundations through `cli_common`

---

## 2. Core Principles

### 2.1 Agent-first interfaces
Every tool must be easy for an LLM agent to call correctly.

Rules:
- prefer JSON input / JSON output
- keep commands explicit and predictable
- avoid interactive prompts
- avoid hidden side effects
- return structured errors
- make success and failure easy to parse

### 2.2 Clarity over cleverness
Write boring, obvious Python.

Rules:
- prefer simple functions over abstractions
- prefer explicit control flow over magic
- avoid premature generalization
- avoid framework-heavy designs
- do not introduce indirection unless it removes real duplication

### 2.3 Deterministic behavior
Tools should behave consistently for the same input.

Rules:
- validate all inputs
- avoid non-deterministic output ordering unless required
- sort output where appropriate
- make side effects explicit
- do not rely on ambient shell state unless documented

### 2.4 Small, composable packages
Each package should do one thing well.

Rules:
- one package = one tool capability
- keep package boundaries clean
- shared generic code belongs in `cli_common`
- do not create giant “misc utils” modules

---

## 3. Repository Standards

### 3.1 Stack
Use the following defaults unless there is a strong reason not to:

- Python 3.12+
- `uv`
- `typer`
- `pydantic`
- `pytest`
- `ruff`
- `mypy`

### 3.2 Monorepo structure

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
    file_tool/
      pyproject.toml
      src/file_tool/
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
```

### 3.3 Package naming
Rules:
- package names must be short, descriptive, and capability-based
- use snake_case for Python package directories
- avoid vague names like `utils`, `common_tool`, `misc`
- CLI command names should be stable and human-readable

Good:
- `file_tool`
- `git_tool`
- `browser_tool`

Bad:
- `toolkit`
- `helpers`
- `agent_utils`

---

## 4. Shared Package Rules: `cli_common`

`cli_common` is the shared base package for reusable types and utilities.

Allowed in `cli_common`:
- base request/response wrappers
- shared error models and error helpers
- shared exception types
- JSON serialization/parsing helpers
- stdout/stderr helpers
- stable reusable protocol types

Not allowed in `cli_common`:
- package-specific service logic
- tool-specific workflows
- code used by only one package unless it is clearly foundational
- random helper accumulation without a clear ownership model

Rule:
Shared code must be generic, broadly useful, and stable.

If code is specific to one tool, keep it in that tool package.

---

## 5. CLI Design Standards

### 5.1 Non-interactive by default
All CLIs must run non-interactively.

Rules:
- do not ask the user questions at runtime
- do not require terminal TTY features
- do not use menus or prompts
- all required inputs must be passed explicitly

### 5.2 JSON in / JSON out
Every tool must support machine-readable input and output.

Preferred pattern:
- input comes from `--input` as a JSON string, or from stdin if explicitly designed
- output goes to stdout as JSON
- logs and diagnostics go to stderr

Example success output:
```json
{
  "ok": true,
  "result": {
    "path": "README.md",
    "content": "hello"
  }
}
```

Example error output:
```json
{
  "ok": false,
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "Path does not exist",
    "details": {
      "path": "README.md"
    }
  }
}
```

### 5.3 Stable exit codes
Rules:
- `0` = success
- non-zero = failure
- detailed failure classification belongs in structured JSON error codes

### 5.4 No decorative terminal output
Rules:
- no emojis in CLI output
- no colored output by default
- no banners
- no chatty prose on stdout

Allowed:
- explicit `--pretty` mode if needed

---

## 6. Code Organization Standards

### 6.1 Separate CLI, models, and business logic
Do not mix CLI argument parsing with core logic.

Recommended file roles:
- `cli.py`: command definitions and request/response wiring
- `models.py`: package-specific pydantic models
- `service.py`: business logic
- `errors.py`: package-specific exceptions if needed

Shared roles:
- `cli_common.models`: shared response/error models
- `cli_common.errors`: shared exception classes
- `cli_common.io`: JSON output helpers and error emission helpers
- `cli_common.utils`: truly generic utilities

### 6.2 Keep functions small and single-purpose
Rules:
- functions should do one thing
- prefer early validation and early returns
- avoid giant functions
- extract helpers when a logical unit becomes reusable or hard to read

### 6.3 Avoid unnecessary classes
Use classes only when they model real state or behavior.

Prefer:
- plain functions
- pydantic models
- dataclasses only if needed

Do not wrap stateless logic in classes just for style.

---

## 7. Type Safety Standards

### 7.1 Type hints are required
All production code must use type hints.

Rules:
- annotate function parameters and returns
- annotate public attributes
- do not leave public interfaces untyped
- avoid `Any` unless truly necessary

### 7.2 Validate external input at boundaries
Rules:
- parse all external structured input with `pydantic`
- never trust raw CLI JSON
- convert raw input into typed models immediately
- internal code should operate on validated typed objects
- all structured JSON output must be emitted from Pydantic models rather than hand-built dictionaries

---

## 8. Error Handling Standards

### 8.1 Use structured, intentional errors
Rules:
- expected operational failures must be handled
- define stable error codes
- messages should be concise and specific
- include details that help the caller recover

Good error codes:
- `INVALID_INPUT`
- `FILE_NOT_FOUND`
- `PERMISSION_DENIED`
- `TIMEOUT`
- `COMMAND_FAILED`
- `INTERNAL_ERROR`

### 8.2 Never swallow exceptions silently
Rules:
- do not use bare `except:`
- do not hide unexpected failures
- wrap expected failures cleanly
- convert unknown failures into safe structured internal errors

### 8.3 Keep user-facing errors clean
Rules:
- do not dump raw tracebacks to stdout
- do not leak secrets in error messages
- internal debug info may go to stderr in debug mode

---

## 9. Testing Standards

### 9.1 Every package must have tests
Minimum required:
- input validation test
- success path test
- expected failure test
- CLI-level smoke test

### 9.2 Test behavior, not implementation trivia
Rules:
- prefer black-box tests
- assert outputs, side effects, and error behavior
- avoid coupling tests to private implementation details

### 9.3 Keep tests deterministic
Rules:
- no network in unit tests unless explicitly marked
- no dependency on wall clock time unless mocked
- no dependency on local machine state unless isolated with fixtures
- use temp directories for filesystem tests

---

## 10. Dependency Standards

### 10.1 Keep dependencies minimal
Rules:
- prefer stdlib when sufficient
- do not pull large frameworks for trivial tasks
- avoid overlapping dependencies

### 10.2 Prefer mature, boring libraries
Good libraries are:
- well maintained
- widely used
- simple to understand
- compatible with automation use cases

### 10.3 Package dependency boundaries

Rules:
- CLI tool packages must NOT depend on each other
- CLI packages may ONLY depend on `cli_common` for shared functionality
- do not import or reuse code directly from another CLI package
- if shared functionality or types are needed across multiple CLI packages, move them into `cli_common`
- `cli_common` is the only allowed shared dependency between tool packages

---

## 11. Logging Standards

### 11.1 Logging is for diagnostics, not output contracts
Rules:
- structured results go to stdout
- logs go to stderr
- do not mix logs into machine-readable stdout

### 11.2 Default logging should be quiet
Rules:
- log only important operational information
- support verbose/debug mode explicitly
- do not spam per-step logs unless debug is enabled

---

## 12. Security Standards

### 12.1 Treat all inputs as untrusted
Rules:
- validate paths
- validate command args
- validate URLs and file operations
- reject malformed or ambiguous inputs

### 12.2 Principle of least surprise
Rules:
- destructive actions must be explicit
- no hidden file writes
- no hidden network calls
- no hidden subprocess execution

### 12.3 Never hardcode secrets
Rules:
- secrets must come from environment or explicit config
- never commit credentials
- never log secrets or sensitive tokens

---

## 13. Definition of Done

A package is not complete until all of the following are true:

- code is formatted and lint-clean
- mypy passes
- tests pass
- CLI works end-to-end
- outputs are structured and stable
- errors are machine-readable
- no interactive behavior exists
- README explains purpose, input, output, and examples

---

## 14. Non-Negotiable Anti-Patterns

Do not:
- mix human prose with machine output on stdout
- build interactive CLIs
- create giant utility dumping grounds
- duplicate shared foundational code that belongs in `cli_common`
- move package-specific code into `cli_common`
- add abstractions for hypothetical future flexibility
- skip type hints
- accept loosely shaped dicts deep into the codebase
- print stack traces as part of normal error handling
- add dependencies casually