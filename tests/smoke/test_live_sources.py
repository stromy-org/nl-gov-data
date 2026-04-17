from __future__ import annotations

import os

import pytest
from fastmcp import FastMCP

from nlgovdata.cli.health import run_connectivity_checks
from nlgovdata.mcp.dependencies import build_services
from nlgovdata.mcp.tools_unified import register_unified_tools

pytestmark = pytest.mark.smoke


def _require_live_smoke() -> None:
    if os.environ.get("NLGOVDATA_RUN_SMOKE") != "1":
        pytest.skip("Set NLGOVDATA_RUN_SMOKE=1 to execute live upstream smoke tests")


def test_live_connectivity_checks_all_sources() -> None:
    _require_live_smoke()

    results = run_connectivity_checks(build_services())

    assert {item["source"] for item in results} == {"tk", "rijksoverheid", "koop"}
    assert all(item["reachable"] for item in results)


def test_live_cli_contract_has_positive_duration() -> None:
    _require_live_smoke()

    results = run_connectivity_checks(build_services(), sources=["tk"])

    assert results[0]["source"] == "tk"
    assert results[0]["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_live_bounded_unified_tools() -> None:
    _require_live_smoke()

    mcp = FastMCP("live")
    register_unified_tools(mcp, build_services())

    factions = mcp._tool_manager._tools["list_factions"].fn(limit=5)
    committees = mcp._tool_manager._tools["list_committees"].fn(limit=5)
    activities = mcp._tool_manager._tools["search_activities"].fn(date_from="2026-04-01", max_results=5)
    votes = mcp._tool_manager._tools["search_votes"].fn(date_from="2026-04-01", max_results=5)
    timeline = await mcp._tool_manager._tools["get_dossier_timeline"].fn(
        dossier_number="26643",
        max_results_per_source=5,
        timeline_limit=20,
    )

    assert factions["returned_count"] <= 5
    assert committees["returned_count"] <= 5
    assert activities["returned_count"] <= 5
    assert votes["returned_count"] <= 5
    assert timeline["returned_count"] <= 20
    assert "total_count" in timeline
    assert "truncated" in timeline
