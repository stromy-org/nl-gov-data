"""Rijksoverheid open data REST adapter."""

from __future__ import annotations

from typing import Any

from nlgovdata.core.config import AppConfig
from nlgovdata.core.schema import SourceResponse
from nlgovdata.core.types import (
    RIJK_DOC_TYPE_FILTERS,
    RIJKSOVERHEID_ENDPOINT_ALIASES,
    RIJKSOVERHEID_ENDPOINTS,
    slugify,
)
from nlgovdata.utils.http import HttpRequester


class RijksoverheidAdapter:
    source_name = "rijksoverheid"

    def __init__(self, config: AppConfig, requester: HttpRequester) -> None:
        self.config = config
        self.requester = requester

    def _resolve_endpoint(self, endpoint: str) -> str:
        normalized = slugify(endpoint)
        canonical = RIJKSOVERHEID_ENDPOINT_ALIASES.get(normalized, normalized)
        if canonical not in RIJKSOVERHEID_ENDPOINTS:
            valid = ", ".join(RIJKSOVERHEID_ENDPOINTS)
            raise ValueError(f"Unsupported Rijksoverheid endpoint: {endpoint}. Use one of: {valid}")
        return canonical

    def _extract_results(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("results", "result", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
        return []

    def _extract_total(self, payload: Any, results: list[dict[str, Any]]) -> int | None:
        if isinstance(payload, dict):
            for key in ("total", "totalCount", "count"):
                value = payload.get(key)
                if isinstance(value, int):
                    return value
            meta = payload.get("meta")
            if isinstance(meta, dict):
                for key in ("total", "totalCount", "count"):
                    value = meta.get(key)
                    if isinstance(value, int):
                        return value
        return len(results)

    def search(
        self,
        endpoint: str,
        *,
        doc_type: str | None = None,
        subject: str | None = None,
        ministry: str | None = None,
        since_date: str | None = None,
        rows: int = 25,
        offset: int = 0,
    ) -> SourceResponse:
        endpoint = self._resolve_endpoint(endpoint)
        path = RIJKSOVERHEID_ENDPOINTS[endpoint]
        params: dict[str, Any] = {"output": "json", "rows": min(rows, 200), "offset": offset}

        if endpoint == "documents":
            if doc_type:
                params["type"] = doc_type
            if subject:
                params["subject"] = subject
            if ministry:
                params["organisationalunit"] = ministry
            if since_date:
                params["lastmodifiedsince"] = since_date.replace("-", "")
        elif endpoint == "news":
            if subject:
                path += f"/subjects/{subject}"
            if ministry:
                path += f"/ministries/{ministry}"
            if since_date:
                path += f"/lastmodifiedsince/{since_date.replace('-', '')}"

        payload = self.requester.get_json(
            self.source_name,
            f"{self.config.rijk_base_url.rstrip('/')}/{path}",
            params=params,
        )
        results = self._extract_results(payload)
        return SourceResponse(
            source=self.source_name,
            total_count=self._extract_total(payload, results),
            returned_count=len(results),
            next_cursor=str(offset + len(results)) if len(results) == params["rows"] else None,
            results=results,
            warnings=[],
        )

    def get(self, endpoint: str, item_id: str) -> dict[str, Any]:
        endpoint = self._resolve_endpoint(endpoint)
        path = RIJKSOVERHEID_ENDPOINTS[endpoint]
        return self.requester.get_json(
            self.source_name,
            f"{self.config.rijk_base_url.rstrip('/')}/{path}/{item_id}",
            params={"output": "json"},
        )

    def _keyword_filter(self, rows: list[dict[str, Any]], keyword: str | None) -> list[dict[str, Any]]:
        if not keyword:
            return rows
        needle = keyword.lower()
        filtered: list[dict[str, Any]] = []
        for row in rows:
            haystack = " ".join(
                str(value)
                for value in (
                    row.get("title"),
                    row.get("introduction"),
                    row.get("summary"),
                )
                if value
            ).lower()
            if needle in haystack:
                filtered.append(row)
        return filtered

    def search_documents(
        self,
        *,
        keyword: str | None = None,
        doc_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        dossier_number: str | None = None,
        max_results: int = 50,
    ) -> SourceResponse:
        del date_to, dossier_number
        endpoints = ["documents", "news", "faq"]
        all_results: list[dict[str, Any]] = []
        total_count = 0

        for endpoint in endpoints:
            source_doc_type = RIJK_DOC_TYPE_FILTERS.get(doc_type or "")
            response = self.search(
                endpoint,
                doc_type=source_doc_type if endpoint == "documents" else None,
                since_date=date_from,
                rows=max_results,
                offset=0,
            )
            total_count += response.total_count or 0
            tagged = [{**row, "_endpoint": endpoint} for row in self._keyword_filter(response.results, keyword)]
            all_results.extend(tagged)

        return SourceResponse(
            source=self.source_name,
            total_count=total_count,
            returned_count=min(len(all_results), max_results),
            next_cursor=None,
            results=all_results[:max_results],
            warnings=[],
        )

    def list_subjects(self) -> list[dict[str, Any]]:
        return self.search("subject", rows=200).results

    def list_ministries(self) -> list[dict[str, Any]]:
        return self.search("ministry", rows=200).results

    def healthcheck(self) -> dict[str, str]:
        response = self.search("documents", rows=1)
        return {"source": self.source_name, "status": "ok", "returned_count": str(response.returned_count)}
