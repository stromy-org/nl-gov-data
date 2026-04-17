from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from nlgovdata.cli.main import cli

pytestmark = pytest.mark.unit


def test_list_sources_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    services = SimpleNamespace(
        config=SimpleNamespace(
            tk_base_url="https://tk.test",
            rijk_base_url="https://rijk.test",
            koop_base_url="https://koop.test",
        )
    )
    monkeypatch.setattr("nlgovdata.cli.main.build_services", lambda: services)

    result = CliRunner().invoke(cli, ["list-sources"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert [item["source"] for item in payload] == ["tk", "rijksoverheid", "koop"]
    assert payload[0]["capabilities"]["default_page_size"] == 250


def test_list_sources_text_output(monkeypatch: pytest.MonkeyPatch) -> None:
    services = SimpleNamespace(
        config=SimpleNamespace(
            tk_base_url="https://tk.test",
            rijk_base_url="https://rijk.test",
            koop_base_url="https://koop.test",
        )
    )
    monkeypatch.setattr("nlgovdata.cli.main.build_services", lambda: services)

    result = CliRunner().invoke(cli, ["list-sources", "--format", "text"])

    assert result.exit_code == 0
    assert "tk: Tweede Kamer OData v4" in result.output
    assert "native_tools: tk_search, tk_get, tk_count" in result.output


def test_test_connection_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    services = object()
    monkeypatch.setattr("nlgovdata.cli.main.build_services", lambda: services)
    monkeypatch.setattr(
        "nlgovdata.cli.main.run_connectivity_checks",
        lambda _services, sources=None: [
            {
                "source": "tk",
                "status": "ok",
                "reachable": True,
                "duration_ms": 12,
                "returned_count": "1",
            }
        ],
    )

    result = CliRunner().invoke(cli, ["test-connection"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload[0]["source"] == "tk"
    assert payload[0]["reachable"] is True


def test_test_connection_fails_on_unreachable_source(monkeypatch: pytest.MonkeyPatch) -> None:
    services = object()
    monkeypatch.setattr("nlgovdata.cli.main.build_services", lambda: services)
    monkeypatch.setattr(
        "nlgovdata.cli.main.run_connectivity_checks",
        lambda _services, sources=None: [
            {
                "source": "koop",
                "status": "error",
                "reachable": False,
                "duration_ms": 99,
                "error": "network down",
            }
        ],
    )

    result = CliRunner().invoke(cli, ["test-connection", "--format", "text"])

    assert result.exit_code != 0
    assert "network down" in result.output
