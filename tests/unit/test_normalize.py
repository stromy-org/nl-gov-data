from __future__ import annotations

import pytest

from nlgovdata.core.normalize import (
    build_dossier_timeline,
    normalize_activity,
    normalize_committee,
    normalize_dossier,
    normalize_faction,
    normalize_koop_document,
    normalize_tk_document,
    normalize_vote,
)

from tests.conftest import load_json_fixture, load_text_fixture
from nlgovdata.utils.xml import parse_koop_search_response

pytestmark = pytest.mark.unit


def test_normalize_tk_document_extracts_dossier_and_actor() -> None:
    row = load_json_fixture("tk/documents.json")["value"][0]

    document = normalize_tk_document(row)

    assert document.doc_type == "motie"
    assert document.dossier_number == "36228"
    assert document.actors == ["Jan Jansen"]


def test_build_dossier_timeline_orders_mixed_events() -> None:
    tk_document = normalize_tk_document(load_json_fixture("tk/documents.json")["value"][0])
    koop_payload = parse_koop_search_response(load_text_fixture("koop/search.xml"))
    koop_document = normalize_koop_document(koop_payload["records"][0])
    activity = normalize_activity(load_json_fixture("tk/activities.json")["value"][0])
    vote = normalize_vote(load_json_fixture("tk/votes.json")["value"][0])

    timeline = build_dossier_timeline(
        "36228",
        dossier=None,
        tk_documents=[tk_document],
        koop_documents=[koop_document],
        activities=[activity],
        votes=[vote],
    )

    assert timeline.total_count == 4
    assert timeline.returned_count == 4
    assert [event["event_type"] for event in timeline.timeline] == ["document", "document", "activity", "vote"]


def test_build_dossier_timeline_adds_fallback_anchor_when_empty() -> None:
    dossier = normalize_dossier(load_json_fixture("tk/dossier.json")["value"][0])

    timeline = build_dossier_timeline(
        "36228",
        dossier=dossier,
        tk_documents=[],
        koop_documents=[],
        activities=[],
        votes=[],
    )

    assert timeline.total_count == 1
    assert timeline.returned_count == 1
    assert timeline.timeline[0]["event_type"] == "dossier"
    assert timeline.timeline[0]["metadata"]["fallback"] is True


def test_normalize_faction_supports_live_tk_shape() -> None:
    row = load_json_fixture("tk/factions.json")["value"][0]

    faction = normalize_faction(row)

    assert faction.name == "Partij van de Arbeid"
    assert faction.abbreviation == "PvdA"
    assert faction.seats == 25
    assert faction.active is True


def test_normalize_committee_supports_live_tk_shape() -> None:
    row = load_json_fixture("tk/committees.json")["value"][0]

    committee = normalize_committee(row)

    assert committee.name == "Commissie voor Binnenlandse Zaken"
    assert committee.abbreviation == "BZK"
