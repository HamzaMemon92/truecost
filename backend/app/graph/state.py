from __future__ import annotations

from typing import Any, TypedDict

from app.schemas.shopping import CanonicalProduct


class ShoppingGraphState(TypedDict):
    query: str
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
    provider_results: list[CanonicalProduct]
    recommendation: CanonicalProduct | None
    provider_warnings: list[str]
    payment_benefits: list[str]
    verification: list[str]
    reasoning: list[str]
    response: dict[str, Any]
