from __future__ import annotations
from typing import Any
from mcp.server.fastmcp import FastMCP

def create_mobility_mcp_server() -> FastMCP:
    """Create the Mobility MCP server."""
    mcp = FastMCP("decision-advisor-mobility", dependencies=[])

    @mcp.tool()
    async def search_mobility(query: str) -> dict[str, Any]:
        """Search for mobility by query."""
        from app.repositories.search_cache import search_cache
        results = search_cache.search("mobility", query)
        if not results:
            return {"results": [], "source": "cache_miss", "note": "Ingest provider data first via POST /api/v1/aggregator/ingest"}
        return {"query": query, "results": results, "source": "cache_hit"}

    return mcp
