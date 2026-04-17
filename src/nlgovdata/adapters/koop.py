"""KOOP SRU adapter."""

from __future__ import annotations

from nlgovdata.core.config import AppConfig
from nlgovdata.core.schema import SourceResponse
from nlgovdata.core.types import KOOP_COLLECTIONS, KOOP_DOC_TYPE_FILTERS
from nlgovdata.utils.http import HttpRequester
from nlgovdata.utils.xml import parse_koop_search_response


class KoopAdapter:
    source_name = "koop"

    def __init__(self, config: AppConfig, requester: HttpRequester) -> None:
        self.config = config
        self.requester = requester

    def search(
        self,
        query: str,
        *,
        collection: str = "officielepublicaties",
        max_records: int = 50,
        start_record: int = 1,
        sort: str | None = None,
    ) -> SourceResponse:
        if collection not in KOOP_COLLECTIONS:
            raise ValueError(f"Unsupported KOOP collection: {collection}")

        query_value = query
        if sort:
            query_value = f"{query_value} sortBy {sort}"

        params = {
            "version": "2.0",
            "operation": "searchRetrieve",
            "x-connection": collection,
            "query": query_value,
            "startRecord": start_record,
            "maximumRecords": min(max_records, 1000),
        }
        xml_text = self.requester.get_text(self.source_name, self.config.koop_base_url, params=params)
        payload = parse_koop_search_response(xml_text)
        return SourceResponse(
            source=self.source_name,
            total_count=payload["total_count"],
            returned_count=len(payload["records"]),
            next_cursor=str(payload["next_record_position"]) if payload["next_record_position"] else None,
            results=payload["records"],
            warnings=[],
        )

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
        clauses: list[str] = []
        if keyword:
            clauses.append(f'(dt.title all "{keyword}" OR w.documenttitel all "{keyword}")')
        if dossier_number:
            clauses.append(f"w.dossiernummer=={dossier_number}")
        if doc_type and doc_type in KOOP_DOC_TYPE_FILTERS:
            raw_type, subrubriek = KOOP_DOC_TYPE_FILTERS[doc_type]
            clauses.append(f'dt.type=="{raw_type}"')
            if subrubriek:
                clauses.append(f'w.subrubriek=="{subrubriek}"')
        if date_from:
            clauses.append(f"dt.modified>={date_from}")
        if date_to:
            clauses.append(f"dt.modified<={date_to}")
        query = " AND ".join(clauses) if clauses else "dt.identifier any *"
        return self.search(query, max_records=max_results, sort="dt.modified /sort.descending")

    def healthcheck(self) -> dict[str, str]:
        response = self.search("dt.identifier any *", max_records=1)
        return {"source": self.source_name, "status": "ok", "returned_count": str(response.returned_count)}
