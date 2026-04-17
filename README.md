# nl-gov-data

`nl-gov-data` is a thin FastMCP server over three Dutch government data products:

- Tweede Kamer OData v4
- Rijksoverheid open data REST
- KOOP SRU official publications

It keeps the source APIs visible through source-specific tools while also exposing a normalized cross-source layer for common workflows such as document search, dossier timelines, votes, activities, members, committees, ministries, and subjects.

## Status

Phases 1, 2, and 3 from [PLAN-nl-gov-data.md](/Users/williammasquelier/Repositories/stromy-org/PLAN-nl-gov-data.md) are implemented in this repo. The live connectivity command and smoke tests were exercised successfully on 2026-04-16.

## Quick Start

```bash
uv sync --all-extras
uv run pytest -v
uv run nlgovdata list-sources
uv run nlgovdata test-connection
uv run nlgovdata serve
NLGOVDATA_RUN_SMOKE=1 uv run pytest -m smoke -v
```

## Environment

Copy `.env.template` to `.env` for local overrides.

Supported variables:

- `NLGOVDATA_TK_BASE_URL`
- `NLGOVDATA_RIJK_BASE_URL`
- `NLGOVDATA_KOOP_BASE_URL`
- `NLGOVDATA_TIMEOUT_SECONDS`
- `NLGOVDATA_MAX_RETRIES`
- `NLGOVDATA_REQUEST_INTERVAL_SECONDS`
- `NLGOVDATA_CACHE_TTL_SECONDS`

## Package Layout

```text
src/nlgovdata/
  adapters/      Upstream source clients
  core/          Models, config, normalization, type maps
  mcp/           FastMCP server, tools, resources
  cli/           Local operator commands
  utils/         HTTP, OData, and XML helpers
tests/
  fixtures/      Frozen representative upstream payloads
  unit/          Adapter, normalization, MCP, and resource tests
```

## Tools

Source-specific:

- `tk_search`
- `tk_get`
- `tk_count`
- `rijksoverheid_search`
- `rijksoverheid_get`
- `koop_search`

Unified:

- `search_documents`
- `get_dossier_timeline`
- `search_activities`
- `search_votes`
- `get_member`
- `list_factions`
- `list_committees`
- `list_ministries`
- `list_subjects`

## Resources

- `data://nlgov/schema/tk`
- `data://nlgov/schema/rijksoverheid`
- `data://nlgov/schema/koop`
- `data://nlgov/doc-types`
- `data://nlgov/subjects`
- `data://nlgov/ministries`
- `data://nlgov/factions`

## Development

```bash
uv run pytest -v
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pyright src/nlgovdata
```

## Live Smoke Tests

Smoke tests are intentionally opt-in. They hit the real upstream APIs and are skipped unless `NLGOVDATA_RUN_SMOKE=1` is set.

```bash
NLGOVDATA_RUN_SMOKE=1 uv run pytest -m smoke -v
uv run nlgovdata test-connection --format text
```
