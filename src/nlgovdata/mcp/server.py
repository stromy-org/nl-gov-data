"""FastMCP server composition root."""

from __future__ import annotations

from fastmcp import FastMCP

from nlgovdata.mcp.dependencies import build_services
from nlgovdata.mcp.resources import register_resources
from nlgovdata.mcp.tools_koop import register_koop_tools
from nlgovdata.mcp.tools_rijk import register_rijk_tools
from nlgovdata.mcp.tools_tk import register_tk_tools
from nlgovdata.mcp.tools_unified import register_unified_tools

services = build_services()

mcp = FastMCP("Dutch Government Data", version="0.1.0")

register_tk_tools(mcp, services)
register_rijk_tools(mcp, services)
register_koop_tools(mcp, services)
register_unified_tools(mcp, services)
register_resources(mcp, services)
