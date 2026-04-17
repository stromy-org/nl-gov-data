from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from nlgovdata.core.config import AppConfig


FIXTURES_ROOT = Path(__file__).parent / "fixtures"


def load_json_fixture(relative_path: str) -> Any:
    return json.loads((FIXTURES_ROOT / relative_path).read_text(encoding="utf-8"))


def load_text_fixture(relative_path: str) -> str:
    return (FIXTURES_ROOT / relative_path).read_text(encoding="utf-8")


class FakeRequester:
    def __init__(
        self,
        *,
        json_responses: dict[str, Any] | None = None,
        text_responses: dict[str, str] | None = None,
    ) -> None:
        self.json_responses = json_responses or {}
        self.text_responses = text_responses or {}
        self.calls: list[dict[str, Any]] = []

    def _lookup(self, store: dict[str, Any], url: str) -> Any:
        for key, value in store.items():
            if key in url:
                return deepcopy(value)
        raise AssertionError(f"Unexpected URL: {url}")

    def get_json(
        self,
        source: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        self.calls.append({"source": source, "url": url, "params": params or {}, "headers": headers or {}})
        return self._lookup(self.json_responses, url)

    def get_text(
        self,
        source: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        self.calls.append({"source": source, "url": url, "params": params or {}, "headers": headers or {}})
        return self._lookup(self.text_responses, url)


@pytest.fixture
def app_config() -> AppConfig:
    return AppConfig(
        tk_base_url="https://tk.test/OData/v4/2.0",
        rijk_base_url="https://rijk.test/v1",
        koop_base_url="https://koop.test/sru",
        timeout_seconds=1.0,
        max_retries=1,
        request_interval_seconds=0.0,
        cache_ttl_seconds=3600,
    )
