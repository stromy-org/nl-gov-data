"""Runtime dependency construction for MCP tools and CLI."""

from __future__ import annotations

from dataclasses import dataclass

from nlgovdata.adapters.koop import KoopAdapter
from nlgovdata.adapters.rijksoverheid import RijksoverheidAdapter
from nlgovdata.adapters.tk import TweedeKamerAdapter
from nlgovdata.core.config import AppConfig
from nlgovdata.utils.http import HttpRequester


@dataclass
class ServiceContainer:
    config: AppConfig
    requester: HttpRequester
    tk: TweedeKamerAdapter
    rijk: RijksoverheidAdapter
    koop: KoopAdapter


def build_services(config: AppConfig | None = None, requester: HttpRequester | None = None) -> ServiceContainer:
    resolved_config = config or AppConfig.from_env()
    resolved_requester = requester or HttpRequester(resolved_config)
    return ServiceContainer(
        config=resolved_config,
        requester=resolved_requester,
        tk=TweedeKamerAdapter(resolved_config, resolved_requester),
        rijk=RijksoverheidAdapter(resolved_config, resolved_requester),
        koop=KoopAdapter(resolved_config, resolved_requester),
    )
