from __future__ import annotations

from typing import Any

from app.schemas.grocery import SearchIntent, CanonicalProduct

def match_products(intent: SearchIntent, catalog: list[CanonicalProduct]) -> list[tuple[CanonicalProduct, float, dict[str, Any]]]:
    """
    Match products in the catalog against the parsed intent.
    Returns a list of (product, score, debug_info) tuples, sorted by score descending.
    """
    results = []
    
    # Pre-process remaining terms from intent
    intent_terms = set(intent.remaining_terms.split()) if intent.remaining_terms else set()
    
    for product in catalog:
        # HARD CONSTRAINTS
        if intent.category and product.category != intent.category:
            continue
            
        # Hard constraint on max price if requested
        if intent.max_price is not None and product.base_price_estimate > intent.max_price:
            continue
            
        # Hard constraint on min price if requested
        if intent.min_price is not None and product.base_price_estimate < intent.min_price:
            continue
            
        # Initialize score
        score = 0.0
        debug = {"reasons": []}
        
        # 1. Brand matching (Strong signal)
        if intent.brand:
            if intent.brand.lower() == product.brand.lower():
                score += 50.0
                debug["reasons"].append("Exact brand match")
            else:
                # If brand is explicitly requested and doesn't match, heavily penalize or filter out
                continue
                
        # 2. Variant matching (Strong signal)
        if intent.variant and product.variant:
            if intent.variant == product.variant:
                score += 30.0
                debug["reasons"].append("Variant match")
            else:
                score -= 10.0
                
        # 3. Quantity matching
        if intent.normalized_quantity is not None and intent.normalized_unit is not None:
            if (product.normalized_quantity == intent.normalized_quantity and 
                product.normalized_unit == intent.normalized_unit):
                score += 40.0
                debug["reasons"].append("Exact quantity match")
            elif product.normalized_unit == intent.normalized_unit:
                # Same unit, different quantity. E.g. want 500ml, got 1L.
                diff = abs(product.normalized_quantity - intent.normalized_quantity)
                score -= (diff * 10)  # simple penalty for diff
                debug["reasons"].append(f"Quantity diff penalty: {-diff*10}")
        
        # 4. Lexical matching (Title/Tags vs remaining terms)
        title_lower = product.title.lower()
        matched_terms = 0
        for term in intent_terms:
            if term in title_lower:
                score += 10.0
                matched_terms += 1
                debug["reasons"].append(f"Term '{term}' in title")
            elif any(term in tag for tag in product.tags):
                score += 5.0
                matched_terms += 1
                debug["reasons"].append(f"Term '{term}' in tags")
                
        # Base relevance
        if matched_terms == len(intent_terms) and len(intent_terms) > 0:
            score += 20.0
            debug["reasons"].append("All remaining terms matched")
            
        results.append((product, score, debug))
        
    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results
