import re
from typing import Any
from collections import defaultdict

from app.schemas.grocery import CanonicalGroceryItem, CanonicalBasket

class BasketBuilder:
    @staticmethod
    def build(items: list[CanonicalGroceryItem]) -> list[CanonicalBasket]:
        """Group flat CanonicalGroceryItems into primitive CanonicalBaskets by provider."""
        provider_map = defaultdict(list)
        for item in items:
            provider_map[item.provider].append(item)
            
        baskets = []
        for provider, provider_items in provider_map.items():
            basket = CanonicalBasket(
                provider=provider,
                items=provider_items,
                subtotal=0.0,
                delivery_fee=0.0,
                platform_fee=0.0,
                final_total=0.0,
                meets_minimum_order=True,
                estimated_delivery=None,
                missing_items=[]
            )
            baskets.append(basket)
        return baskets


class CostCalculator:
    @staticmethod
    def calculate_all(baskets: list[CanonicalBasket]) -> list[CanonicalBasket]:
        return [CostCalculator.calculate(b) for b in baskets]

    @staticmethod
    def calculate(basket: CanonicalBasket) -> CanonicalBasket:
        subtotal = sum(item.price for item in basket.items)
        basket.subtotal = subtotal
        
        # Simple simulated delivery math:
        # If order < 200, high delivery fee. If > 500, free delivery. Else standard.
        if subtotal < 200:
            base_delivery = 49.0
        elif subtotal > 500:
            base_delivery = 0.0
        else:
            base_delivery = 29.0
            
        # Add provider-specific mock delivery fees based on name (for mock testing)
        provider_name = basket.provider.lower()
        if "fast" in provider_name:
            base_delivery += 20.0
            basket.estimated_delivery = "10 minutes"
        elif "cheap" in provider_name:
            base_delivery = 15.0 if subtotal < 200 else 0.0
            basket.estimated_delivery = "30 minutes"
        else:
            basket.estimated_delivery = "15 minutes"
            
        basket.delivery_fee = base_delivery
        basket.platform_fee = 5.0
        
        basket.final_total = basket.subtotal + basket.delivery_fee + basket.platform_fee
        
        # Fake min order logic
        min_order = 100.0 if "fast" in provider_name else 50.0
        basket.meets_minimum_order = basket.subtotal >= min_order
        
        return basket


class ConstraintEngine:
    @staticmethod
    def evaluate_all(baskets: list[CanonicalBasket], query_items: list[str]) -> list[CanonicalBasket]:
        return [ConstraintEngine.evaluate(b, query_items) for b in baskets]

    @staticmethod
    def evaluate(basket: CanonicalBasket, query_items: list[str]) -> CanonicalBasket:
        # Find which requested items are missing from the basket
        # Very simple heuristic: check if word from query is in any title
        missing = []
        
        # Extract keywords (ignoring numbers like "1", "dozen", etc for simplicity)
        def get_keywords(text):
            words = text.lower().split()
            return [w for w in words if w.isalpha() and w not in ('a', 'an', 'the', 'dozen', 'kg', 'g', 'l')]
            
        for query in query_items:
            q_words = get_keywords(query)
            if not q_words:
                continue
                
            found = False
            for item in basket.items:
                title_lower = item.title.lower()
                # If any significant word matches, assume it's found
                if any(w in title_lower for w in q_words):
                    found = True
                    break
                    
            if not found:
                missing.append(query)
                
        basket.missing_items = missing
        return basket


class BasketOptimizer:
    @staticmethod
    def optimize(baskets: list[CanonicalBasket], objective: str) -> list[CanonicalBasket]:
        """Rank baskets based on objective: cheapest, fastest, or balanced."""
        if not baskets:
            return []
            
        def extract_minutes(delivery_str: str | None) -> int:
            if not delivery_str:
                return 30
            match = re.search(r'\d+', delivery_str)
            return int(match.group()) if match else 30

        def score(b: CanonicalBasket) -> float:
            missing_penalty = len(b.missing_items) * 1000.0  # Heavy penalty for missing items
            min_order_penalty = 500.0 if not b.meets_minimum_order else 0.0
            
            delivery_mins = extract_minutes(b.estimated_delivery)
            cost = b.final_total
            
            if objective == "cheapest":
                return cost + missing_penalty + min_order_penalty
            elif objective == "fastest":
                # 1 minute faster = 30 points. This ensures speed dominates over
                # small price differences between providers.
                return (delivery_mins * 30.0) + cost + missing_penalty + min_order_penalty
            else:
                # balanced
                return cost + (delivery_mins * 5.0) + missing_penalty + min_order_penalty

        ranked = sorted(baskets, key=score)
        return ranked
