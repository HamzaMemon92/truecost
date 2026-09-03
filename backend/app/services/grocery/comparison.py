from __future__ import annotations

from typing import Any
from app.schemas.grocery import CanonicalProduct, RetailerOffer
from app.services.grocery.pricing import rank_offers, calculate_effective_price, calculate_unit_price

class ProductComparison:
    def __init__(self, canonical_product: CanonicalProduct, offers: list[RetailerOffer]):
        self.canonical_product = canonical_product
        self.offers = offers
        self.cheapest_offer: RetailerOffer | None = None
        self.fastest_offer: RetailerOffer | None = None
        self.best_value_offer: RetailerOffer | None = None
        self.analysis: dict[str, Any] = {}
        
    def compare(self):
        if not self.offers:
            return
            
        cheapest_rank = rank_offers(self.offers, "CHEAPEST")
        fastest_rank = rank_offers(self.offers, "FASTEST")
        best_value_rank = rank_offers(self.offers, "BEST_VALUE")
        
        if cheapest_rank and cheapest_rank[0][0].availability in ("IN_STOCK", "LOW_STOCK"):
            self.cheapest_offer = cheapest_rank[0][0]
            self.analysis["cheapest"] = cheapest_rank[0][2]
            
        if fastest_rank and fastest_rank[0][0].availability in ("IN_STOCK", "LOW_STOCK"):
            self.fastest_offer = fastest_rank[0][0]
            self.analysis["fastest"] = fastest_rank[0][2]
            
        if best_value_rank and best_value_rank[0][0].availability in ("IN_STOCK", "LOW_STOCK"):
            self.best_value_offer = best_value_rank[0][0]
            self.analysis["best_value"] = best_value_rank[0][2]

        # Add unit price and effective price to analysis
        for o in self.offers:
            res = calculate_effective_price(o)
            eff_price = res.effective_total
            unit_price_str = calculate_unit_price(
                eff_price, 
                self.canonical_product.normalized_quantity, 
                self.canonical_product.normalized_unit
            )
            self.analysis[o.provider] = {
                "unit_price": unit_price_str,
                "effective_price": eff_price,
                "breakdown": res.get_breakdown()
            }

    def to_dict(self) -> dict[str, Any]:
        return {
            "product": self.canonical_product.model_dump(),
            "offers": [o.model_dump() for o in self.offers],
            "winners": {
                "cheapest": self.cheapest_offer.provider if self.cheapest_offer else None,
                "fastest": self.fastest_offer.provider if self.fastest_offer else None,
                "best_value": self.best_value_offer.provider if self.best_value_offer else None,
            },
            "analysis": self.analysis
        }
