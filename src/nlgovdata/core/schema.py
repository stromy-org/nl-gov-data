"""Immutable data contracts for source-native and unified responses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceResponse:
    source: str
    total_count: int | None
    returned_count: int
    next_cursor: str | None
    results: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UnifiedResponse:
    total_count: int | None
    returned_count: int
    results: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GovernmentDocument:
    id: str
    source: str
    title: str
    doc_type: str
    doc_type_raw: str
    dossier_number: str | None
    dossier_sub_number: str | None
    published_at: str | None
    issued_at: str | None
    modified_at: str | None
    summary: str | None
    content_url: str | None
    subjects: list[str]
    organizations: list[str]
    actors: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ParliamentMember:
    id: str
    name: str
    faction: str | None
    role: str
    active: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Faction:
    id: str
    name: str
    abbreviation: str
    seats: int
    active: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Committee:
    id: str
    name: str
    abbreviation: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Dossier:
    id: str
    number: int
    title: str
    closed: bool
    chamber: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Activity:
    id: str
    type: str
    type_raw: str
    subject: str
    date: str
    start_time: str | None
    end_time: str | None
    status: str
    organizations: list[str] = field(default_factory=list)
    actors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Vote:
    id: str
    decision_type: str
    decision_text: str
    factions_for: list[dict[str, Any]]
    factions_against: list[dict[str, Any]]
    related_document: str | None
    sort_date: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TimelineEvent:
    id: str
    event_type: str
    source: str
    sort_date: str
    title: str
    summary: str | None
    status: str | None
    actors: list[str]
    organizations: list[str]
    document: GovernmentDocument | None = None
    activity: Activity | None = None
    vote: Vote | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DossierTimelineResponse:
    dossier_number: str
    dossier: Dossier | None
    returned_count: int
    timeline: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)
