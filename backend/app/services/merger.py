"""
TrueCost Product Merger Service
Groups products from multiple providers into merged canonical products.
Uses difflib.SequenceMatcher for fuzzy name similarity.
Uses model_copy(update=...) to stay safe with Pydantic v2 immutability.
"""

import re
from difflib import SequenceMatcher
from typing import List, Dict
from app.schemas.product import TrueCostProduct, ProviderPrice

_SPEC_UNITS = {
    "ml", "l", "kg", "g", "gm", "ltr", "litre", "litres", "h", "hr", "hrs", "hour", "hours",
    "mah", "w", "mm", "cm", "inch", "inches", "hz", "khz", "pack", "pcs", "piece", "pieces",
}
_SPEC_WORDS = {"battery", "driver", "drivers", "capacity", "playtime", "backup", "screen", "display"}
_SPEC_NUMERIC_RE = re.compile(r"^\d+(?:ml|l|kg|g|gm|ltr|litre|litres|h|hr|hrs|hour|hours|mah|w|mm|cm|inch|inches|hz|khz)$")
_STRICT_VARIANT_TOKENS = {
    "lite", "low", "sodium", "gold", "full", "cream", "atta", "magic", "xt", "plus", "pro", "max",
    "mini", "ultra", "air", "anc", "sugar", "free", "butter", "cashew", "almond", "chocolate",
    "classic", "original", "masala", "tomato", "cheese", "onion", "salted", "unsalted", "diet",
    "zero", "dark", "milk", "white", "vanilla", "strawberry", "neo", "ace", "millennia",
    "cashback", "platinum", "signature", "infinite", "business", "teams", "organization",
}


def _normalize(name: str) -> str:
    """Strip weight/volume/marketing noise and lowercase for fair comparison."""
    name = name.lower().strip()
    # Strip weights, volumes, packs
    name = re.sub(r'\d+\s*(ml|l|kg|g|gm|ltr|litre|pack|pcs|piece|units?)\b', '', name)
    # Strip common electronics/marketing noise
    noise_words = [
        r'\bwireless\b', r'\bbluetooth\b', r'\bheadphones?\b', r'\bearphones?\b', 
        r'\bearbuds?\b', r'\btws\b', r'\bwith\b', r'\bmic\b', r'\bnewly launched\b',
        r'\bto\b', r'\bfrom\b', r'\bnear\b', r'\bat\b',
        r'\bnew\b', r'\b202[0-9]\b', r'\bhours?\b', r'\bplaytime\b', r'\benc\b',
        r'\bquad\b', r'\bdrivers?\b', r'\bport\b', r'\bv5\.\d+\b', r'\bover-ear\b',
        r'\bon-ear\b', r'\bin-ear\b'
    ]
    for noise in noise_words:
        name = re.sub(noise, '', name)
        
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def _identity_numbers(name: str) -> set[str]:
    """Extract numeric model/variant signals that must not be merged away."""
    tokens = re.findall(r'\b\w+\b', name.lower())
    result: set[str] = set()
    for index, token in enumerate(tokens):
        if not any(char.isdigit() for char in token):
            continue
        previous_token = tokens[index - 1] if index > 0 else ""
        next_token = tokens[index + 1] if index + 1 < len(tokens) else ""
        is_spec = bool(_SPEC_NUMERIC_RE.match(token)) or next_token in _SPEC_UNITS or previous_token in _SPEC_WORDS
        if not is_spec:
            result.add(token)
    return result


def _variant_tokens(name: str) -> set[str]:
    """Extract flavor/model/variant terms that should block unsafe merges."""
    tokens = set(re.findall(r'\b\w+\b', name.lower()))
    return tokens & _STRICT_VARIANT_TOKENS


def _similarity(a: str, b: str) -> float:
    """Returns 0.0–1.0 similarity between two product name strings."""
    a_numbers = _identity_numbers(a)
    b_numbers = _identity_numbers(b)
    if a_numbers != b_numbers:
        return 0.0
    a_variants = _variant_tokens(a)
    b_variants = _variant_tokens(b)
    if a_variants != b_variants:
        return 0.0
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def merge_products(products: List[TrueCostProduct], threshold: float = 0.75) -> List[TrueCostProduct]:
    """
    Takes a flat list of TrueCostProduct (one per provider per item)
    and merges them into canonical products with multiple ProviderPrices.
    Uses model_copy() for Pydantic v2 safety — no direct mutation.
    """
    merged: List[TrueCostProduct] = []

    for product in products:
        matched = False
        for i, canonical in enumerate(merged):
            category = (product.category or "").casefold()
            canonical_category = (canonical.category or "").casefold()
            if category == canonical_category == "finance" and product.brand.casefold().strip() != canonical.brand.casefold().strip():
                continue
            if _similarity(product.name, canonical.name) >= threshold:
                # Merge prices into the canonical card
                existing_providers = {p.provider for p in canonical.prices}
                new_prices = [p for p in product.prices if p.provider not in existing_providers]
                if new_prices:
                    # Use model_copy to safely update the immutable prices list
                    merged[i] = canonical.model_copy(
                        update={'prices': canonical.prices + new_prices}
                    )
                matched = True
                break

        if not matched:
            merged.append(product.model_copy(deep=True))

    # Post-merge: deduplicate + mark best price using model_copy (no direct mutation)
    result = []
    for product in merged:
        if not product.prices:
            result.append(product)
            continue

        # Deduplicate: keep cheapest per provider
        seen: Dict[str, ProviderPrice] = {}
        for p in product.prices:
            if p.provider not in seen or p.price < seen[p.provider].price:
                seen[p.provider] = p

        deduped = list(seen.values())
        min_price = min(p.price for p in deduped)

        # Mark best + sort cheapest first — all via model_copy, zero direct mutation
        ranked = sorted(
            [p.model_copy(update={'is_best': p.price == min_price}) for p in deduped],
            key=lambda p: p.price
        )

        result.append(product.model_copy(update={'prices': ranked}))

    return result
