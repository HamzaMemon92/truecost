"""
Query Specificity Classifier V2
=================================
Determines how specific the user's query is.

V2 CHANGES:
  - nl_triggers uses word-boundary regex (P0 fix: "laptop" no longer triggers NATURAL_LANG)
  - IDENTIFIER specificity is now actually implemented and returned
    (was defined in enum but never produced — now fires for SKU-like patterns)
  - specificity_score: float added (0.0 = very broad → 1.0 = exact identifier)
  - build_hard_constraints() produces both legacy dict and typed QueryConstraint list
  - nl_triggers promoted to module-level constant (not rebuilt per call)
"""
from __future__ import annotations

import re

from app.services.search_intelligence.models import (
    ConstraintHardness,
    ConstraintOperator,
    ParsedQuery,
    QueryConstraint,
    QuerySpecificity,
)


# ─────────────────────────────────────────────────────────────────────────────
# Natural-language query trigger — word-boundary safe
# ─────────────────────────────────────────────────────────────────────────────
# P0 FIX: was `t in normalized_query` — substring match caused "laptop" to
# trigger is_natural_lang because "top" in "laptop" is True.
# Now uses \b word boundaries.
_NL_TRIGGER_RE = re.compile(
    r"\b(?:best|cheapest|affordable|budget|recommended|popular|top|"
    r"under|below|above|around|within|value|worth|good)\b",
    re.I,
)

# ─────────────────────────────────────────────────────────────────────────────
# IDENTIFIER pattern — SKU/MPN/EAN-like strings
# Must NOT match plain integers (prices, quantities) or short model numbers
# Matches: "WH-1000XM5", "SM-A546E", "B09V3ZNDQS", "EAN:1234567890"
# Does NOT match: "5000", "6", "5G", "24" — those are handled as model/price
# ─────────────────────────────────────────────────────────────────────────────
_IDENTIFIER_RE = re.compile(
    r"\b(?:"
    # Pattern 1: LETTER(S)-DIGITS-LETTERS format: WH-1000XM5, SM-A546E
    r"[A-Za-z]{1,5}-\d{3,}[A-Za-z0-9]*"
    # Pattern 2: Long alphanumeric code with BOTH letters and digits (8+ chars): B09V3ZNDQS
    r"|(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*[0-9])[A-Z0-9]{8,}"
    # Pattern 3: Labeled identifiers
    r"|(?:ean|sku|asin|mpn):\s*\S+"
    r")\b",
    re.I,
)


def classify(parsed: ParsedQuery, normalized_query: str) -> QuerySpecificity:
    """
    Return the QuerySpecificity for the given parsed attributes.

    Evaluation order (highest to lowest priority):
      1. Has identifier-like token → IDENTIFIER
      2. Has model number + brand or family → EXACT_MODEL
      3. Has brand + family (no model) → FAMILY
      4. Has brand only → BRAND or NATURAL_LANG
      5. Natural-language triggers (price/superlatives) + type → NATURAL_LANG
      6. Has product type + feature → CAT_FEATURE
      7. Everything else → BROAD
    """
    has_model = bool(parsed.model)
    has_brand = bool(parsed.brand)
    has_family = bool(parsed.product_family)
    has_type = bool(parsed.product_type)
    has_feature = bool(parsed.features)
    has_price = parsed.price_constraint is not None

    # Word-boundary safe natural-language detection
    is_natural_lang = has_price or bool(_NL_TRIGGER_RE.search(normalized_query))

    # 1. Identifier (highest specificity — no brand/family needed)
    if _IDENTIFIER_RE.search(normalized_query):
        return QuerySpecificity.IDENTIFIER

    # 2. Exact model: needs model + (brand or family)
    if has_model and (has_brand or has_family):
        return QuerySpecificity.EXACT_MODEL

    # 3. Natural-language with model (e.g. "best Sony XM5") → EXACT_MODEL wins
    if has_model and is_natural_lang and (has_brand or has_family):
        return QuerySpecificity.EXACT_MODEL

    # 4. Brand + family (no model)
    if has_brand and has_family and not has_model:
        return QuerySpecificity.FAMILY

    # 5. Brand only
    if has_brand and not has_family and not has_model:
        if is_natural_lang:
            return QuerySpecificity.NATURAL_LANGUAGE
        return QuerySpecificity.BRAND

    # 6. Natural language with type constraint
    if is_natural_lang and (has_type or has_price):
        return QuerySpecificity.NATURAL_LANGUAGE

    # 7. Category feature
    if has_type and has_feature:
        return QuerySpecificity.CATEGORY_FEATURE

    return QuerySpecificity.BROAD


def specificity_score(specificity: QuerySpecificity, parsed: ParsedQuery) -> float:
    """
    Return a float 0.0 → 1.0 representing how specific the query is.
    Used for ranking interpolation (not binary branch jumping).

    Examples:
      "headphones"              → BROAD, 0.05
      "Noise headphones"        → BRAND, 0.30
      "Noise Airwave"           → FAMILY, 0.55
      "Noise Airwave Max 6"     → EXACT_MODEL, 0.90
      "WH-1000XM5"              → IDENTIFIER, 0.98
      "best headphones under 5k" → NATURAL_LANG, 0.20
      "ANC headphones"          → CAT_FEATURE, 0.25
    """
    base_scores = {
        QuerySpecificity.BROAD: 0.05,
        QuerySpecificity.CATEGORY_FEATURE: 0.25,
        QuerySpecificity.NATURAL_LANGUAGE: 0.20,
        QuerySpecificity.BRAND: 0.35,
        QuerySpecificity.FAMILY: 0.60,
        QuerySpecificity.EXACT_MODEL: 0.88,
        QuerySpecificity.IDENTIFIER: 0.98,
    }
    score = base_scores.get(specificity, 0.10)
    # Boost if multiple signals present
    if parsed.brand and parsed.product_family and parsed.model:
        score = min(score + 0.05, 0.95)
    return score


def build_hard_constraints(parsed: ParsedQuery) -> dict[str, str]:
    """
    Return hard constraints dict (legacy format) for backward compat.
    Brand and model are always hard when detected with high confidence.
    """
    constraints: dict[str, str] = {}
    if parsed.brand and parsed.brand_confidence >= 0.90:
        constraints["brand"] = parsed.brand
    if parsed.model and parsed.model_confidence >= 0.90:
        constraints["model"] = parsed.model
    # Include any typed HARD constraints from attributes
    for c in parsed.constraints:
        if c.hardness == ConstraintHardness.HARD and c.attribute not in constraints:
            constraints[c.attribute] = str(c.value)
    return constraints
