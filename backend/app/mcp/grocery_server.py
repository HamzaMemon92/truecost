"""
Grocery MCP Server (FastMCP)

ALL tools read from GroceryObservationRepository.
NO live provider network calls are made from this server.

When no observations exist for a query, returns empty list.
Does NOT silently fall back to provider.search() or any network call.

Tools:
  search_items(query)          — returns CanonicalGroceryItem dicts from observation repo
  get_item_details(item_id)    — stub; returns empty details dict
  get_availability(item_id)    — stub; returns "unknown"
  get_delivery_estimate(prov)  — stub; returns "unknown" eta
  get_offers(item_id)          — stub; returns []
  get_provider_link(item_id)   — stub; returns empty string
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP


def create_grocery_mcp_server() -> FastMCP:
    """Create the Grocery MCP server. All tools read from the observation repository."""
    mcp = FastMCP("decision-advisor-grocery", dependencies=[])

    @mcp.tool()
    async def search_items(query: str) -> dict[str, Any]:
        """
        Search for grocery items by query string.

        Reads ONLY from GroceryObservationRepository (ingest-backed observations).
        Returns empty list when no observations exist for this query.
        NEVER calls provider network.

        Returns:
            query: the input query
            items: list of CanonicalGroceryItem-compatible dicts
            source: "observation_repository"
            provider_network_calls: always 0
        """
        from app.repositories.grocery_observation_repository import (
            GROCERY_OBSERVATION_PROVIDERS,
            grocery_observations,
        )

        items = grocery_observations.search_observations_as_canonical(
            query, GROCERY_OBSERVATION_PROVIDERS
        )
        return {
            "query": query,
            "items": items,
            "source": "observation_repository",
            "provider_network_calls": 0,
        }

    @mcp.tool()
    async def get_item_details(item_id: str) -> dict[str, Any]:
        """Get detailed information for a specific grocery item by canonical ID."""
        return {"item_id": item_id, "details": {}}

    @mcp.tool()
    async def get_availability(item_id: str) -> dict[str, Any]:
        """Check grocery item availability. Returns 'unknown' without network calls."""
        return {"item_id": item_id, "availability": "unknown"}

    @mcp.tool()
    async def get_delivery_estimate(provider: str) -> dict[str, Any]:
        """Get estimated delivery time for a provider (stub)."""
        return {"provider": provider, "eta": "unknown", "delivery_fee": None}

    @mcp.tool()
    async def get_offers(item_id: str) -> dict[str, Any]:
        """Get available offers for a grocery item (stub)."""
        return {"item_id": item_id, "offers": []}

    @mcp.tool()
    async def get_provider_link(item_id: str) -> dict[str, Any]:
        """Get provider deep link for a grocery item (stub)."""
        return {"item_id": item_id, "link": ""}

    return mcp
