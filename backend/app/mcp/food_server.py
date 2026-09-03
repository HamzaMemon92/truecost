from __future__ import annotations
from typing import Any
from mcp.server.fastmcp import FastMCP

def create_food_mcp_server() -> FastMCP:
    """Create the Food MCP server."""
    mcp = FastMCP("decision-advisor-food", dependencies=[])

    @mcp.tool()
    async def search_food(query: str) -> dict[str, Any]:
        """Search for food by query."""
        from app.repositories.search_cache import search_cache
        results = search_cache.search("food", query)
        if not results:
            return {"results": [], "source": "cache_miss", "note": "Ingest provider data first via POST /api/v1/aggregator/ingest"}
        return {"query": query, "results": results, "source": "cache_hit"}

    return mcp
