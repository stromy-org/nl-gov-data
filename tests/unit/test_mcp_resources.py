from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from fastmcp import FastMCP

from nlgovdata.mcp.resources import ResourceCatalog, register_resources

from tests.conftest import load_json_fixture

pytestmark = pytest.mark.unit


def _services() -> SimpleNamespace:
    class _Rijk:
        def __init__(self) -> None:
            self.subject_calls = 0

        def list_subjects(self):
            self.subject_calls += 1
            return load_json_fixture("rijksoverheid/subjects.json")["results"]

        def list_ministries(self):
            return load_json_fixture("rijksoverheid/ministries.json")["results"]

    class _Tk:
        def list_factions(self):
            return SimpleNamespace(results=load_json_fixture("tk/factions.json")["value"])

    return SimpleNamespace(
        config=SimpleNamespace(cache_ttl_seconds=3600),
        rijk=_Rijk(),
        tk=_Tk(),
    )


def test_resource_catalog_caches_successful_loads() -> None:
    services = _services()
    catalog = ResourceCatalog(services)

    first = json.loads(catalog._load_cached("subjects", services.rijk.list_subjects))
    second = json.loads(catalog._load_cached("subjects", services.rijk.list_subjects))

    assert first["results"] == second["results"]
    assert services.rijk.subject_calls == 1


def test_resource_catalog_serves_stale_cache_on_failure() -> None:
    services = _services()
    catalog = ResourceCatalog(services)
    catalog._load_cached("subjects", services.rijk.list_subjects)
    catalog._cache["subjects"].expires_at = -1

    def _broken_loader():
        raise RuntimeError("boom")

    payload = json.loads(catalog._load_cached("subjects", _broken_loader))
    assert payload["stale"] is True
    assert "serving stale cache" in payload["warnings"][0]


def test_resource_registration_exposes_expected_uris() -> None:
    mcp = FastMCP("test")
    register_resources(mcp, _services())

    uris = {str(uri) for uri in mcp._resource_manager._resources}
    assert "data://nlgov/schema/tk" in uris
    assert "data://nlgov/schema/rijksoverheid" in uris
    assert "data://nlgov/schema/koop" in uris
    assert "data://nlgov/doc-types" in uris
