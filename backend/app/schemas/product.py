from pydantic import BaseModel, ConfigDict, model_validator
"""
TrueCost Universal Product Schema
Uses Pydantic v2 camelCase alias generator so FastAPI serializes
JSON with camelCase keys matching the mobile TypeScript interfaces.

Backend internal field: is_best, original_price, delivery_time, weight_volume
JSON output:            isBest,    originalPrice,  deliveryTime,  weightVolume
"""


from pydantic.alias_generators import to_camel
from typing import List, Optional


class _CamelModel(BaseModel):
    """Base that outputs camelCase JSON — all schemas inherit from this."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,   # also accept snake_case on input
        from_attributes=True,
    )


class ProviderPrice(_CamelModel):
    provider: str                        # "Zepto", "Blinkit", "Amazon"
    price: float                         # Current selling price
    original_price: Optional[float] = None  # MRP (if discounted)
    delivery_time: str = ""              # "10 mins", "Tomorrow"
    is_best: bool = False                # Cheapest across providers
    deep_link: Optional[str] = None     # "zepto://product/123" or web URL
    product_url: Optional[str] = None
    app_deep_link: Optional[str] = None
    fallback_search_url: Optional[str] = None
    handoff_confidence: Optional[str] = None
    in_stock: Optional[bool] = None
    serviceable: Optional[bool] = None
    observed_at: Optional[str] = None


class TrueCostProduct(_CamelModel):
    id: str                              # Canonical TrueCost ID
    name: str
    brand: str
    weight_volume: str = ""             # "500ml", "1kg", "1 strip"
    image_url: str = ""
    category: str                        # "Grocery", "Pharmacy", etc.
    prices: List[ProviderPrice] = []
    
    # Entity Resolution / Strong Identifiers
    gtin: Optional[str] = None
    ean: Optional[str] = None
    upc: Optional[str] = None
    isbn: Optional[str] = None
    mpn: Optional[str] = None
    provider_sku: Optional[str] = None
    
    # Controlled fallback for future attributes
    unknown_attributes: dict = {}
    
    @model_validator(mode='before')
    @classmethod
    def extract_unknown(cls, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        known_fields = {"id", "name", "brand", "weight_volume", "weightVolume", "image_url", "imageUrl", "category", "prices", "gtin", "ean", "upc", "isbn", "mpn", "provider_sku", "unknown_attributes"}
        unknown = data.get("unknown_attributes", {})
        for k, v in list(data.items()):
            if k not in known_fields and k != "isBest": # isBest is handled by CamelModel sometimes
                unknown[k] = v
        data["unknown_attributes"] = unknown
        return data


