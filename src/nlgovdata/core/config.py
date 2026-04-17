"""Configuration loading for nl-gov-data."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _read_local_dotenv() -> dict[str, str]:
    candidates = [Path.cwd() / ".env"]
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            candidates.append(parent / ".env")
            break

    for env_path in candidates:
        if not env_path.exists():
            continue
        values: dict[str, str] = {}
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
        return values

    return {}


@dataclass(frozen=True)
class AppConfig:
    tk_base_url: str = "https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0"
    rijk_base_url: str = "https://opendata.rijksoverheid.nl/v1"
    koop_base_url: str = "https://repository.overheid.nl/sru"
    timeout_seconds: float = 30.0
    max_retries: int = 3
    request_interval_seconds: float = 1.0
    cache_ttl_seconds: int = 3600
    user_agent: str = "nl-gov-data/0.1.0"

    @classmethod
    def from_env(cls) -> "AppConfig":
        defaults = cls()
        values = _read_local_dotenv()
        values.update({k: v for k, v in os.environ.items() if k.startswith("NLGOVDATA_")})

        return cls(
            tk_base_url=values.get("NLGOVDATA_TK_BASE_URL", defaults.tk_base_url),
            rijk_base_url=values.get("NLGOVDATA_RIJK_BASE_URL", defaults.rijk_base_url),
            koop_base_url=values.get("NLGOVDATA_KOOP_BASE_URL", defaults.koop_base_url),
            timeout_seconds=float(values.get("NLGOVDATA_TIMEOUT_SECONDS", defaults.timeout_seconds)),
            max_retries=int(values.get("NLGOVDATA_MAX_RETRIES", defaults.max_retries)),
            request_interval_seconds=float(
                values.get("NLGOVDATA_REQUEST_INTERVAL_SECONDS", defaults.request_interval_seconds)
            ),
            cache_ttl_seconds=int(values.get("NLGOVDATA_CACHE_TTL_SECONDS", defaults.cache_ttl_seconds)),
            user_agent=values.get("NLGOVDATA_USER_AGENT", defaults.user_agent),
        )
