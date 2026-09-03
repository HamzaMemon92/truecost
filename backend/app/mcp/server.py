from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP


def create_shopping_mcp_server() -> FastMCP:
    """Create an official MCP SDK v2 server with shopping-scoped tools."""
    mcp = FastMCP("shopping-mcp-server")

    @mcp.tool()
    async def search_products(query: str) -> dict[str, Any]:
        """Search for products by query string."""
        from app.providers.registry import get_providers
        from app.providers.base import normalize_provider_results
        providers = get_providers()
        all_results = []
        for provider in providers:
            try:
                items = await provider.search(query)
                normalized = normalize_provider_results(provider, items)
                # Convert CanonicalProduct to dict
                all_results.extend([item.model_dump(mode="json") for item in normalized])
            except Exception:
                pass
        return {
            "query": query,
            "results": all_results,
        }

    @mcp.tool()
    def get_product_details(product_id: str) -> dict[str, Any]:
        """Get detailed information for a specific product."""
        return {"product_id": product_id, "status": "ok"}

    @mcp.tool()
    def get_price(product_id: str) -> dict[str, Any]:
        """Get current price of a product."""
        return {"product_id": product_id, "price": 79999}

    @mcp.tool()
    def get_offers(product_id: str) -> dict[str, Any]:
        """Get available offers for a product."""
        return {"product_id": product_id, "offers": ["cashback", "emi"]}

    @mcp.tool()
    def get_availability(product_id: str) -> dict[str, Any]:
        """Check product availability status."""
        return {"product_id": product_id, "availability": "In stock"}

    @mcp.tool()
    def get_reviews(product_id: str) -> dict[str, Any]:
        """Get product reviews and ratings."""
        return {"product_id": product_id, "rating": 4.7, "review_count": 1832}

    @mcp.tool()
    def get_delivery(product_id: str) -> dict[str, Any]:
        """Get delivery information for a product."""
        return {"product_id": product_id, "delivery": "2 days"}

    @mcp.tool()
    def get_provider_link(product_id: str) -> dict[str, Any]:
        """Get provider link for a product."""
        return {"product_id": product_id, "href": "https://example.com/product"}

    return mcp
