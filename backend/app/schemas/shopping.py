from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


ShoppingComplexity = Literal["simple", "moderate", "complex"]
ShoppingRoute = Literal["direct-tools", "shopping-agent", "deep-agent"]
ProviderStatus = Literal["live", "mock", "pending_authorization"]


class ShoppingRequest(BaseModel):
    query: str = Field(min_length=1)
    category: Literal["shopping"] = "shopping"
    session_id: str | None = None
    user_id: str | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)


class CanonicalProduct(BaseModel):
    canonical_product_id: str
    provider: str
    provider_product_id: str
    title: str
    brand: str
    category: str
    variant: str
    price: float
    currency: str = "INR"
    availability: str
    seller: str
    rating: float
    review_count: int
    delivery: str
    offers: list[str]
    return_policy: str
    warranty: str
    source_url: str
    affiliate_url: str
    source_type: ProviderStatus
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=30))
    confidence: float = 0.9


class ShoppingResponse(BaseModel):
    category: Literal["shopping"] = "shopping"
    query: str
    complexity: ShoppingComplexity
    route: ShoppingRoute
    recommendation: CanonicalProduct | None = None
    provider_results: list[CanonicalProduct] = Field(default_factory=list)
    verification: list[str] = Field(default_factory=list)
    payment_benefits: list[str] = Field(default_factory=list)
    provider_warnings: list[str] = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "decision-advisor-backend"
