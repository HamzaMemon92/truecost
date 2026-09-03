from __future__ import annotations

from typing import Any
from app.schemas.grocery import RetailerOffer, RankingMode, AvailabilityStatus


class EffectivePriceResult:
    def __init__(self, offer: RetailerOffer):
        self.offer = offer
        
        self.item_price = round(offer.price, 2)
        self.mrp = round(offer.mrp or offer.price, 2)
        self.delivery_fee = round(offer.delivery_fee, 2)
        self.platform_fee = round(offer.platform_fee, 2)
        self.discount = round(offer.discount, 2)
        self.coupon_discount = round(offer.coupon_discount, 2)
        
        capped_item_discount = min(self.item_price, self.discount)
        self.effective_total = round((self.item_price - capped_item_discount) + self.delivery_fee + self.platform_fee - self.coupon_discount, 2)
        
        # Guard against negative totals
        if self.effective_total < 0:
            self.effective_total = 0.0
            
    def get_breakdown(self) -> dict[str, float]:
        return {
            "item_price": self.item_price,
            "mrp": self.mrp,
            "delivery_fee": self.delivery_fee,
            "platform_fee": self.platform_fee,
            "discount": self.discount,
            "coupon_discount": self.coupon_discount,
            "effective_total": self.effective_total
        }


def calculate_effective_price(offer: RetailerOffer) -> EffectivePriceResult:
    """Reusable service to compute effective cost and breakdown of an offer."""
    return EffectivePriceResult(offer)


def calculate_unit_price(effective_price: float, quantity_value: float, quantity_unit: str) -> str:
    """Calculate normalized unit pricing. E.g. 60/L, 140/kg"""
    if not quantity_value or quantity_value <= 0:
        return "N/A"
        
    unit_price = effective_price / quantity_value
    
    # Format cleanly
    if quantity_unit in ("L", "kg", "pcs"):
        return f"₹{unit_price:.2f}/{quantity_unit}"
    else:
        return f"₹{unit_price:.2f}/{quantity_unit}"


def rank_offers(offers: list[RetailerOffer], mode: RankingMode) -> list[tuple[RetailerOffer, EffectivePriceResult, dict[str, Any]]]:
    """Rank offers based on mode. Returns sorted list of (offer, price_result, explanation_dict)."""
    
    scored_offers = []
    
    for offer in offers:
        price_result = calculate_effective_price(offer)
        
        # Hard constraints: reject invalid offers entirely or deprioritize them deeply
        if offer.availability not in ("IN_STOCK", "LOW_STOCK"):
            # Mark score as infinite (worst) to drop them to bottom
            score = float('inf')
            explanation = {"reason": "Unavailable", "status": offer.availability}
        else:
            # Score depends on mode
            if mode == "CHEAPEST":
                score = price_result.effective_total
                explanation = {"reason": f"Effective cost: ₹{score:.2f}"}
            elif mode == "FASTEST":
                eta = offer.delivery_minutes or 999
                score = eta
                explanation = {"reason": f"{eta} min ETA"}
            else: # BEST_VALUE
                # A balanced formula: effective total + penalty for slow delivery
                # E.g. Every minute of delivery is worth ₹1 penalty.
                eta = offer.delivery_minutes or 60
                score = price_result.effective_total + (eta * 1.0)
                explanation = {"reason": f"Best balance of ₹{price_result.effective_total:.2f} + {eta} mins"}
                
        # Additional formatting for explanation
        explanation["breakdown"] = price_result.get_breakdown()
        
        scored_offers.append((offer, price_result, score, explanation))
        
    # Sort by score ascending
    scored_offers.sort(key=lambda x: x[2])
    
    # Return (offer, result, explanation) mapping
    return [(o[0], o[1], o[3]) for o in scored_offers]
