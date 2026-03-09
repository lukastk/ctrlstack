# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ctrlstack** is a Python library that lets you define a `Controller` class once and automatically generates CLI apps (Typer), REST APIs (FastAPI), remote client proxies, and remote CLIs from it. Version 0.1.3, Python 3.11+.

## Literate Programming with nblite

This project uses **nblite** for literate programming. See `NBLITE_INSTRUCTIONS.md` for the full nblite reference.

**Export pipeline (from `nblite.toml`):**
- `nbs -> pts` and `nbs -> lib` (nbs is source of truth for the library)
- `nbs_tests -> pts_tests` and `nbs_tests -> lib_tests` (nbs is source of truth for tests)

**Directory layout:**

| Code location | Path | Format |
|--------------|------|--------|
| `nbs` | `nbs/ctrlstack/` | `.ipynb` (source of truth, gitignored) |
| `pts` | `pts/ctrlstack/` | `.pct.py` (plaintext notebooks) |
| `lib` | `src/ctrlstack/` | `.py` (auto-generated, gitignored except `__init__.py`) |
| `nbs_tests` | `nbs/tests/` | `.ipynb` (gitignored) |
| `pts_tests` | `pts/tests/` | `.pct.py` |
| `lib_tests` | `src/tests/` | `.py` (auto-generated, gitignored) |

### Critical workflow rules

1. **Edit `.pct.py` files in `pts/`** — never edit `src/ctrlstack/**/*.py` directly (auto-generated and gitignored).
2. **After editing `.pct.py` files, run `nbl export --reverse`** to sync changes back to `.ipynb`, then `nbl export` to regenerate the library. Otherwise your pts changes will be overwritten by the older nbs versions.
3. **Exception: `__init__.py`** — nblite skips dunder files during export, so `src/ctrlstack/__init__.py` must be edited directly.

### Notebook cell directives

Percent notebooks use `# %%` to delimit cells. Key directives:

| Directive | Purpose |
|-----------|---------|
| `#\|default_exp module` | Set export target module (once per notebook) |
| `#\|export` | Export this cell to the module |
| `#\|exporti` | Export but exclude from `__all__` (internal) |
| `#\|hide` | Hide from documentation (setup/testing cells) |

Cells without `#|export` or `#|exporti` are not exported — use them for inline tests and examples (literate programming style).

## Commands

```bash
# Environment setup
uv sync --all-extras          # Install dependencies
nbl install-hooks             # Install nblite git hooks (required for commits)

# Development
nbl export                    # Export nbs → pts and nbs → lib
nbl export --reverse          # Sync pts changes back to nbs
nbl clean                     # Clean notebook outputs
nbl test                      # Test that all notebooks execute without errors

# Testing (requires nbl export first to generate src/tests/)
uv run pytest                 # Run all tests
uv run pytest src/tests/test_cli.py  # Run a single test file
uv run pytest -k test_bar     # Run tests matching a pattern

# Dependencies
uv add <package>              # Add a dependency
uv sync --upgrade --all-extras  # Upgrade all dependencies
```

## Architecture

### Controller Pattern

The core abstraction is `Controller` (ABC in `pts/ctrlstack/controller.pct.py`). Methods are decorated to indicate their type:

- `@ctrl_query_method` — read-only operations (→ GET endpoints in server, query commands in CLI)
- `@ctrl_cmd_method` — state-changing operations (→ POST endpoints, command in CLI)
- `@ctrl_method(method_type, group)` — generic with optional routing group

### Exposure Layers

Each layer reads Controller method metadata (`_is_controller_method`, `_controller_method_type`, `_controller_method_group`) and generates the appropriate interface:

| Layer | Source | Purpose |
|-------|--------|---------|
| CLI | `pts/ctrlstack/cli.pct.py` | Creates Typer app from Controller. Handles Pydantic/dict args as JSON strings. |
| Server | `pts/ctrlstack/server.pct.py` | Creates FastAPI app. QUERY→GET, COMMAND→POST. Optional API key auth (`X-API-Key`). |
| Remote Controller | `pts/ctrlstack/remote_controller.pct.py` | Dynamically creates proxy class that calls remote server. Marshalls params to HTTP. |
| Remote CLI | `pts/ctrlstack/remote_cli.pct.py` | CLI that calls remote server. Has local server lifecycle commands (start/stop/restart/status). |
| Controller App | `pts/ctrlstack/controller_app.pct.py` | `ControllerApp` for runtime method registration via `@capp.register_cmd()` / `@capp.register_query()`. |

### Entry Point

CLI entry point: `ctrlstack.cli.app:app` (defined in pyproject.toml as `ctrlstack` command).
