# Development Patterns

- Adapters stay thin and source-native.
- Shared contracts live in `core/schema.py`.
- Source-specific parsing helpers belong in `utils/odata.py` and `utils/xml.py`.
- Unified behavior belongs in `core/normalize.py` and `mcp/tools_unified.py`.
- Use immutable dataclasses for normalized outputs.
