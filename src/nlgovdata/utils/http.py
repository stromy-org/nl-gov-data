"""HTTP client factory and request helpers."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any

import httpx

from nlgovdata.core.config import AppConfig

logger = logging.getLogger(__name__)


class UpstreamRequestError(RuntimeError):
    """Raised when an upstream request fails after retries."""

    def __init__(
        self,
        source: str,
        url: str,
        kind: str,
        detail: str,
        *,
        status_code: int | None = None,
    ) -> None:
        self.source = source
        self.url = url
        self.kind = kind
        self.detail = detail
        self.status_code = status_code
        status_text = f", status={status_code}" if status_code is not None else ""
        super().__init__(f"{source} request failed ({kind}{status_text}) for {url}: {detail}")


def _classify_http_error(exc: Exception) -> tuple[str, int | None, str]:
    if isinstance(exc, httpx.TimeoutException):
        return "timeout", None, str(exc)
    if isinstance(exc, httpx.NetworkError):
        return "network", None, str(exc)
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        if status_code == 429:
            kind = "rate_limited"
        elif 500 <= status_code:
            kind = "upstream_server"
        elif 400 <= status_code:
            kind = "upstream_validation"
        else:
            kind = "http_error"
        return kind, status_code, str(exc)
    if isinstance(exc, ValueError):
        return "invalid_payload", None, str(exc)
    return "request_error", None, str(exc)


class HttpRequester:
    """Thin wrapper over httpx with retry, pacing, and structured logging."""

    def __init__(
        self,
        config: AppConfig,
        *,
        client: httpx.Client | None = None,
        sleep_func: Any = time.sleep,
    ) -> None:
        self.config = config
        self._client = client or httpx.Client(
            timeout=config.timeout_seconds,
            headers={"User-Agent": config.user_agent},
            follow_redirects=True,
        )
        self._sleep = sleep_func

    def request(
        self,
        source: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        last_error: Exception | None = None

        for attempt in range(1, self.config.max_retries + 1):
            started = time.perf_counter()
            try:
                response = self._client.get(url, params=params, headers=headers)
                response.raise_for_status()
                duration_ms = int((time.perf_counter() - started) * 1000)
                logger.info(
                    "upstream_request source=%s url=%s status=%s duration_ms=%s retry_count=%s",
                    source,
                    url,
                    response.status_code,
                    duration_ms,
                    attempt - 1,
                )
                if self.config.request_interval_seconds > 0:
                    self._sleep(self.config.request_interval_seconds)
                return response
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    break
                self._sleep(min(attempt, 3))

        kind, status_code, detail = _classify_http_error(last_error or RuntimeError("unknown request failure"))
        raise UpstreamRequestError(source, url, kind, detail, status_code=status_code) from last_error

    def get_json(
        self,
        source: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        response = self.request(source, url, params=params, headers=headers)
        return response.json()

    def get_text(
        self,
        source: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> str:
        response = self.request(source, url, params=params, headers=headers)
        return response.text
