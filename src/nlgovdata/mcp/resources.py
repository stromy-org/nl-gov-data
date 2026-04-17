"""Schema and reference resources for nl-gov-data."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable

from fastmcp import FastMCP

from nlgovdata.core.types import DOCUMENT_TYPE_MAP
from nlgovdata.mcp.dependencies import ServiceContainer

TK_SCHEMA = {
    "source": "tk",
    "description": "Tweede Kamer OData entity catalog",
    "entities": [
        {"name": "Document", "notes": "documents, dossier relations, submitters, dates"},
        {"name": "Kamerstukdossier", "notes": "deterministic dossier key"},
        {"name": "Persoon", "notes": "members and related faction links"},
        {"name": "Activiteit", "notes": "agenda and activity data"},
        {"name": "Stemming", "notes": "votes and outcomes"},
        {"name": "Commissie", "notes": "committee catalog"},
        {"name": "Fractie", "notes": "faction/party catalog"},
    ],
}

RIJK_SCHEMA = {
    "source": "rijksoverheid",
    "description": "Rijksoverheid endpoint catalog",
    "endpoints": [
        {"name": "documents", "filters": ["type", "subject", "organisationalunit", "lastmodifiedsince"]},
        {"name": "news", "filters": ["subject", "ministry", "lastmodifiedsince"]},
        {"name": "faq", "filters": []},
        {"name": "subject", "filters": []},
        {"name": "ministry", "filters": []},
    ],
}

KOOP_SCHEMA = {
    "source": "koop",
    "description": "KOOP SRU collections and common indexes",
    "collections": ["officielepublicaties", "sgd", "bwb", "wetgevingskalender"],
    "indexes": [
        "dt.identifier",
        "dt.title",
        "dt.type",
        "dt.modified",
        "w.dossiernummer",
        "w.vergaderjaar",
        "w.subrubriek",
        "w.documenttitel",
        "c.product-area",
    ],
}


@dataclass
class _CacheEntry:
    payload: dict[str, Any]
    expires_at: float


class ResourceCatalog:
    def __init__(self, services: ServiceContainer) -> None:
        self.services = services
        self._cache: dict[str, _CacheEntry] = {}

    def _load_cached(self, key: str, loader: Callable[[], list[dict[str, Any]]]) -> str:
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached and cached.expires_at > now:
            return json.dumps(cached.payload)

        try:
            results = loader()
            payload = {"results": results, "stale": False, "warnings": []}
            self._cache[key] = _CacheEntry(payload=payload, expires_at=now + self.services.config.cache_ttl_seconds)
            return json.dumps(payload)
        except Exception as exc:  # noqa: BLE001
            if cached:
                stale_payload = dict(cached.payload)
                stale_payload["stale"] = True
                stale_payload["warnings"] = [f"serving stale cache: {exc}"]
                return json.dumps(stale_payload)
            return json.dumps({"results": [], "stale": False, "warnings": [str(exc)]})


def register_resources(mcp: FastMCP, services: ServiceContainer) -> None:
    catalog = ResourceCatalog(services)

    @mcp.resource("data://nlgov/schema/tk")
    def get_tk_schema() -> str:
        """Return static TK entity discovery data."""
        return json.dumps(TK_SCHEMA)

    @mcp.resource("data://nlgov/schema/rijksoverheid")
    def get_rijk_schema() -> str:
        """Return static Rijksoverheid endpoint discovery data."""
        return json.dumps(RIJK_SCHEMA)

    @mcp.resource("data://nlgov/schema/koop")
    def get_koop_schema() -> str:
        """Return static KOOP index discovery data."""
        return json.dumps(KOOP_SCHEMA)

    @mcp.resource("data://nlgov/doc-types")
    def get_doc_types() -> str:
        """Return document type normalization mappings."""
        return json.dumps(DOCUMENT_TYPE_MAP)

    @mcp.resource("data://nlgov/subjects")
    def get_subjects() -> str:
        """Return cached Rijksoverheid subject taxonomy."""
        return catalog._load_cached("subjects", services.rijk.list_subjects)

    @mcp.resource("data://nlgov/ministries")
    def get_ministries() -> str:
        """Return cached Rijksoverheid ministry list."""
        return catalog._load_cached("ministries", services.rijk.list_ministries)

    @mcp.resource("data://nlgov/factions")
    def get_factions() -> str:
        """Return cached TK faction list."""
        return catalog._load_cached("factions", lambda: services.tk.list_factions().results)
