"""Connectivity checks for CLI and live smoke tests."""

from __future__ import annotations

import time
from typing import Any

from nlgovdata.mcp.dependencies import ServiceContainer


def _run_single_check(source: str, fn: Any) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = fn()
        duration_ms = int((time.perf_counter() - started) * 1000)
        payload = dict(result)
        payload.update(
            {
                "source": source,
                "status": payload.get("status", "ok"),
                "reachable": True,
                "duration_ms": duration_ms,
            }
        )
        return payload
    except Exception as exc:  # noqa: BLE001
        duration_ms = int((time.perf_counter() - started) * 1000)
        return {
            "source": source,
            "status": "error",
            "reachable": False,
            "duration_ms": duration_ms,
            "error": str(exc),
        }


def run_connectivity_checks(services: ServiceContainer, *, sources: list[str] | None = None) -> list[dict[str, Any]]:
    selected = sources or ["tk", "rijksoverheid", "koop"]
    checks = {
        "tk": lambda: services.tk.healthcheck(),
        "rijksoverheid": lambda: services.rijk.healthcheck(),
        "koop": lambda: services.koop.healthcheck(),
    }
    return [_run_single_check(source, checks[source]) for source in selected]
