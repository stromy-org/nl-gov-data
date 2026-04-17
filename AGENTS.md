# AGENTS.md

Self-contained instructions for Codex and other agents working in `nl-gov-data`.

## Project Overview

`nl-gov-data` is a read-only FastMCP server for Dutch government data. It wraps Tweede Kamer OData v4, Rijksoverheid REST, and KOOP SRU behind source-specific and unified tools. There is no local database, ingestion pipeline, or persistence beyond process-local reference-data caching.

## Repository Structure

```text
nl-gov-data/
├── src/nlgovdata/
│   ├── adapters/          Thin upstream clients
│   ├── core/              Dataclasses, config, normalization, type maps
│   ├── mcp/               FastMCP server, tools, resources
│   ├── cli/               Operator commands
│   └── utils/             HTTP, OData, XML helpers
├── tests/
│   ├── fixtures/          Frozen representative upstream payloads
│   └── unit/              Deterministic unit tests
├── docs/
├── README.md
├── pyproject.toml
└── .env.template
```

## Commands

```bash
uv sync --all-extras
uv run pytest -v
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pyright src/nlgovdata
uv run nlgovdata list-sources
uv run nlgovdata test-connection
uv run nlgovdata serve
```

## Engineering Rules

- Keep adapters source-native and read-only.
- Put normalized cross-source behavior in `core/normalize.py`.
- Keep search/list MCP responses object-rooted with a flat `results` array.
- Keep dossier chronology object-rooted with a `timeline` array.
- Every upstream failure in unified tools must degrade to warnings, not a full failure, when partial data is still available.
- Use fixtures and mocked requesters in unit tests; reserve live shape checks for explicit smoke coverage.

## Context Management

When compacting, preserve the modified files list, the current implementation step, and any failing command output.
