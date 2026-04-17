"""Unified cross-source MCP tools."""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from fastmcp import FastMCP

from nlgovdata.adapters.tk import validate_sources
from nlgovdata.core.normalize import (
    build_dossier_timeline,
    normalize_activity,
    normalize_committee,
    normalize_dossier,
    normalize_faction,
    normalize_koop_document,
    normalize_member,
    normalize_rijk_document,
    normalize_tk_document,
    normalize_vote,
    sort_documents_desc,
)
from nlgovdata.core.schema import SourceResponse, UnifiedResponse
from nlgovdata.mcp.dependencies import ServiceContainer


def _source_warning(source: str, exc: Exception) -> str:
    return f"{source} failed: {exc}"


def _next_offset(total_count: int | None, offset: int, returned_count: int) -> int | None:
    if total_count is None:
        return None
    next_value = offset + returned_count
    return next_value if next_value < total_count else None


async def _run_source_call(
    source: str,
    func: Callable[[], SourceResponse],
) -> tuple[str, SourceResponse | None, str | None]:
    try:
        response = await asyncio.to_thread(func)
        return source, response, None
    except Exception as exc:  # noqa: BLE001
        return source, None, _source_warning(source, exc)


def _filter_documents(
    documents: list[dict[str, Any]],
    *,
    subject: str | None = None,
    organization: str | None = None,
) -> list[dict[str, Any]]:
    subject_lower = subject.lower() if subject else None
    organization_lower = organization.lower() if organization else None
    filtered: list[dict[str, Any]] = []

    for document in documents:
        if subject_lower:
            subjects = [item.lower() for item in document.get("subjects", [])]
            if not any(subject_lower in item for item in subjects):
                continue
        if organization_lower:
            orgs = [item.lower() for item in document.get("organizations", [])]
            if not any(organization_lower in item for item in orgs):
                continue
        filtered.append(document)

    return filtered


