from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP

from nlgovdata.core.schema import SourceResponse
from nlgovdata.mcp.tools_koop import register_koop_tools
from nlgovdata.mcp.tools_rijk import register_rijk_tools
from nlgovdata.mcp.tools_tk import register_tk_tools
from nlgovdata.mcp.tools_unified import register_unified_tools

from tests.conftest import load_json_fixture

pytestmark = pytest.mark.unit


def _build_services() -> SimpleNamespace:
    class _Tk:
        def search_documents(self, **kwargs) -> SourceResponse:
            del kwargs
            return SourceResponse("tk", 1, 1, None, load_json_fixture("tk/documents.json")["value"])

        def search_activities(self, **kwargs) -> SourceResponse:
            del kwargs
            return SourceResponse("tk", 1, 1, None, load_json_fixture("tk/activities.json")["value"])

        def search_votes(self, **kwargs) -> SourceResponse:
            del kwargs
            return SourceResponse("tk", 1, 1, None, load_json_fixture("tk/votes.json")["value"])

        def search_members(self, query: str) -> SourceResponse:
            del query
            return SourceResponse("tk", 2, 2, None, load_json_fixture("tk/people.json")["value"])

        def list_factions(self, *, limit: int = 100, offset: int = 0) -> SourceResponse:
            del limit, offset
            return SourceResponse("tk", 30, 1, None, load_json_fixture("tk/factions.json")["value"])

        def list_committees(self, *, limit: int = 100, offset: int = 0) -> SourceResponse:
            del limit, offset
            return SourceResponse("tk", 30, 1, None, load_json_fixture("tk/committees.json")["value"])

        def get_dossier(self, dossier_number: str):
            del dossier_number
            return load_json_fixture("tk/dossier.json")["value"][0]

        def search(self, *args, **kwargs) -> SourceResponse:
            del args, kwargs
            return SourceResponse("tk", 1, 1, None, load_json_fixture("tk/documents.json")["value"])

        def get(self, *args, **kwargs):
            del args, kwargs
            return load_json_fixture("tk/documents.json")["value"][0]

        def count(self, *args, **kwargs) -> int:
            del args, kwargs
            return 1

    class _Rijk:
        def search_documents(self, **kwargs) -> SourceResponse:
            del kwargs
            raise RuntimeError("upstream timeout")

        def list_ministries(self):
            return load_json_fixture("rijksoverheid/ministries.json")["results"]

        def list_subjects(self):
            return load_json_fixture("rijksoverheid/subjects.json")["results"]

        def search(self, *args, **kwargs) -> SourceResponse:
            del args, kwargs
            return SourceResponse(
                "rijksoverheid",
                5,
                1,
                None,
                load_json_fixture("rijksoverheid/documents.json")["results"],
            )

        def get(self, *args, **kwargs):
            del args, kwargs
            return load_json_fixture("rijksoverheid/documents.json")["results"][0]

    class _Koop:
        def search_documents(self, **kwargs) -> SourceResponse:
            del kwargs
            return SourceResponse(
                "koop",
                1,
                1,
                None,
                [
                    {
                        "identifier": "kst-36228-3",
                        "title": "Motie over woningbouw",
                        "type": "Kamerstuk",
                        "available": "2026-04-09",
                        "issued": "2026-04-08",
                        "modified": "2026-04-09T11:00:00Z",
                        "dossier_number": "36228",
                        "dossier_sub_number": "3",
                        "subrubriek": "Motie",
                        "product_area": "Wonen",
                        "creator": "Tweede Kamer",
                    }
                ],
            )

        def search(self, *args, **kwargs) -> SourceResponse:
            del args, kwargs
            return self.search_documents()

    return SimpleNamespace(
        config=SimpleNamespace(cache_ttl_seconds=3600),
        requester=object(),
        tk=_Tk(),
        rijk=_Rijk(),
        koop=_Koop(),
    )


def test_unified_search_documents_fails_open_when_one_source_errors() -> None:
    mcp = FastMCP("test")
    register_unified_tools(mcp, _build_services())

    payload = asyncio.run(mcp._tool_manager._tools["search_documents"].fn(keyword="woningbouw"))

    assert payload["returned_count"] == 2
    assert any("rijksoverheid failed" in warning for warning in payload["warnings"])


def test_get_member_returns_multiple_matches() -> None:
    mcp = FastMCP("test")
    register_unified_tools(mcp, _build_services())

    payload = mcp._tool_manager._tools["get_member"].fn(query="Jansen")

    assert payload["returned_count"] == 2
    assert {item["name"] for item in payload["results"]} == {"Jan Jansen", "Janneke Jansen"}


def test_list_tools_expose_next_offset_and_bounded_params() -> None:
    mcp = FastMCP("test")
    register_unified_tools(mcp, _build_services())

    factions = mcp._tool_manager._tools["list_factions"].fn(limit=10, offset=5)
    subjects = mcp._tool_manager._tools["list_subjects"].fn(limit=3, offset=2)

    assert factions["next_offset"] == 6
    assert factions["results"][0]["name"] == "Partij van de Arbeid"
    assert subjects["next_offset"] == 3
    assert len(subjects["results"]) == 1


def test_search_tools_pass_max_results_to_underlying_services() -> None:
    mcp = FastMCP("test")
    services = _build_services()
    register_unified_tools(mcp, services)

    activities = mcp._tool_manager._tools["search_activities"].fn(keyword="ai", max_results=7)
    votes = mcp._tool_manager._tools["search_votes"].fn(faction="PvdA", max_results=6)

    assert activities["returned_count"] == 1
    assert votes["returned_count"] == 1


def test_get_dossier_timeline_reports_total_count_and_truncation() -> None:
    mcp = FastMCP("test")
    register_unified_tools(mcp, _build_services())

    payload = asyncio.run(
        mcp._tool_manager._tools["get_dossier_timeline"].fn(
            dossier_number="36228",
            max_results_per_source=1,
            timeline_limit=2,
        )
    )

    assert payload["total_count"] == 4
    assert payload["returned_count"] == 2
    assert payload["truncated"] is True
    assert len(payload["timeline"]) == 2


def test_all_tool_groups_register_expected_names() -> None:
    mcp = FastMCP("test")
    services = _build_services()
    register_tk_tools(mcp, services)
    register_rijk_tools(mcp, services)
    register_koop_tools(mcp, services)
    register_unified_tools(mcp, services)

    tool_names = {tool.name for tool in mcp._tool_manager._tools.values()}
    assert tool_names == {
        "tk_search",
        "tk_get",
        "tk_count",
        "rijksoverheid_search",
        "rijksoverheid_get",
        "koop_search",
        "search_documents",
        "get_dossier_timeline",
        "search_activities",
        "search_votes",
        "get_member",
        "list_factions",
        "list_committees",
        "list_ministries",
        "list_subjects",
    }


@pytest.mark.asyncio
async def test_fastmcp_client_can_call_unified_tool() -> None:
    mcp = FastMCP("test")
    register_unified_tools(mcp, _build_services())

    async with Client(mcp) as client:
        payload = await client.call_tool("search_documents", {"keyword": "woningbouw"})

    assert payload.data["returned_count"] == 2
    assert any(result["source"] == "tk" for result in payload.data["results"])
