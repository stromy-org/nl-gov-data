"""Static source metadata used by CLI and docs."""

from __future__ import annotations

from typing import Any

from nlgovdata.core.types import KOOP_COLLECTIONS, RIJKSOVERHEID_ENDPOINTS, TK_ENTITY_ALLOWLIST


def build_source_catalog(*, tk_base_url: str, rijk_base_url: str, koop_base_url: str) -> list[dict[str, Any]]:
    return [
        {
            "source": "tk",
            "name": "Tweede Kamer OData v4",
            "protocol": "OData v4 JSON",
            "base_url": tk_base_url,
            "auth": "none",
            "native_tools": ["tk_search", "tk_get", "tk_count"],
            "unified_contributions": [
                "search_documents",
                "get_dossier_timeline",
                "search_activities",
                "search_votes",
                "get_member",
                "list_factions",
                "list_committees",
            ],
            "capabilities": {
                "pagination": "server-driven @odata.nextLink with opaque skiptoken",
                "default_page_size": 250,
                "max_page_size": 250,
                "entities": sorted(TK_ENTITY_ALLOWLIST),
            },
        },
        {
            "source": "rijksoverheid",
            "name": "Rijksoverheid Open Data REST",
            "protocol": "REST JSON",
            "base_url": rijk_base_url,
            "auth": "none",
            "native_tools": ["rijksoverheid_search", "rijksoverheid_get"],
            "unified_contributions": [
                "search_documents",
                "list_ministries",
                "list_subjects",
            ],
            "capabilities": {
                "pagination": "offset + rows",
                "max_page_size": 200,
                "endpoints": sorted(RIJKSOVERHEID_ENDPOINTS),
            },
        },
        {
            "source": "koop",
            "name": "KOOP SRU",
            "protocol": "SRU 2.0 XML",
            "base_url": koop_base_url,
            "auth": "none",
            "native_tools": ["koop_search"],
            "unified_contributions": [
                "search_documents",
                "get_dossier_timeline",
            ],
            "capabilities": {
                "pagination": "startRecord + maximumRecords",
                "max_page_size": 1000,
                "collections": sorted(KOOP_COLLECTIONS),
            },
        },
    ]
