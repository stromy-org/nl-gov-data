"""Source-specific Rijksoverheid tools."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from nlgovdata.mcp.dependencies import ServiceContainer


def register_rijk_tools(mcp: FastMCP, services: ServiceContainer) -> None:
    @mcp.tool
    def rijksoverheid_search(
        endpoint: str,
        type: str | None = None,
        subject: str | None = None,
        ministry: str | None = None,
        since_date: str | None = None,
        rows: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search a Rijksoverheid endpoint with native filtering and pagination.

        Canonical endpoints are: documents, news, faq, subject, ministry.
        """
        return services.rijk.search(
            endpoint,
            doc_type=type,
            subject=subject,
            ministry=ministry,
            since_date=since_date,
            rows=rows,
            offset=offset,
        ).to_payload()

    @mcp.tool
    def rijksoverheid_get(endpoint: str, id: str) -> dict[str, Any]:
        """Fetch a single Rijksoverheid record by UUID or source id."""
        return services.rijk.get(endpoint, id)
