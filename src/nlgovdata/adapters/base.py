"""Common adapter protocol."""

from __future__ import annotations

from typing import Protocol

from nlgovdata.core.schema import SourceResponse


class SourceAdapter(Protocol):
    source_name: str

    def healthcheck(self) -> dict[str, str]: ...

    def search_documents(
        self,
        *,
        keyword: str | None = None,
        doc_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        dossier_number: str | None = None,
        max_results: int = 50,
    ) -> SourceResponse: ...
