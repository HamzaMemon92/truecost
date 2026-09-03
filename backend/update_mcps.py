import os

servers = [
    ("food_server.py", "food", "create_food_mcp_server", "decision-advisor-food"),
    ("pharmacy_server.py", "pharmacy", "create_pharmacy_mcp_server", "decision-advisor-pharmacy"),
    ("mobility_server.py", "mobility", "create_mobility_mcp_server", "decision-advisor-mobility"),
    ("travel_server.py", "travel", "create_travel_mcp_server", "decision-advisor-travel"),
    ("finance_server.py", "finance", "create_finance_mcp_server", "decision-advisor-finance"),
    ("productivity_server.py", "productivity", "create_productivity_mcp_server", "decision-advisor-productivity")
]

for filename, category, func_name, mcp_name in servers:
    path = os.path.join("app", "mcp", filename)
    with open(path, "r") as f:
        content = f.read()
    
    # We will just rewrite the whole file, it's easier and safer
    new_content = f'''from __future__ import annotations
from typing import Any
from mcp.server.fastmcp import FastMCP

def {func_name}() -> FastMCP:
    """Create the {category.capitalize()} MCP server."""
    mcp = FastMCP("{mcp_name}", dependencies=[])

    @mcp.tool()
    async def search_{category}(query: str) -> dict[str, Any]:
        """Search for {category} by query."""
        from app.repositories.search_cache import search_cache
        results = search_cache.search("{category}", query)
        if not results:
            return {{"results": [], "source": "cache_miss", "note": "Ingest provider data first via POST /api/v1/aggregator/ingest"}}
        return {{"query": query, "results": results, "source": "cache_hit"}}

    return mcp
'''
    with open(path, "w") as f:
        f.write(new_content)

