"""Source-to-unified normalization helpers."""

from __future__ import annotations

import re
from dataclasses import asdict
from html import unescape
from typing import Any, Iterable, Sequence

from .schema import (
    Activity,
    Committee,
    Dossier,
    DossierTimelineResponse,
    Faction,
    GovernmentDocument,
    ParliamentMember,
    TimelineEvent,
    Vote,
)
from .types import normalize_doc_type, slugify

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+", " ", unescape(_HTML_TAG_RE.sub(" ", value))).strip() or None


def _deep_get(mapping: dict[str, Any], *paths: Sequence[str]) -> Any:
    for path in paths:
        current: Any = mapping
        found = True
        for part in path:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                found = False
                break
        if found and current not in (None, "", []):
            return current
    return None


def _to_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _unique_strings(values: Iterable[str | None]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        if not value:
            continue
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        items.append(cleaned)
    return items


def _primary_document_date(document: GovernmentDocument) -> str:
    return document.published_at or document.issued_at or document.modified_at or ""


def normalize_tk_document(record: dict[str, Any]) -> GovernmentDocument:
    dossier = _deep_get(
        record,
        ("Zaak", "Kamerstukdossier", "Nummer"),
        ("Kamerstukdossier", "Nummer"),
    )
    dossier_title = _deep_get(
        record,
        ("Zaak", "Titel"),
        ("Kamerstukdossier", "Titel"),
    )
    actors = [
        _deep_get(actor, ("Persoon", "Naam"), ("Naam",), ("PersoonNaam",))
        for actor in _to_list(record.get("DocumentActor"))
    ]
    organizations = _unique_strings(
        [
            _deep_get(record, ("Zaak", "BehandelendeOrganisatie"), ("Organisatie", "Naam")),
            _deep_get(record, ("Kamer", "Naam")),
        ]
    )
    subjects = _unique_strings([dossier_title, record.get("Onderwerp")])

    return GovernmentDocument(
        id=f"tk:{record.get('Id', 'unknown')}",
        source="tk",
        title=record.get("Titel") or record.get("Onderwerp") or "Untitled document",
        doc_type=normalize_doc_type("tk", record.get("Soort")),
        doc_type_raw=record.get("Soort") or "unknown",
        dossier_number=str(dossier) if dossier is not None else None,
        dossier_sub_number=str(record.get("Nummer")) if record.get("Nummer") not in (None, "") else None,
        published_at=record.get("Datum"),
        issued_at=record.get("DatumRegistratie"),
        modified_at=record.get("GewijzigdOp") or record.get("ApiGewijzigdOp"),
        summary=_strip_html(record.get("Onderwerp")),
        content_url=record.get("resourceUrl") or record.get("PdfUrl"),
        subjects=subjects,
        organizations=organizations,
        actors=_unique_strings(actors),
        metadata=record,
    )


def normalize_rijk_document(record: dict[str, Any]) -> GovernmentDocument:
    summary = _strip_html(record.get("introduction"))
    organizations = _unique_strings(
        [
            record.get("organisationalUnit"),
            record.get("ministerie"),
            record.get("creator"),
        ]
    )
    subjects = _unique_strings(_to_list(record.get("subject")) + _to_list(record.get("subjects")))

    return GovernmentDocument(
        id=f"rijk:{record.get('id', 'unknown')}",
        source="rijksoverheid",
        title=record.get("title") or "Untitled record",
        doc_type=normalize_doc_type("rijksoverheid", record.get("type")),
        doc_type_raw=record.get("type") or "unknown",
        dossier_number=None,
        dossier_sub_number=None,
        published_at=record.get("available") or record.get("frontenddate"),
        issued_at=record.get("issued"),
        modified_at=record.get("lastmodified"),
        summary=summary,
        content_url=record.get("url"),
        subjects=subjects,
        organizations=organizations,
        actors=[],
        metadata=record,
    )


def normalize_koop_document(record: dict[str, Any]) -> GovernmentDocument:
    return GovernmentDocument(
        id=f"koop:{record.get('identifier', 'unknown')}",
        source="koop",
        title=record.get("title") or "Untitled publication",
        doc_type=normalize_doc_type("koop", record.get("type"), subrubriek=record.get("subrubriek")),
        doc_type_raw=record.get("type") or "unknown",
        dossier_number=record.get("dossier_number"),
        dossier_sub_number=record.get("dossier_sub_number"),
        published_at=record.get("available"),
        issued_at=record.get("issued"),
        modified_at=record.get("modified"),
        summary=_strip_html(record.get("summary") or record.get("description")),
        content_url=record.get("preferred_url") or record.get("portal_url") or record.get("pdf_url"),
        subjects=_unique_strings([record.get("product_area"), record.get("subrubriek")]),
        organizations=_unique_strings([record.get("creator")]),
        actors=[],
        metadata=record.get("metadata", record),
    )


def normalize_activity(record: dict[str, Any]) -> Activity:
    actors = [
        _deep_get(actor, ("Persoon", "Naam"), ("Naam",))
        for actor in _to_list(record.get("ActiviteitActor"))
    ]
    organizations = _unique_strings(
        [
            _deep_get(record, ("Commissie", "Naam")),
            _deep_get(record, ("Vergadering", "Naam")),
            record.get("Voortouwnaam"),
            record.get("Voortouwafkorting"),
        ]
    )
    raw_type = record.get("Soort") or record.get("Type") or "unknown"
    return Activity(
        id=f"tk:{record.get('Id', 'unknown')}",
        type=slugify(raw_type).replace(" ", "_"),
        type_raw=raw_type,
        subject=record.get("Onderwerp") or record.get("Titel") or "Untitled activity",
        date=record.get("Datum") or "",
        start_time=record.get("Aanvangstijd"),
        end_time=record.get("Eindtijd"),
        status=slugify(record.get("Status") or "unknown").replace(" ", "_"),
        organizations=organizations,
        actors=_unique_strings(actors),
        metadata=record,
    )


def normalize_vote(record: dict[str, Any]) -> Vote:
    actor_name = record.get("ActorNaam")
    actor_size = record.get("FractieGrootte")
    factions_for = (
        [{"name": actor_name, "seats": actor_size}]
        if record.get("Soort") == "Voor" and actor_name
        else []
    )
    factions_against = (
        [{"name": actor_name, "seats": actor_size}]
        if record.get("Soort") == "Tegen" and actor_name
        else []
    )

    return Vote(
        id=f"tk:{record.get('Id', 'unknown')}",
        decision_type=slugify(record.get("Soort") or record.get("Uitslag") or "unknown"),
        decision_text=(
            _deep_get(record, ("Besluit", "BesluitTekst"), ("Besluit", "Status"))
            or record.get("BesluitTekst")
            or record.get("Titel")
            or ""
        ),
        factions_for=factions_for
        or [
            {"name": side.get("Naam"), "seats": side.get("Zetels")}
            for side in _to_list(record.get("FractiesVoor"))
            if side.get("Naam")
        ],
        factions_against=factions_against
        or [
            {"name": side.get("Naam"), "seats": side.get("Zetels")}
            for side in _to_list(record.get("FractiesTegen"))
            if side.get("Naam")
        ],
        related_document=_deep_get(
            record,
            ("Besluit", "Agendapunt", "Onderwerp"),
            ("Besluit", "Opmerking"),
            ("Besluit", "Document", "Titel"),
        ),
        sort_date=(
            record.get("GewijzigdOp")
            or record.get("ApiGewijzigdOp")
            or record.get("Datum")
            or _deep_get(record, ("Besluit", "Datum"))
        ),
        metadata=record,
    )


def normalize_member(record: dict[str, Any]) -> ParliamentMember:
    name = " ".join(part for part in [record.get("Roepnaam"), record.get("Achternaam")] if part).strip()
    faction = _deep_get(
        record,
        ("Fractielabel",),
        ("Fractie", "Afkorting"),
        ("Fractie", "NaamNL"),
        ("Fractie", "Naam"),
        ("FractieZetelPersoon", "FractieZetel", "Fractie", "Afkorting"),
        ("FractieZetelPersoon", "FractieZetel", "Fractie", "NaamNL"),
    )
    return ParliamentMember(
        id=f"tk:{record.get('Id', 'unknown')}",
        name=name or record.get("Naam") or "Unknown member",
        faction=faction,
        role="former_mp" if record.get("Overleden") else "mp",
        active=not bool(record.get("Verwijderd")),
        metadata=record,
    )


def normalize_faction(record: dict[str, Any]) -> Faction:
    active = not bool(record.get("Verwijderd")) and not bool(record.get("DatumInactief"))
    name = record.get("NaamNL") or record.get("Naam") or "Unknown faction"
    return Faction(
        id=f"tk:{record.get('Id', 'unknown')}",
        name=name,
        abbreviation=record.get("Afkorting") or name,
        seats=int(record.get("AantalZetels") or record.get("ZetelAantal") or 0),
        active=active,
        metadata=record,
    )


def normalize_committee(record: dict[str, Any]) -> Committee:
    return Committee(
        id=f"tk:{record.get('Id', 'unknown')}",
        name=record.get("NaamNL") or record.get("Naam") or "Unknown committee",
        abbreviation=record.get("Afkorting"),
        metadata=record,
    )


def normalize_dossier(record: dict[str, Any]) -> Dossier:
    return Dossier(
        id=f"tk:{record.get('Id', 'unknown')}",
        number=int(record.get("Nummer") or 0),
        title=record.get("Titel") or "Untitled dossier",
        closed=bool(record.get("Afgesloten")),
        chamber=record.get("Kamer") or "Tweede Kamer",
        metadata=record,
    )


def sort_documents_desc(documents: Iterable[GovernmentDocument]) -> list[GovernmentDocument]:
    return sorted(documents, key=_primary_document_date, reverse=True)


def _timeline_event_sort_key(event: TimelineEvent) -> str:
    return event.sort_date


def _dossier_anchor_date(dossier: Dossier) -> str | None:
    return (
        dossier.metadata.get("GewijzigdOp")
        or dossier.metadata.get("ApiGewijzigdOp")
        or dossier.metadata.get("Datum")
    )


def build_dossier_timeline(
    dossier_number: str,
    dossier: Dossier | None,
    tk_documents: Iterable[GovernmentDocument],
    koop_documents: Iterable[GovernmentDocument],
    activities: Iterable[Activity],
    votes: Iterable[Vote],
    warnings: list[str] | None = None,
) -> DossierTimelineResponse:
    timeline: list[TimelineEvent] = []

    for document in [*tk_documents, *koop_documents]:
        sort_date = _primary_document_date(document)
        if not sort_date:
            continue
        timeline.append(
            TimelineEvent(
                id=document.id,
                event_type="document",
                source=document.source,
                sort_date=sort_date,
                title=document.title,
                summary=document.summary,
                status=None,
                actors=document.actors,
                organizations=document.organizations,
                document=document,
                metadata={"dossier_number": document.dossier_number},
            )
        )

    for activity in activities:
        if not activity.date:
            continue
        sort_date = activity.date if not activity.start_time else f"{activity.date}T{activity.start_time}"
        timeline.append(
            TimelineEvent(
                id=activity.id,
                event_type="activity",
                source="tk",
                sort_date=sort_date,
                title=activity.subject,
                summary=None,
                status=activity.status,
                actors=activity.actors,
                organizations=activity.organizations,
                activity=activity,
                metadata={},
            )
        )

    for vote in votes:
        if not vote.sort_date:
            continue
        timeline.append(
            TimelineEvent(
                id=vote.id,
                event_type="vote",
                source="tk",
                sort_date=vote.sort_date,
                title=vote.decision_text,
                summary=vote.related_document,
                status=vote.decision_type,
                actors=[],
                organizations=[],
                vote=vote,
                metadata={},
            )
        )

    if not timeline and dossier:
        timeline.append(
            TimelineEvent(
                id=dossier.id,
                event_type="dossier",
                source="tk",
                sort_date=_dossier_anchor_date(dossier) or "",
                title=dossier.title,
                summary=(
                    "Fallback dossier anchor from the Tweede Kamer register. "
                    "Linked timeline events were unavailable from upstream queries."
                ),
                status="closed" if dossier.closed else "open",
                actors=[],
                organizations=[dossier.chamber],
                metadata={
                    "fallback": True,
                    "dossier_number": str(dossier.number),
                },
            )
        )

    payload = [asdict(event) for event in sorted(timeline, key=_timeline_event_sort_key)]
    return DossierTimelineResponse(
        dossier_number=dossier_number,
        dossier=dossier,
        total_count=len(payload),
        returned_count=len(payload),
        timeline=payload,
        warnings=warnings or [],
    )
