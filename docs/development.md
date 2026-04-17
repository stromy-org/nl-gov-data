# Development

## Setup

```bash
uv sync --all-extras
cp .env.template .env
```

## Quality Checks

```bash
uv run pytest -v
uv run ruff check src/ tests/
uv run pyright src/nlgovdata
NLGOVDATA_RUN_SMOKE=1 uv run pytest -m smoke -v
uv run nlgovdata test-connection --format text
```

## Test Strategy

- Use `tests/fixtures/` for representative frozen payloads.
- Mock HTTP through injected requester objects instead of real network calls.
- Keep live upstream verification in smoke tests and `nlgovdata test-connection`.
