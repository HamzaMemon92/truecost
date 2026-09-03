from __future__ import annotations
from typing import Any
from mcp.server.fastmcp import FastMCP

def create_pharmacy_mcp_server() -> FastMCP:
    """Create the Pharmacy MCP server."""
    mcp = FastMCP("decision-advisor-pharmacy", dependencies=[])

    @mcp.tool()
    async def search_pharmacy(query: str) -> dict[str, Any]:
        """Search for pharmacy by query."""
        from app.repositories.search_cache import search_cache
        results = search_cache.search("pharmacy", query)
        if not results:
            return {"results": [], "source": "cache_miss", "note": "Ingest provider data first via POST /api/v1/aggregator/ingest"}
        return {"query": query, "results": results, "source": "cache_hit"}

    return mcp
