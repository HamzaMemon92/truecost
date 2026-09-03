from __future__ import annotations

from typing import Any, TypedDict

from app.schemas.grocery import CanonicalBasket


class GroceryGraphState(TypedDict):
    items: list[str]
    category: str
    session_id: str | None
    user_id: str | None
    preferences: dict[str, Any]
    force_deep_agent: bool
    context: dict[str, Any]
    complexity: str
    route: str
    agent_type: str | None
    mcp_tools_used: list[str]
    mcp_results: list[dict[str, Any]]
    evidence: list[str]
    
    # Grocery-specific state
    objective: str  # e.g., cheapest, fastest, balanced, personalized
    product_comparisons: list[dict[str, Any]]
    basket_results: list[CanonicalBasket]
    recommended_basket: CanonicalBasket | None
    alternative_baskets: list[CanonicalBasket]
    substitutions: list[dict[str, Any]]
    observability: list[dict[str, Any]]
    
    verification: list[str]
    reasoning: list[str]
    response: dict[str, Any]
