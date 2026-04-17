"""Operator CLI for nl-gov-data."""

from __future__ import annotations

import json
import logging

import click

from nlgovdata.cli.health import run_connectivity_checks
from nlgovdata.core.source_info import build_source_catalog
from nlgovdata.mcp.dependencies import build_services

logger = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose: bool) -> None:
    """Dutch government data MCP CLI."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["json", "text"]), default="json")
def list_sources(fmt: str) -> None:
    """List configured upstream sources."""
    services = build_services()
    catalog = build_source_catalog(
        tk_base_url=services.config.tk_base_url,
        rijk_base_url=services.config.rijk_base_url,
        koop_base_url=services.config.koop_base_url,
    )
    if fmt == "json":
        click.echo(json.dumps(catalog, indent=2))
        return

    for item in catalog:
        click.echo(
            "\n".join(
                [
                    f"{item['source']}: {item['name']}",
                    f"  protocol: {item['protocol']}",
                    f"  base_url: {item['base_url']}",
                    f"  native_tools: {', '.join(item['native_tools'])}",
                    f"  unified_contributions: {', '.join(item['unified_contributions'])}",
                ]
            )
        )


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["json", "text"]), default="json")
@click.option("--source", "sources", multiple=True, type=click.Choice(["tk", "rijksoverheid", "koop"]))
def test_connection(fmt: str, sources: tuple[str, ...]) -> None:
    """Run a lightweight connectivity check against all upstreams."""
    services = build_services()
    selected_sources = list(sources) if sources else None
    payload = run_connectivity_checks(services, sources=selected_sources)

    if fmt == "json":
        click.echo(json.dumps(payload, indent=2))
    else:
        for item in payload:
            summary = (
                f"{item['source']}: {item['status']} "
                f"(reachable={item['reachable']}, duration_ms={item['duration_ms']})"
            )
            click.echo(summary)
            if item.get("returned_count") is not None:
                click.echo(f"  returned_count: {item['returned_count']}")
            if item.get("error"):
                click.echo(f"  error: {item['error']}")

    if any(not item["reachable"] for item in payload):
        raise click.ClickException("One or more upstream connectivity checks failed")


@cli.command()
def serve() -> None:
    """Start the FastMCP stdio server."""
    from nlgovdata.mcp.server import mcp

    mcp.run()


def main() -> None:
    cli()
