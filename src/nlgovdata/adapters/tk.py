"""Tweede Kamer OData v4 adapter."""

from __future__ import annotations

from typing import Any, Sequence

from nlgovdata.core.config import AppConfig
from nlgovdata.core.schema import SourceResponse
from nlgovdata.core.types import SOURCE_NAMES, TK_DOC_TYPE_FILTERS, TK_ENTITY_ALLOWLIST
from nlgovdata.utils.http import HttpRequester
from nlgovdata.utils.odata import build_entity_url, build_query_params


def _escape_odata_string(value: str) -> str:
    return value.replace("'", "''")


def _is_numeric_keyword(value: str) -> bool:
    return value.isdigit()


def _collection_any(path: str, alias: str, predicate: str) -> str:
    return f"{path}/any({alias}:{predicate})"


def _dossier_filter_for_collection(path: str, dossier_number: int, *, alias: str = "d") -> str:
    return _collection_any(path, alias, f"{alias}/Nummer eq {dossier_number}")


def _dossier_filter_for_zaak_collection(path: str, dossier_number: int) -> str:
    return _collection_any(
        path,
        "z",
        _dossier_filter_for_collection("z/Kamerstukdossier", dossier_number, alias="d"),
    )


class TweedeKamerAdapter:
    source_name = "tk"

    def __init__(self, config: AppConfig, requester: HttpRequester) -> None:
        self.config = config
        self.requester = requester

    def _validate_entity(self, entity: str) -> None:
        if entity not in TK_ENTITY_ALLOWLIST:
            raise ValueError(f"Unsupported TK entity: {entity}")

    def search(
        self,
        entity: str,
        *,
        filter_value: str | None = None,
        select: str | Sequence[str] | None = None,
        expand: str | Sequence[str] | None = None,
        orderby: str | None = None,
        top: int = 50,
        skip: int | None = None,
    ) -> SourceResponse:
        self._validate_entity(entity)
        params = build_query_params(
            filter_value=filter_value,
            select=select,
            expand=expand,
            orderby=orderby,
            top=min(top, 250),
            skip=skip,
            include_count=True,
        )
        payload = self.requester.get_json(
            self.source_name,
            build_entity_url(self.config.tk_base_url, entity),
            params=params,
        )
        rows = payload.get("value", [])
        return SourceResponse(
            source=self.source_name,
            total_count=payload.get("@odata.count"),
            returned_count=len(rows),
            next_cursor=payload.get("@odata.nextLink"),
            results=rows,
            warnings=[],
        )

    def get(self, entity: str, entity_id: str, *, expand: str | Sequence[str] | None = None) -> dict[str, Any]:
        self._validate_entity(entity)
        params = build_query_params(expand=expand, include_count=False)
        return self.requester.get_json(
            self.source_name,
            build_entity_url(self.config.tk_base_url, entity, entity_id),
            params=params,
        )

    def count(self, entity: str, *, filter_value: str | None = None) -> int:
        response = self.search(entity, filter_value=filter_value, top=0)
        return response.total_count or 0

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
        filters = ["Verwijderd eq false"]
        if keyword:
            escaped = _escape_odata_string(keyword)
            filters.append(f"(contains(Titel,'{escaped}') or contains(Onderwerp,'{escaped}'))")
        if dossier_number:
            filters.append(_dossier_filter_for_collection("Kamerstukdossier", int(dossier_number)))
        if doc_type and doc_type in TK_DOC_TYPE_FILTERS:
            filters.append(f"Soort eq '{_escape_odata_string(TK_DOC_TYPE_FILTERS[doc_type])}'")
        if date_from:
            filters.append(f"Datum ge {date_from}")
        if date_to:
            filters.append(f"Datum le {date_to}")
        return self.search(
            "Document",
            filter_value=" and ".join(filters),
            expand=["Kamerstukdossier", "Zaak($expand=Kamerstukdossier)", "DocumentActor($expand=Persoon)"],
            orderby="Datum desc",
            top=max_results,
        )

    def search_activities(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        activity_type: str | None = None,
        committee: str | None = None,
        keyword: str | None = None,
        dossier_number: str | None = None,
        actor: str | None = None,
        top: int = 50,
    ) -> SourceResponse:
        filters = ["Verwijderd eq false"]
        if date_from:
            filters.append(f"Datum ge {date_from}")
        if date_to:
            filters.append(f"Datum le {date_to}")
        if activity_type:
            filters.append(f"contains(Soort,'{_escape_odata_string(activity_type)}')")
        if committee:
            escaped = _escape_odata_string(committee)
            filters.append(
                f"(contains(Voortouwnaam,'{escaped}') or contains(Voortouwafkorting,'{escaped}'))"
            )
        if keyword:
            escaped = _escape_odata_string(keyword)
            keyword_filters = [f"contains(Onderwerp,'{escaped}')"]
            if _is_numeric_keyword(keyword):
                keyword_filters.append(f"contains(Nummer,'{escaped}')")
            filters.append(f"({' or '.join(keyword_filters)})")
        if dossier_number:
            filters.append(_dossier_filter_for_zaak_collection("Zaak", int(dossier_number)))
        if actor:
            escaped = _escape_odata_string(actor)
            filters.append(_collection_any("ActiviteitActor", "a", f"a/ActorNaam eq '{escaped}'"))

        return self.search(
            "Activiteit",
            filter_value=" and ".join(filters),
            orderby="Datum desc",
            top=top,
        )

    def search_votes(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        dossier_number: str | None = None,
        outcome: str | None = None,
        faction: str | None = None,
        top: int = 50,
    ) -> SourceResponse:
        filters = ["Verwijderd eq false"]
        if date_from:
            filters.append(f"GewijzigdOp ge {date_from}")
        if date_to:
            filters.append(f"GewijzigdOp le {date_to}")
        if outcome:
            filters.append(f"Soort eq '{_escape_odata_string(outcome)}'")
        if dossier_number:
            filters.append(_dossier_filter_for_zaak_collection("Besluit/Zaak", int(dossier_number)))
        if faction:
            escaped = _escape_odata_string(faction)
            filters.append(f"(ActorFractie eq '{escaped}' or ActorNaam eq '{escaped}')")

        return self.search(
            "Stemming",
            filter_value=" and ".join(filters),
            expand=["Besluit($expand=Zaak($expand=Kamerstukdossier),Agendapunt)", "Persoon", "Fractie"],
            orderby="GewijzigdOp desc",
            top=top,
        )

    def search_members(self, query: str, *, top: int = 10) -> SourceResponse:
        escaped = _escape_odata_string(query)
        filter_value = (
            "Verwijderd eq false and "
            f"(contains(Roepnaam,'{escaped}') or contains(Achternaam,'{escaped}'))"
        )
        return self.search("Persoon", filter_value=filter_value, orderby="Achternaam asc", top=top)

    def list_factions(self) -> SourceResponse:
        return self.search("Fractie", filter_value="Verwijderd eq false", orderby="Naam asc", top=100)

    def list_committees(self) -> SourceResponse:
        return self.search("Commissie", filter_value="Verwijderd eq false", orderby="Naam asc", top=100)

    def get_dossier(self, dossier_number: str) -> dict[str, Any] | None:
        response = self.search(
            "Kamerstukdossier",
            filter_value=f"Nummer eq {int(dossier_number)}",
            orderby="Nummer asc",
            top=1,
        )
        return response.results[0] if response.results else None

    def healthcheck(self) -> dict[str, str]:
        response = self.search("Document", top=1)
        return {"source": self.source_name, "status": "ok", "returned_count": str(response.returned_count)}


def validate_sources(sources: Sequence[str]) -> None:
    invalid = sorted(set(sources) - SOURCE_NAMES)
    if invalid:
        raise ValueError(f"Unsupported sources: {', '.join(invalid)}")
