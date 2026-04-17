"""Shared constants and normalization maps."""

from __future__ import annotations

from typing import Final

SOURCE_NAMES: Final[frozenset[str]] = frozenset({"tk", "rijksoverheid", "koop"})

TK_ENTITY_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "Activiteit",
        "Besluit",
        "Commissie",
        "Document",
        "DocumentActor",
        "Fractie",
        "Kamerstukdossier",
        "Persoon",
        "Stemming",
        "Vergadering",
        "Zaak",
    }
)

RIJKSOVERHEID_ENDPOINTS: Final[dict[str, str]] = {
    "documents": "documents",
    "news": "infotypes/news",
    "faq": "infotypes/faq",
    "subject": "infotypes/subject",
    "ministry": "infotypes/ministry",
}

KOOP_COLLECTIONS: Final[frozenset[str]] = frozenset(
    {
        "officielepublicaties",
        "sgd",
        "bwb",
        "wetgevingskalender",
    }
)

DOCUMENT_TYPE_MAP: Final[dict[str, dict[str, str]]] = {
    "tk": {
        "motie": "motie",
        "amendement": "amendement",
        "brief regering": "brief",
        "brief": "brief",
    },
    "rijksoverheid": {
        "parliamentarydocument": "kamerstuk",
        "rapport": "rapport",
        "besluit": "besluit",
        "toespraak": "toespraak",
        "nieuwsbericht": "nieuwsbericht",
        "vraag en antwoord": "faq",
        "regeling": "wetgeving",
        "brief": "brief",
    },
    "koop": {
        "kamerstuk": "kamerstuk",
        "handeling": "handeling",
        "staatsblad": "wetgeving",
        "staatscourant": "wetgeving",
    },
}

KOOP_SUBRUBRIEK_NORMALIZATION: Final[dict[str, str]] = {
    "motie": "motie",
    "amendement": "amendement",
    "brief": "brief",
}

TK_DOC_TYPE_FILTERS: Final[dict[str, str]] = {
    "motie": "Motie",
    "amendement": "Amendement",
    "brief": "Brief",
}

RIJK_DOC_TYPE_FILTERS: Final[dict[str, str]] = {
    "kamerstuk": "parliamentarydocument",
    "rapport": "rapport",
    "besluit": "besluit",
    "toespraak": "toespraak",
    "brief": "brief",
}

KOOP_DOC_TYPE_FILTERS: Final[dict[str, tuple[str, str | None]]] = {
    "motie": ("Kamerstuk", "Motie"),
    "amendement": ("Kamerstuk", "Amendement"),
    "brief": ("Kamerstuk", "Brief"),
    "kamerstuk": ("Kamerstuk", None),
    "handeling": ("Handeling", None),
    "wetgeving": ("Staatsblad", None),
}


def slugify(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace("/", " ")
        .replace("-", " ")
        .replace("_", " ")
        .replace("  ", " ")
        .strip()
    )


def normalize_doc_type(source: str, raw_type: str | None, *, subrubriek: str | None = None) -> str:
    if subrubriek:
        mapped = KOOP_SUBRUBRIEK_NORMALIZATION.get(slugify(subrubriek))
        if mapped:
            return mapped

    if not raw_type:
        return "overig"

    key = slugify(raw_type)
    mapped = DOCUMENT_TYPE_MAP.get(source, {}).get(key)
    if mapped:
        return mapped

    if key in {"nieuws", "news"}:
        return "nieuwsbericht"
    if key in {"faq", "vraag en antwoord"}:
        return "faq"
    return "overig"
