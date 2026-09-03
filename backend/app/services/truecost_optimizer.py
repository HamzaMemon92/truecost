import math
from typing import List, Dict, Any, Set, Tuple
from app.schemas.product import TrueCostProduct

class TrueCostOptimizer:
    """
    The Elite TrueCost AI Basket Optimizer.
    Uses Dynamic Programming with Bitmasking to mathematically guarantee the absolute 
    cheapest cart split across all providers, factoring in multi-store delivery fees.
    """
    
    # Base delivery and platform fees per provider
    DELIVERY_FEES = {
        "Zepto": 15.0,
        "Blinkit": 20.0,
        "Swiggy": 25.0,
        "Swiggy Instamart": 25.0,
        "Bigbasket": 30.0,
        "BigBasket": 30.0,
        "Uber": 0.0,
        "Ola": 0.0,
        "Rapido": 0.0,
        "Amazon": 0.0,
        "Flipkart": 40.0,
        "Swiggy Food": 30.0,
        "Zomato": 25.0,
        "Tata 1mg": 0.0,
        "PharmEasy": 0.0,
        "MakeMyTrip": 0.0,
        "Goibibo": 0.0,
        "BankBazaar": 0.0,
    }

    @classmethod
    def get_fee(cls, provider: str) -> float:
        # Case insensitive fallback
        for k, v in cls.DELIVERY_FEES.items():
            if k.lower() == provider.lower():
                return v
        return 20.0  # Safe default fallback

    @classmethod
    def optimize_basket(cls, items: List[List[TrueCostProduct]]) -> Dict[str, Any]:
        """
        items is a list of groups. e.g., items[0] = all 'Amul Milk' products from various providers.
        """
        if not items:
            return {}

        N = len(items)
        
        # 1. Extract all unique providers and map to integer IDs
        all_providers: Set[str] = set()
        item_names = []
        
        for group in items:
            name = "Unknown Item"
            if group:
                name = group[0].name
            item_names.append(name)
            for product in group:
                for price_offer in product.prices:
                    all_providers.add(price_offer.provider)
                    
        providers_list = list(all_providers)
        P = len(providers_list)
        if P == 0:
            return {}
            
        provider_to_id = {p: i for i, p in enumerate(providers_list)}
        
        # 2. Build Cost Matrix: cost_matrix[i][p_id] = cheapest price for item i at provider p_id
        # Initialize with infinity
        cost_matrix = [[float('inf')] * P for _ in range(N)]
        
        for i, group in enumerate(items):
            for product in group:
                for price_offer in product.prices:
                    p_id = provider_to_id[price_offer.provider]
                    if price_offer.price < cost_matrix[i][p_id]:
                        cost_matrix[i][p_id] = price_offer.price
                        
        # 3. Dynamic Programming with Bitmask (State: item_index, mask_of_used_providers)
        # memo stores tuples: (min_cost, chosen_p_id)
        memo: Dict[Tuple[int, int], Tuple[float, int]] = {}

        def solve(item_idx: int, used_mask: int) -> Tuple[float, int]:
            if item_idx == N:
                # Base case: All items assigned. Add delivery fees for used providers.
                total_fee = 0.0
                for i, p_name in enumerate(providers_list):
                    if (used_mask & (1 << i)):
                        total_fee += cls.get_fee(p_name)
                return total_fee, -1
                
            state = (item_idx, used_mask)
            if state in memo:
                return memo[state]
                
            best_cost = float('inf')
            best_p_id = -1
            
            # Try assigning current item to any available provider
            for p_id in range(P):
                item_price = cost_matrix[item_idx][p_id]
                if item_price == float('inf'):
                    continue  # Provider doesn't have this item
                    
                new_mask = used_mask | (1 << p_id)
                future_cost, _ = solve(item_idx + 1, new_mask)
                total_path_cost = item_price + future_cost
                
                if total_path_cost < best_cost:
                    best_cost = total_path_cost
                    best_p_id = p_id
                    
            memo[state] = (best_cost, best_p_id)
            return memo[state]

        # 4. Execute DP and reconstruct the optimal path
        min_total_cost, first_p_id = solve(0, 0)
        
        if min_total_cost == float('inf'):
            return {"error": "Impossible to fulfill entire basket with current providers."}
            
        optimal_split = {}
        curr_mask = 0
        total_items_cost = 0.0
        
        for i in range(N):
            _, chosen_p_id = solve(i, curr_mask)
            provider_name = providers_list[chosen_p_id]
            price = cost_matrix[i][chosen_p_id]
            
            if provider_name not in optimal_split:
                optimal_split[provider_name] = []
            
            optimal_split[provider_name].append({
                "product_name": item_names[i],
                "price": price
            })
            total_items_cost += price
            curr_mask |= (1 << chosen_p_id)
            
        total_delivery_fee = sum(cls.get_fee(p) for i, p in enumerate(providers_list) if (curr_mask & (1 << i)))

        # 5. Calculate "Best Single Retailer" Baseline for comparison
        best_single_cost = float('inf')
        best_single_provider = None
        for p_id, p_name in enumerate(providers_list):
            can_fulfill = True
            cost = 0.0
            for i in range(N):
                if cost_matrix[i][p_id] == float('inf'):
                    can_fulfill = False
                    break
                cost += cost_matrix[i][p_id]
            if can_fulfill:
                cost += cls.get_fee(p_name)
                if cost < best_single_cost:
                    best_single_cost = cost
                    best_single_provider = p_name

        # 6. Generate Elite Recommendations
        split_count = len(optimal_split)
        if split_count == 1:
            provider = list(optimal_split.keys())[0]
            rec = f"Buy everything on {provider}. It is the mathematically cheapest option including fees."
        else:
            savings = round(best_single_cost - min_total_cost, 2) if best_single_cost != float('inf') else 0
            if savings > 0:
                rec = f"Split your cart across {split_count} apps. Even with multiple delivery fees, you save ₹{savings} compared to buying all from {best_single_provider}!"
            else:
                rec = f"Split your cart across {split_count} apps to get all items."

        return {
            "optimal_split": optimal_split,
            "financials": {
                "items_total": round(total_items_cost, 2),
                "delivery_fees": round(total_delivery_fee, 2),
                "grand_total": round(min_total_cost, 2),
                "single_store_alternative": round(best_single_cost, 2) if best_single_cost != float('inf') else None
            },
            "recommendation": rec
        }
