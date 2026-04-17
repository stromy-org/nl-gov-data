from __future__ import annotations

import os

import pytest

from nlgovdata.cli.health import run_connectivity_checks
from nlgovdata.mcp.dependencies import build_services

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
