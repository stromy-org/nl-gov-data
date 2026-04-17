from __future__ import annotations

import pytest

from nlgovdata.adapters.koop import KoopAdapter
from nlgovdata.adapters.rijksoverheid import RijksoverheidAdapter
from nlgovdata.adapters.tk import TweedeKamerAdapter

from tests.conftest import FakeRequester, load_json_fixture, load_text_fixture

pytestmark = pytest.mark.unit


def test_tk_search_documents_builds_odata_filter(app_config) -> None:
    requester = FakeRequester(json_responses={"Document": load_json_fixture("tk/documents.json")})
    adapter = TweedeKamerAdapter(app_config, requester)

    response = adapter.search_documents(keyword="woningbouw", dossier_number="36228", doc_type="motie", max_results=5)

    assert response.source == "tk"
    assert response.total_count == 1
    assert response.results[0]["Titel"] == "Motie over woningbouw"
    assert "Kamerstukdossier/any(d:d/Nummer eq 36228)" in requester.calls[0]["params"]["$filter"]
    assert "Soort eq 'Motie'" in requester.calls[0]["params"]["$filter"]


def test_tk_search_activities_avoids_numeric_field_for_name_queries(app_config) -> None:
    requester = FakeRequester(json_responses={"Activiteit": load_json_fixture("tk/activities.json")})
    adapter = TweedeKamerAdapter(app_config, requester)

    response = adapter.search_activities(keyword="Frans Timmermans", top=5)

    assert response.source == "tk"
    assert "contains(Onderwerp,'Frans Timmermans')" in requester.calls[0]["params"]["$filter"]
    assert "contains(Nummer,'Frans Timmermans')" not in requester.calls[0]["params"]["$filter"]


def test_tk_search_activities_can_filter_by_dossier_and_actor(app_config) -> None:
    requester = FakeRequester(json_responses={"Activiteit": load_json_fixture("tk/activities.json")})
    adapter = TweedeKamerAdapter(app_config, requester)

    response = adapter.search_activities(dossier_number="36228", actor="Frans Timmermans", top=5)

    assert response.source == "tk"
    filter_value = requester.calls[0]["params"]["$filter"]
    assert "Zaak/any(z:z/Kamerstukdossier/any(d:d/Nummer eq 36228))" in filter_value
    assert "ActiviteitActor/any(a:a/ActorNaam eq 'Frans Timmermans')" in filter_value


def test_tk_search_votes_builds_live_safe_filters(app_config) -> None:
    requester = FakeRequester(json_responses={"Stemming": load_json_fixture("tk/votes.json")})
    adapter = TweedeKamerAdapter(app_config, requester)

    response = adapter.search_votes(dossier_number="36228", outcome="Voor", faction="GL-PvdA", top=5)

    assert response.source == "tk"
    filter_value = requester.calls[0]["params"]["$filter"]
    assert "Besluit/Zaak/any(z:z/Kamerstukdossier/any(d:d/Nummer eq 36228))" in filter_value
    assert "Soort eq 'Voor'" in filter_value
    assert "(ActorFractie eq 'GL-PvdA' or ActorNaam eq 'GL-PvdA')" in filter_value


def test_rijk_search_documents_fans_out_and_filters_keyword(app_config) -> None:
    requester = FakeRequester(
        json_responses={
            "documents": load_json_fixture("rijksoverheid/documents.json"),
            "infotypes/news": load_json_fixture("rijksoverheid/news.json"),
            "infotypes/faq": load_json_fixture("rijksoverheid/faq.json"),
        }
    )
    adapter = RijksoverheidAdapter(app_config, requester)

    response = adapter.search_documents(keyword="woningbouw", doc_type="kamerstuk", max_results=10)

    assert response.returned_count == 3
    assert response.total_count == 3
    assert {row["_endpoint"] for row in response.results} == {"documents", "news", "faq"}


def test_koop_search_documents_parses_xml(app_config) -> None:
    requester = FakeRequester(text_responses={"koop.test/sru": load_text_fixture("koop/search.xml")})
    adapter = KoopAdapter(app_config, requester)

    response = adapter.search_documents(keyword="woningbouw", dossier_number="36228", doc_type="motie")

    assert response.total_count == 1
    assert response.results[0]["identifier"] == "kst-36228-3"
    assert "w.dossiernummer==36228" in requester.calls[0]["params"]["query"]
