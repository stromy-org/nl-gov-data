---
name: quality-check
description: Validate repo structure, core commands, and bootstrap coherence for nl-gov-data.
---

Run focused structural checks for this repo:

- `uv run pytest -q`
- `uv run ruff check src/ tests/`
- `uv run pyright src/nlgovdata`
- verify MCP tools/resources match README and docs
