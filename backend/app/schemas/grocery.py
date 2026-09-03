from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

GroceryComplexity = Literal["simple", "moderate", "complex"]
GroceryRoute = Literal["direct-basket", "grocery-agent", "deep-agent"]
GrocerySourceType = Literal["live", "mock", "cached", "estimated"]
ProviderStatus = Literal["active", "unavailable", "pending_authorization"]

# --- Location / availability / pricing / ranking (retailer-offer layer) ---
AvailabilityStatus = Literal["IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK", "UNAVAILABLE_IN_AREA", "UNKNOWN"]
PriceConfidence = Literal["known", "estimated", "unknown"]
RankingMode = Literal["CHEAPEST", "FASTEST", "BEST_VALUE", "SINGLE_RETAILER"]
DeepLinkType = Literal["PRODUCT_PAGE", "CART", "SEARCH_FALLBACK", "UNAVAILABLE"]


class Location(BaseModel):
    postal_code: str | None = None
    city: str | None = None
    locality: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_id: str | None = None


DataFreshnessStatus = Literal["FRESH", "STALE", "UNKNOWN"]

class ProviderObservability(BaseModel):
    provider_name: str
    status: Literal["success", "timeout", "error"]
    latency_ms: int
    error_class: str | None = None
    item_count: int = 0


class SearchIntent(BaseModel):
    raw_query: str
    category: str | None = None
    brand: str | None = None
    variant: str | None = None
    quantity_value: float | None = None
    quantity_unit: str | None = None
    normalized_quantity: float | None = None
    normalized_unit: str | None = None
    pack_count: int | None = None
    min_price: float | None = None
    max_price: float | None = None
    remaining_terms: str = ""
    location: Location | None = None


class RetailerOffer(BaseModel):
    provider: str
    provider_sku: str
    canonical_product_id: str | None = None
    store_id: str | None = None
    location: Location | None = None
    
    price: float
    mrp: float | None = None
    discount: float = 0.0
    coupon_discount: float = 0.0
    delivery_fee: float = 0.0
    platform_fee: float = 0.0
    min_order_value: float = 0.0
    
    availability: AvailabilityStatus = "UNKNOWN"
    delivery_minutes: int | None = None
    offers: list[str] = Field(default_factory=list)
    source_url: str | None = None
    affiliate_url: str | None = None
    source_type: GrocerySourceType = "live"
    
    # Image fields
    retailer_image_url: str | None = None
    image_verified: bool = False
    image_source: str | None = None
    
    # Destination handoff fields
    deep_link_type: DeepLinkType = "UNAVAILABLE"
    deep_link_url: str | None = None
    
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 0.9
    
    # Freshness
    freshness: DataFreshnessStatus = "UNKNOWN"
    price_checked_at: datetime | None = None
    availability_checked_at: datetime | None = None
    image_checked_at: datetime | None = None


ImageConfidence = Literal["TRUSTED", "KNOWN_SOURCE", "FALLBACK", "UNVERIFIED"]

class CanonicalProduct(BaseModel):
    """The canonical internal representation of a grocery product."""
    canonical_product_id: str
    title: str
    brand: str
    category: str
    variant: str | None = None
    normalized_quantity: float
    normalized_unit: str
    pack_count: int = 1
    base_price_estimate: float
    image_url: str | None = None
    image_source: str | None = None
    image_confidence: ImageConfidence = "UNVERIFIED"
    image_variant_key: str | None = None
    tags: list[str] = Field(default_factory=list)


class GroceryRequest(BaseModel):
    items: list[str] = Field(min_length=1)
    category: Literal["grocery"] = "grocery"
    session_id: str | None = None
    user_id: str | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)
    # Expected preferences: objective (e.g. cheapest, fastest, balanced), max_delivery_minutes, etc.


class CanonicalGroceryItem(BaseModel):
    """A single normalized product from a grocery provider."""
    canonical_product_id: str
    provider: str
    provider_sku: str
    title: str
    brand: str
    category: str
    quantity_value: float
    quantity_unit: str
    
    price: float
    mrp: float | None = None
    discount: float = 0.0
    coupon_discount: float | None = None
    delivery_fee: float | None = None
    platform_fee: float | None = None
    currency: str = "INR"
    
    availability: str
    delivery_minutes: int | None = None
    min_order_value: float | None = None
    er_decision: str | None = None
    offers: list[str] = Field(default_factory=list)
    source_url: str
    affiliate_url: str
    source_type: GrocerySourceType
    provider_status: ProviderStatus = "active"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=30))
    confidence: float = 0.9
    
    # Image fields
    retailer_image_url: str | None = None
    image_verified: bool = False
    image_source: str | None = None
    
    # Destination handoff fields
    deep_link_type: DeepLinkType = "UNAVAILABLE"
    deep_link_url: str | None = None
    
    # Freshness
    freshness: DataFreshnessStatus = "UNKNOWN"
    price_checked_at: datetime | None = None
    availability_checked_at: datetime | None = None
    image_checked_at: datetime | None = None


class CanonicalBasket(BaseModel):
    """A complete normalized grocery basket from one provider."""
    provider: str
    items: list[CanonicalGroceryItem]
    subtotal: float
    delivery_fee: float
    platform_fee: float = 0.0
    discount: float = 0.0
    coupon_discount: float = 0.0
    membership_discount: float = 0.0
    final_total: float
    meets_minimum_order: bool
    estimated_delivery: str | None
    missing_items: list[str] = Field(default_factory=list)


class TrueCostBasketItem(BaseModel):
    # canonical_product_id is optional — mobile app may send only `name`.
    # The basket endpoint resolves the canonical ID from the observation catalog.
    canonical_product_id: str | None = None
    name: str | None = None  # human-readable name, used when canonical_product_id is absent
    quantity: int = 1

class BasketEvaluationRequest(BaseModel):
    items: list[TrueCostBasketItem]
    location: Location | None = None
    mode: RankingMode = "CHEAPEST"

class FulfillmentGroup(BaseModel):
    provider: str
    items: list[CanonicalGroceryItem]
    subtotal: float
    delivery_fee: float
    platform_fee: float
    discount: float = 0.0
    coupon_discount: float = 0.0
    final_total: float
    estimated_delivery: str | None
    missing_items: list[str] = Field(default_factory=list)
    deep_link_type: DeepLinkType = "UNAVAILABLE"
    deep_link_url: str | None = None

class BasketComparisonResult(BaseModel):
    mode: RankingMode
    total: float
    savings: float = 0.0
    retailer_count: int
    deliveries: int
    fulfillment_groups: list[FulfillmentGroup]
    unavailable_items: list[str] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)

class GroceryResponse(BaseModel):
    category: Literal["grocery"] = "grocery"
    items_requested: list[str]
    complexity: GroceryComplexity
    route: GroceryRoute
    
    # New Field for Product Search/Comparison Experience
    product_comparisons: list[dict[str, Any]] = Field(default_factory=list)
    
    recommended_basket: CanonicalBasket | None = None
    alternative_baskets: list[CanonicalBasket] = Field(default_factory=list)
    substitutions: list[dict[str, Any]] = Field(default_factory=list)
    verification: list[str] = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)
    observability: list[ProviderObservability] = Field(default_factory=list)
