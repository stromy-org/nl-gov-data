from __future__ import annotations

import httpx
import pytest

from nlgovdata.utils.http import HttpRequester, UpstreamRequestError

pytestmark = pytest.mark.unit


def test_http_requester_classifies_upstream_server_errors(app_config) -> None:
    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, request=request, text="Service unavailable")

    requester = HttpRequester(app_config, client=httpx.Client(transport=httpx.MockTransport(_handler)))

    with pytest.raises(UpstreamRequestError, match=r"upstream_server, status=503"):
        requester.get_json("koop", "https://koop.test/sru")


def test_http_requester_classifies_upstream_validation_errors(app_config) -> None:
    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, request=request, text="Bad request")

    requester = HttpRequester(app_config, client=httpx.Client(transport=httpx.MockTransport(_handler)))

    with pytest.raises(UpstreamRequestError, match=r"upstream_validation, status=400"):
        requester.get_json("tk", "https://tk.test/OData/v4/2.0/Fractie")
