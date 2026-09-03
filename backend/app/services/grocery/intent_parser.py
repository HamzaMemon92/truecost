from __future__ import annotations

import re

from app.schemas.grocery import SearchIntent
from app.services.grocery.normalization import normalize_quantity, normalize_unit

# Common brands to detect
KNOWN_BRANDS = {
    "amul", "mother dairy", "nandini", "milky mist", "heritage",
    "britannia", "modern", "harvest gold", "english oven",
    "fortune", "saffola", "dhara", "gemini",
    "aashirvaad", "pillsbury", "india gate", "kohinoor", "daawat",
    "tata", "red label", "taj mahal", "nescafe", "bru"
}

# Categories
KNOWN_CATEGORIES = {
    "milk": "dairy",
    "egg": "eggs",
    "eggs": "eggs",
    "bread": "bakery",
    "butter": "dairy",
    "paneer": "dairy",
    "curd": "dairy",
    "rice": "staples",
    "atta": "staples",
    "flour": "staples",
    "dal": "staples",
    "oil": "staples",
    "tea": "beverages",
    "coffee": "beverages",
}

# Quantity matching regex
# Matches: "500 ml", "1 litre", "1.5 kg", "1L", "250g", "6 pcs", "12 pieces"
QTY_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*(ml|l|litre|liter|litres|liters|kg|kilo|kilogram|g|gm|grams|pc|pcs|piece|pieces|pack)', re.IGNORECASE)

# Price matching regex
# Matches: "under 60", "below 50", "max 100", "< 20"
PRICE_PATTERN = re.compile(r'(?:under|below|max|<)\s*(?:rs|inr|₹)?\s*(\d+(?:\.\d+)?)', re.IGNORECASE)


def parse_grocery_intent(query: str) -> SearchIntent:
    """Parse raw query into a structured SearchIntent deterministically."""
    q_lower = query.lower()
    
    intent = SearchIntent(raw_query=query)
    
    # 1. Price Constraint
    price_match = PRICE_PATTERN.search(q_lower)
    if price_match:
        intent.max_price = float(price_match.group(1))
        # Remove the price part so it doesn't pollute remaining terms
        q_lower = q_lower[:price_match.start()] + q_lower[price_match.end():]
        
    # 2. Quantity
    qty_match = QTY_PATTERN.search(q_lower)
    if qty_match:
        val = float(qty_match.group(1))
        unit = qty_match.group(2)
        
        # If the unit is pieces/pack, it might be pack_count
        norm_u = normalize_unit(unit)
        if norm_u == "pcs":
            intent.pack_count = int(val)
        else:
            intent.quantity_value = val
            intent.quantity_unit = norm_u
            
            # Compute normalized quantity
            n_val, n_unit = normalize_quantity(val, norm_u)
            intent.normalized_quantity = n_val
            intent.normalized_unit = n_unit
            
        # Remove from query
        q_lower = q_lower[:qty_match.start()] + q_lower[qty_match.end():]
    else:
        # Check for standalone integer before known packable categories (like "6 eggs")
        # Just grab any standalone number as pack_count
        num_match = re.search(r'\b(\d+)\b', q_lower)
        if num_match:
            val = int(num_match.group(1))
            intent.pack_count = val
            q_lower = q_lower[:num_match.start()] + q_lower[num_match.end():]
        
    # 3. Brand
    words = q_lower.split()
    for brand in KNOWN_BRANDS:
        if brand in q_lower:
            # Simple check to avoid substring matches like "tata" in "potato"
            # It's better to check if brand words are in the word list
            b_words = brand.split()
            if all(bw in words for bw in b_words):
                intent.brand = brand
                # remove brand words
                words = [w for w in words if w not in b_words]
                q_lower = " ".join(words)
                break
                
    # 4. Category
    for word in words:
        if word in KNOWN_CATEGORIES:
            intent.category = KNOWN_CATEGORIES[word]
            intent.variant = word # the specific type of category product, e.g. "milk"
            # we don't necessarily remove the category word, but we can to isolate remaining terms
            words.remove(word)
            break
            
    # 5. Remaining terms (variant details like "taaza", "full cream", "toned")
    remaining = " ".join(words).strip()
    if remaining:
        intent.remaining_terms = remaining
        
    return intent
