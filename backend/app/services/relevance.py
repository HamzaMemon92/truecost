"""
TrueCost Relevance Scoring Engine
Scores each product against the user's search query using token matching.
Returns a score 0.0–1.0 where 1.0 = perfect match.
"""

import re
from difflib import SequenceMatcher
from typing import List


def _tokenize(text: str) -> List[str]:
    """Lowercase, remove punctuation, split into tokens."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return [t for t in text.split() if t]


# Words that carry no semantic meaning (stop words for product matching)
_STOP_WORDS = {
    "of", "the", "a", "an", "and", "with", "in", "for", "by",
    "to", "from", "near", "at", "pack", "pcs", "piece", "pieces", "combo", "set", "buy",
}
_SPEC_UNITS = {
    "ml", "l", "kg", "g", "gm", "ltr", "litre", "litres", "h", "hr", "hrs", "hour", "hours",
    "mah", "w", "mm", "cm", "inch", "inches", "gb", "tb", "hz", "khz", "pack", "pcs", "piece", "pieces",
}
_SPEC_WORDS = {"battery", "driver", "drivers", "capacity", "playtime", "backup", "screen", "display"}
_SPEC_NUMERIC_RE = re.compile(r"^\d+(?:ml|l|kg|g|gm|ltr|litre|litres|h|hr|hrs|hour|hours|mah|w|mm|cm|inch|inches|gb|tb|hz|khz)$")

# Brand name normalisation aliases for fuzzy matching
# e.g. "boat" → "boat", "adil qadri" → "adilqadri"
_BRAND_ALIASES: dict[str, str] = {
    "adil qadri": "adilqadri",
    "adil": "adilqadri",
    "aadil": "adilqadri",
    "aadil qadri": "adilqadri",
    "boat": "boat",
    "jbl": "jbl",
    "noise": "noise",
    "oneplus": "oneplus",
    "one plus": "oneplus",
    "samsung": "samsung",
    "apple": "apple",
    "meesho": "meesho",
}


def _normalize_brand_query(text: str) -> str:
    """Normalise known brand name misspellings in user queries."""
    t = text.lower().strip()
    for alias, canonical in _BRAND_ALIASES.items():
        if alias in t:
            t = t.replace(alias, canonical)
    return t


def _clean_tokens(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t not in _STOP_WORDS and (len(t) > 1 or any(char.isdigit() for char in t))]


def _is_spec_number(tokens: list[str], index: int) -> bool:
    token = tokens[index]
    if not any(char.isdigit() for char in token):
        return False
    previous_token = tokens[index - 1] if index > 0 else ""
    next_token = tokens[index + 1] if index + 1 < len(tokens) else ""
    return bool(_SPEC_NUMERIC_RE.match(token)) or next_token in _SPEC_UNITS or previous_token in _SPEC_WORDS


def _exact_tokens(text: str) -> list[str]:
    raw_tokens = _clean_tokens(_tokenize(text))
    result: list[str] = []
    for index, token in enumerate(raw_tokens):
        if token in _SPEC_UNITS:
            continue
        if _is_spec_number(raw_tokens, index):
            continue
        result.append(token)
    return result


def _model_numbers(text: str) -> set[str]:
    tokens = _clean_tokens(_tokenize(text))
    return {token for index, token in enumerate(tokens) if any(char.isdigit() for char in token) and not _is_spec_number(tokens, index)}


def score_product(query: str, product_name: str, product_brand: str = "") -> float:
    """
    Score a product against a search query.

    Returns:
        0.0  → completely unrelated
        0.4  → loosely related (some shared tokens)
        0.7  → closely related (most tokens match)
        0.85 → very strong match
        1.0  → exact / near-exact match
    """
    # Normalise known brand misspellings in queries ("aadil qadri" → "adilqadri")
    normalised_query = _normalize_brand_query(query)
    
    query_tokens = set(_clean_tokens(_tokenize(normalised_query)))
    name_tokens = set(_clean_tokens(_tokenize(product_name)))
    brand_tokens = set(_clean_tokens(_tokenize(product_brand)))
    searchable_tokens = name_tokens | brand_tokens

    if not query_tokens or not searchable_tokens:
        return 0.0

    # 1. Exact substring match in name (highest signal)
    q_lower = normalised_query.lower().strip()
    n_lower = product_name.lower().strip()
    n_combined = f"{product_name} {product_brand}".lower().strip()
    if q_lower in n_lower or n_lower.startswith(q_lower):
        return 1.0
    # Also check brand-combined: "adilqadri" in "Adilqadri Oudh al Hashmi"
    if q_lower in n_combined:
        return 1.0

    # 2. Single word brand-only query → match if any product token contains it
    if len(query_tokens) == 1:
        single = list(query_tokens)[0]
        if any(single in t or t in single for t in searchable_tokens):
            return 0.85

    # 3. Coverage logic (Two-Way)
    matched = query_tokens & searchable_tokens
    
    # query_coverage = how much of the user's query is in the product
    query_coverage = len(matched) / len(query_tokens)
    
    # product_coverage = how much of the product's name is in the query
    product_coverage = len(matched) / len(searchable_tokens)
    
    # Max coverage prevents penalizing short products matching long queries
    best_coverage = max(query_coverage, product_coverage)

    # 4. Fuzzy name similarity (SequenceMatcher handles typos)
    fuzzy = SequenceMatcher(None, q_lower, n_lower).ratio()

    # 5. Weighted blend: token coverage is the primary signal
    score = (best_coverage * 0.8) + (fuzzy * 0.2)

    return round(min(score, 1.0), 4)


def score_exact_product(query: str, product_name: str, product_brand: str = "") -> float:
    """Score a selected-product comparison.

    This is intentionally stricter than discovery search. A shared generic word
    such as "bluetooth" or "max" must not make a different SKU look like the
    same product offer.
    """
    query_tokens = set(_exact_tokens(query))
    searchable_tokens = set(_exact_tokens(f"{product_name} {product_brand}"))
    if not query_tokens or not searchable_tokens:
        return 0.0

    matched = query_tokens & searchable_tokens
    query_coverage = len(matched) / len(query_tokens)
    product_coverage = len(matched) / len(searchable_tokens)
    fuzzy = SequenceMatcher(None, " ".join(sorted(query_tokens)), " ".join(sorted(searchable_tokens))).ratio()
    score = min((max(query_coverage, product_coverage) * 0.82) + (fuzzy * 0.18), 1.0)

    # Model numbers are strong identity signals. If the selected product has a
    # number and a provider result does not contain it, keep it out of exact
    # comparison even if generic words match.
    query_numbers = _model_numbers(query)
    product_numbers = _model_numbers(f"{product_name} {product_brand}")
    if query_numbers and not query_numbers.issubset(product_numbers):
        return round(min(score, 0.34), 4)

    # Brand/model phrase coverage must be high for exact comparison. This keeps
    # "Noise Airwave Max 6" away from unrelated "BT Max" headphones.
    if query_coverage < 0.75:
        return round(min(score, 0.34), 4)

    return score


def classify_product(query: str, product_name: str, product_brand: str = "") -> str:
    """
    Returns one of:
    - "primary"       → score >= 0.55 (exact or near-exact match)
    - "secondary"     → score >= 0.35 (related product)
    - "discard"       → score < 0.35 (irrelevant noise)
    """
    score = score_product(query, product_name, product_brand)
    if score >= 0.55:
        return "primary"
    elif score >= 0.35:
        return "secondary"
    return "discard"
