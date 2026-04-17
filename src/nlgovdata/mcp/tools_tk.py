"""Source-specific Tweede Kamer tools."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from nlgovdata.mcp.dependencies import ServiceContainer


def register_tk_tools(mcp: FastMCP, services: ServiceContainer) -> None:
    @mcp.tool
    def tk_search(
        entity: str,
        filter: str | None = None,
        select: list[str] | None = None,
        expand: list[str] | None = None,
        orderby: str | None = None,
        top: int = 50,
    ) -> dict[str, Any]:
        """Search a Tweede Kamer entity set with native OData semantics."""
        return services.tk.search(
            entity,
            filter_value=filter,
            select=select,
            expand=expand,
            orderby=orderby,
            top=top,
        ).to_payload()

    @mcp.tool
    def tk_get(entity: str, id: str, expand: list[str] | None = None) -> dict[str, Any]:
        """Fetch a single Tweede Kamer entity by GUID."""
        return services.tk.get(entity, id, expand=expand)

    @mcp.tool
    def tk_count(entity: str, filter: str | None = None) -> int:
        """Count matching Tweede Kamer rows for an entity set."""
        return services.tk.count(entity, filter_value=filter)