def register_unified_tools(mcp: FastMCP, services: ServiceContainer) -> None:
    @mcp.tool
    async def search_documents(
        keyword: str | None = None,
        doc_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        dossier_number: str | None = None,
        subject: str | None = None,
        organization: str | None = None,
        sources: list[str] | None = None,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """Search documents across TK, Rijksoverheid, and KOOP with normalized output."""
        chosen_sources = sources or ["tk", "rijksoverheid", "koop"]
        validate_sources(chosen_sources)

        async def _run() -> UnifiedResponse:
            tasks = []
            if "tk" in chosen_sources:
                tasks.append(
                    _run_source_call(
                        "tk",
                        lambda: services.tk.search_documents(
                            keyword=keyword,
                            doc_type=doc_type,
                            date_from=date_from,
                            date_to=date_to,
                            dossier_number=dossier_number,
                            max_results=max_results,
                        ),
                    )
                )
            if "rijksoverheid" in chosen_sources:
                tasks.append(
                    _run_source_call(
                        "rijksoverheid",
                        lambda: services.rijk.search_documents(
                            keyword=keyword,
                            doc_type=doc_type,
                            date_from=date_from,
                            date_to=date_to,
                            dossier_number=dossier_number,
                            max_results=max_results,
                        ),
                    )
                )
            if "koop" in chosen_sources:
                tasks.append(
                    _run_source_call(
                        "koop",
                        lambda: services.koop.search_documents(
                            keyword=keyword,
                            doc_type=doc_type,
                            date_from=date_from,
                            date_to=date_to,
                            dossier_number=dossier_number,
                            max_results=max_results,
                        ),
                    )
                )

            warnings: list[str] = []
            total_count = 0
            documents = []

            for source, response, warning in await asyncio.gather(*tasks):
                if warning:
                    warnings.append(warning)
                    continue
                if response is None:
                    warnings.append(f"{source} failed without a response")
                    continue
                total_count += response.total_count or 0
                if source == "tk":
                    documents.extend(
                        [
                            doc.to_payload()
                            for doc in sort_documents_desc(normalize_tk_document(row) for row in response.results)
                        ]
                    )
                elif source == "rijksoverheid":
                    documents.extend(
                        [
                            doc.to_payload()
                            for doc in sort_documents_desc(normalize_rijk_document(row) for row in response.results)
                        ]
                    )
                else:
                    documents.extend(
                        [
                            doc.to_payload()
                            for doc in sort_documents_desc(normalize_koop_document(row) for row in response.results)
                        ]
                    )

            filtered_documents = _filter_documents(documents, subject=subject, organization=organization)
            ordered = sorted(
                filtered_documents,
                key=lambda row: row.get("published_at") or row.get("issued_at") or row.get("modified_at") or "",
                reverse=True,
            )[:max_results]
            return UnifiedResponse(
                total_count=total_count or None,
                returned_count=len(ordered),
                results=ordered,
                warnings=warnings,
            )

        return (await _run()).to_payload()

    @mcp.tool
    async def get_dossier_timeline(
        dossier_number: str,
        max_results_per_source: int = 10,
        timeline_limit: int = 40,
    ) -> dict[str, Any]:
        """Return a bounded deterministic dossier timeline using TK and KOOP."""
        source_limit = max(1, min(max_results_per_source, 100))
        capped_timeline_limit = max(1, timeline_limit)

        async def _run() -> dict[str, Any]:
            tasks = await asyncio.gather(
                _run_source_call(
                    "tk_documents",
                    lambda: services.tk.search_documents(dossier_number=dossier_number, max_results=source_limit),
                ),
                _run_source_call(
                    "koop_documents",
                    lambda: services.koop.search_documents(dossier_number=dossier_number, max_results=source_limit),
                ),
                _run_source_call(
                    "activities",
                    lambda: services.tk.search_activities(dossier_number=dossier_number, top=source_limit),
                ),
                _run_source_call(
                    "votes",
                    lambda: services.tk.search_votes(dossier_number=dossier_number, top=source_limit),
                ),
            )

            warnings = [warning for _, _, warning in tasks if warning]
            tk_documents = next((response for source, response, _ in tasks if source == "tk_documents"), None)
            koop_documents = next((response for source, response, _ in tasks if source == "koop_documents"), None)
            activity_response = next((response for source, response, _ in tasks if source == "activities"), None)
            vote_response = next((response for source, response, _ in tasks if source == "votes"), None)

            dossier_row = services.tk.get_dossier(dossier_number)
            dossier = normalize_dossier(dossier_row) if dossier_row else None
            timeline = build_dossier_timeline(
                dossier_number,
                dossier,
                [normalize_tk_document(row) for row in tk_documents.results] if tk_documents else [],
                [normalize_koop_document(row) for row in koop_documents.results] if koop_documents else [],
                [normalize_activity(row) for row in activity_response.results] if activity_response else [],
                [normalize_vote(row) for row in vote_response.results] if vote_response else [],
                warnings=warnings,
            )
            payload = timeline.to_payload()
            payload["timeline"] = payload["timeline"][:capped_timeline_limit]
            payload["truncated"] = payload["total_count"] is not None and payload["total_count"] > capped_timeline_limit
            payload["returned_count"] = len(payload["timeline"])
            return payload

        return await _run()

    @mcp.tool
    def search_activities(
        date_from: str | None = None,
        date_to: str | None = None,
        type: str | None = None,
        committee: str | None = None,
        keyword: str | None = None,
        dossier_number: str | None = None,
        actor: str | None = None,
        max_results: int = 20,
    ) -> dict[str, Any]:
        """Return normalized parliamentary activities from TK with bounded results."""
        response = services.tk.search_activities(
            date_from=date_from,
            date_to=date_to,
            activity_type=type,
            committee=committee,
            keyword=keyword,
            dossier_number=dossier_number,
            actor=actor,
            top=max_results,
        )
        results = [normalize_activity(row).to_payload() for row in response.results]
        return UnifiedResponse(
            total_count=response.total_count,
            returned_count=len(results),
            results=results,
            warnings=response.warnings,
        ).to_payload()

    @mcp.tool
    def search_votes(
        date_from: str | None = None,
        date_to: str | None = None,
        dossier_number: str | None = None,
        outcome: str | None = None,
        faction: str | None = None,
        max_results: int = 20,
    ) -> dict[str, Any]:
        """Return normalized vote results from TK with bounded results."""
        response = services.tk.search_votes(
            date_from=date_from,
            date_to=date_to,
            dossier_number=dossier_number,
            outcome=outcome,
            faction=faction,
            top=max_results,
        )
        results = [normalize_vote(row).to_payload() for row in response.results]
        return UnifiedResponse(
            total_count=response.total_count,
            returned_count=len(results),
            results=results,
            warnings=response.warnings,
        ).to_payload()

    @mcp.tool
    def get_member(query: str) -> dict[str, Any]:
        """Resolve one or more Tweede Kamer members by name query."""
        response = services.tk.search_members(query)
        results = [normalize_member(row).to_payload() for row in response.results]
        return {
            "returned_count": len(results),
            "results": results,
            "warnings": response.warnings,
        }

    @mcp.tool
    def list_factions(limit: int = 25, offset: int = 0) -> dict[str, Any]:
        """List active TK factions with seat counts using bounded pagination."""
        response = services.tk.list_factions(limit=limit, offset=offset)
        results = [normalize_faction(row).to_payload() for row in response.results]
        return UnifiedResponse(
            total_count=response.total_count,
            returned_count=len(results),
            results=results,
            next_offset=_next_offset(response.total_count, offset, len(results)),
            warnings=response.warnings,
        ).to_payload()

    @mcp.tool
    def list_committees(limit: int = 25, offset: int = 0) -> dict[str, Any]:
        """List active TK committees using bounded pagination."""
        response = services.tk.list_committees(limit=limit, offset=offset)
        results = [normalize_committee(row).to_payload() for row in response.results]
        return UnifiedResponse(
            total_count=response.total_count,
            returned_count=len(results),
            results=results,
            next_offset=_next_offset(response.total_count, offset, len(results)),
            warnings=response.warnings,
        ).to_payload()

    @mcp.tool
    def list_ministries(limit: int = 25, offset: int = 0) -> dict[str, Any]:
        """List Rijksoverheid ministries using bounded pagination."""
        response = services.rijk.search("ministry", rows=limit, offset=offset)
        return UnifiedResponse(
            total_count=response.total_count,
            returned_count=response.returned_count,
            results=response.results,
            next_offset=_next_offset(response.total_count, offset, response.returned_count),
            warnings=response.warnings,
        ).to_payload()

    @mcp.tool
    def list_subjects(limit: int = 25, offset: int = 0) -> dict[str, Any]:
        """List Rijksoverheid subjects using bounded pagination."""
        response = services.rijk.search("subject", rows=limit, offset=offset)
        return UnifiedResponse(
            total_count=response.total_count,
            returned_count=response.returned_count,
            results=response.results,
            next_offset=_next_offset(response.total_count, offset, response.returned_count),
            warnings=response.warnings,
        ).to_payload()
