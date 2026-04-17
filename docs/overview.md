# Overview

`nl-gov-data` is organized around four layers:

- `adapters/`: thin HTTP clients for TK, Rijksoverheid, and KOOP
- `core/`: immutable output models, config, normalization, and shared type maps
- `mcp/`: FastMCP tools and resources
- `cli/`: local commands for serving and connectivity checks

Dependency direction is one-way: `cli -> mcp -> adapters -> core`, with `utils` shared by adapters and MCP resources.
