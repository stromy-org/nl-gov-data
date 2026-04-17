"""Source-specific KOOP tools."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from nlgovdata.mcp.dependencies import ServiceContainer


def register_koop_tools(mcp: FastMCP, services: ServiceContainer) -> None:
    @mcp.tool
    def koop_search(
        query: str,
        collection: str = "officielepublicaties",
        max_records: int = 50,
        start_record: int = 1,
        sort: str | None = None,
    ) -> dict[str, Any]:
        """Run a native KOOP SRU CQL search and return parsed source records."""
        return services.koop.search(
            query,
            collection=collection,
            max_records=max_records,
            start_record=start_record,
            sort=sort,
        ).to_payload()
