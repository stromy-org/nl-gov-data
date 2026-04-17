# CLAUDE.md

## Project Overview

`nl-gov-data` is a read-only FastMCP server that wraps Dutch government APIs. The repo has no local persistence layer. Adapters fetch upstream data, `core/normalize.py` converts it to stable dataclasses, and MCP tools expose both source-native and unified contracts.

## Repository Structure

```text
nl-gov-data/
├── src/nlgovdata/
│   ├── adapters/
│   │   ├── base.py
│   │   ├── tk.py
│   │   ├── rijksoverheid.py
│   │   └── koop.py
│   ├── core/
│   │   ├── config.py
│   │   ├── normalize.py
│   │   ├── schema.py
│   │   └── types.py
│   ├── mcp/
│   │   ├── dependencies.py
│   │   ├── resources.py
│   │   ├── server.py
│   │   ├── tools_koop.py
│   │   ├── tools_rijk.py
│   │   ├── tools_tk.py
│   │   └── tools_unified.py
│   ├── cli/
│   │   └── main.py
│   └── utils/
│       ├── http.py
│       ├── odata.py
│       └── xml.py
├── tests/
│   ├── fixtures/
│   └── unit/
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

## Development Rules

- Keep adapters thin. Parsing and normalization belong in `core/normalize.py` and `utils/xml.py`.
- Preserve source-native semantics in source-specific tools.
- Unified search/list responses stay flat under `results`; dossier chronology stays under `timeline`.
- Do not add a local database or ingestion pipeline in this repo.
- Prefer fixture-backed deterministic unit tests over live tests.

## Skill Workflow

- `/quality-check` for repo structure and bootstrap hygiene
- `/instruction-audit` for instruction maintenance only
