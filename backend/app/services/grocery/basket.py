import itertools
from collections import defaultdict
from typing import Any

from app.schemas.grocery import (
    BasketComparisonResult,
    BasketEvaluationRequest,
    CanonicalGroceryItem,
    FulfillmentGroup,
    TrueCostBasketItem,
)


class BasketOptimizerService:
    @staticmethod
    def evaluate(
        request: BasketEvaluationRequest, available_items: list[CanonicalGroceryItem]
    ) -> list[BasketComparisonResult]:
        """
        Evaluate a TrueCost basket against available retailer offers.
        Generates and ranks full and split basket options.
        """
        # 1. Group available items by provider and by canonical_product_id
        provider_catalog: dict[str, dict[str, CanonicalGroceryItem]] = defaultdict(dict)
        for item in available_items:
            # Only consider IN_STOCK items for fulfilling baskets
            if item.availability == "IN_STOCK":
                provider_catalog[item.provider][item.canonical_product_id] = item

        basket_items = {item.canonical_product_id: item.quantity for item in request.items}
        requested_ids = set(basket_items.keys())
        providers = list(provider_catalog.keys())
        
        valid_baskets: list[BasketComparisonResult] = []

        # 2. Evaluate Single-Retailer options
        for provider in providers:
            catalog = provider_catalog[provider]
            missing = requested_ids - set(catalog.keys())
            
            fg = BasketOptimizerService._build_fulfillment_group(
                provider, catalog, basket_items, requested_ids
            )
            
            result = BasketComparisonResult(
                mode=request.mode,
                total=fg.final_total,
                savings=0.0,
                retailer_count=1,
                deliveries=1,
                fulfillment_groups=[fg],
                unavailable_items=list(missing),
                explanations=[]
            )
            valid_baskets.append(result)

        # 3. Evaluate 2-Retailer Split options (only if there are 2+ providers)
        if len(providers) >= 2:
            for p1, p2 in itertools.combinations(providers, 2):
                cat1 = provider_catalog[p1]
                cat2 = provider_catalog[p2]
                
                # Split strategy: For each item, pick the cheapest provider
                split_assignment_1 = set()
                split_assignment_2 = set()
                missing = []
                
                for pid in requested_ids:
                    item1 = cat1.get(pid)
                    item2 = cat2.get(pid)
                    
                    if item1 and item2:
                        if item1.price - item1.discount <= item2.price - item2.discount:
                            split_assignment_1.add(pid)
                        else:
                            split_assignment_2.add(pid)
                    elif item1:
                        split_assignment_1.add(pid)
                    elif item2:
                        split_assignment_2.add(pid)
                    else:
                        missing.append(pid)

                if split_assignment_1 and split_assignment_2:
                    fg1 = BasketOptimizerService._build_fulfillment_group(
                        p1, cat1, basket_items, split_assignment_1
                    )
                    fg2 = BasketOptimizerService._build_fulfillment_group(
                        p2, cat2, basket_items, split_assignment_2
                    )
                    
                    result = BasketComparisonResult(
                        mode=request.mode,
                        total=fg1.final_total + fg2.final_total,
                        savings=0.0,
                        retailer_count=2,
                        deliveries=2,
                        fulfillment_groups=[fg1, fg2],
                        unavailable_items=missing,
                        explanations=["Split basket across 2 retailers"]
                    )
                    valid_baskets.append(result)

        # 4. Rank and Filter
        ranked = BasketOptimizerService._rank_baskets(valid_baskets, request.mode)
        
        # 5. Compute Savings vs the worst/standard single retailer option
        if ranked:
            best = ranked[0]
            standard_baselines = [b for b in valid_baskets if b.retailer_count == 1 and not b.unavailable_items]
            if standard_baselines:
                worst_baseline = max(standard_baselines, key=lambda x: x.total)
                for b in ranked:
                    if b.total < worst_baseline.total:
                        b.savings = worst_baseline.total - b.total
                        if b.retailer_count > 1:
                            b.explanations.append(f"Save ₹{b.savings:.0f} vs buying everything from {worst_baseline.fulfillment_groups[0].provider}")

        return ranked

    @staticmethod
    def _build_fulfillment_group(
        provider: str,
        catalog: dict[str, CanonicalGroceryItem],
        basket_items: dict[str, int],
        assigned_ids: set[str],
    ) -> FulfillmentGroup:
        items = []
        subtotal = 0.0
        missing = []
        
        eta = "30 mins"
        if "zepto" in provider.lower() or "blinkit" in provider.lower():
            eta = "10 mins"

        for pid in assigned_ids:
            if pid in catalog:
                item = catalog[pid]
                quantity = basket_items[pid]
                
                # Prevent negative effective price
                unit_effective_price = max(0.0, item.price - item.discount)
                subtotal += unit_effective_price * quantity
                
                # Update item quantity manually before adding to fg
                item_copy = item.model_copy()
                item_copy.quantity_value = quantity # Coopt quantity_value to mean cart count
                items.append(item_copy)
            else:
                missing.append(pid)

        delivery_fee = 0.0
        if items:
            if subtotal < 200:
                delivery_fee = 49.0
            elif subtotal < 500:
                delivery_fee = 29.0
                
        platform_fee = 5.0 if items else 0.0

        subtotal = round(subtotal, 2)
        final_total = round(subtotal + delivery_fee + platform_fee, 2)

        return FulfillmentGroup(
            provider=provider,
            items=items,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            platform_fee=platform_fee,
            final_total=final_total,
            estimated_delivery=eta,
            missing_items=missing,
            deep_link_type="CART" if not missing else "UNAVAILABLE",
            deep_link_url=f"https://mock-{provider.lower()}.com/cart" if not missing else None
        )

    @staticmethod
    def _rank_baskets(baskets: list[BasketComparisonResult], mode: str) -> list[BasketComparisonResult]:
        def extract_mins(eta: str | None) -> int:
            if not eta: return 30
            import re
            m = re.search(r'\d+', eta)
            return int(m.group()) if m else 30

        def score(b: BasketComparisonResult) -> float:
            penalty = len(b.unavailable_items) * 10000.0
            cost = b.total
            mins = max([extract_mins(fg.estimated_delivery) for fg in b.fulfillment_groups], default=30)
            deliveries = b.deliveries
            
            if mode == "SINGLE_RETAILER":
                multi_penalty = (deliveries - 1) * 5000.0
                return cost + multi_penalty + penalty
            elif mode == "FASTEST":
                return (mins * 50.0) + cost + (deliveries * 20.0) + penalty
            elif mode == "BEST_VALUE":
                return cost + (mins * 2.0) + (deliveries * 15.0) + penalty
            else: # CHEAPEST
                return cost + (deliveries * 20.0) + penalty

        return sorted(baskets, key=score)
