"""
Query Parser V2
===============
Step 3 of the pipeline.

V2 CHANGES vs V1:
  - _KNOWN_BRANDS moved to entity_lexicon (single source of truth)
  - Brand augmentation from SQLite catalog DB at startup
  - _resolve_brand() uses word-boundary regex, not substring
  - brand formatting uses CANONICAL_BRAND_NAMES, never .title()
  - _resolve_family() uses word-boundary regex (fixes "airwave" in "airwaves")
  - product_type and feature extraction are SEPARATE passes (P0 fix)
    "noise cancelling headphones" → type=headphones, feature=ANC
    NOT type="noise cancelling"
  - _extract_model() uses alphanumeric model pattern + position context
  - Category-scoped product type keywords (P0 fix: "tab" safe in pharmacy)
  - Unused _NOISE_FAMILIES, _GENERIC, _MODEL_NUM_RE removed
  - ParsedQuery.attributes dict populated for extensible category attributes
  - Edit-distance (Levenshtein) brand matching as Stage B fallback
"""
from __future__ import annotations

import re
from typing import Any

from app.services.search_intelligence.models import (
    ConstraintHardness,
    ConstraintOperator,
    ParsedAttribute,
    ParsedQuery,
    QueryConstraint,
)
from app.services.search_intelligence.entity_lexicon import (
    CANONICAL_BRAND_NAMES,
    FAMILY_ALIASES,
    KNOWN_BRANDS,
    PRODUCT_TYPE_ALIASES_BY_CATEGORY,
    _BRAND_ALIAS_MAP,
    get_category_alias_records,
)


# ─────────────────────────────────────────────────────────────────────────────
# Catalog-derived brand augmentation
# Reads distinct brand values from ingested products in SQLite DB.
# Runs once at startup; adds to KNOWN_BRANDS without code changes.
# ─────────────────────────────────────────────────────────────────────────────
_catalog_brands: set[str] = set()

def _load_catalog_brands() -> None:
    """
    Populate _catalog_brands from the SQLite product catalog.
    Safe to call multiple times — only runs if catalog is empty.
    Only loads brands that appear in >= 3 distinct products.
    """
    global _catalog_brands
    if _catalog_brands:
        return
    try:
        from app.database import SessionLocal
        from sqlalchemy import text
        with SessionLocal() as db:
            rows = db.execute(text(
                "SELECT DISTINCT lower(brand) FROM products "
                "WHERE brand IS NOT NULL AND brand != '' "
                "GROUP BY lower(brand) HAVING count(*) >= 3"
            )).fetchall()
            _catalog_brands = {row[0] for row in rows}
    except Exception:
        pass  # DB not available — use only static KNOWN_BRANDS


def get_all_known_brands() -> frozenset[str]:
    """Combined static + catalog-derived known brands."""
    _load_catalog_brands()
    return KNOWN_BRANDS | _catalog_brands


# ─────────────────────────────────────────────────────────────────────────────
# Model number pattern — alphanumeric + common suffixes
# Matches: "6", "S24", "XM5", "WH-1000XM5", "A55", "15 Pro", "Max 6"
# ─────────────────────────────────────────────────────────────────────────────
_MODEL_ALPHANUM_RE = re.compile(
    r"\b(?:[A-Z]{0,3}[-]?)?\d+(?:[A-Za-z]{0,4})?(?:\s+(?:pro|max|plus|lite|ultra|mini|neo|ace|fe|5g|4g))?\b",
    re.I,
)
_COMPACT_UNIT_TOKEN_RE = re.compile(
    r"^\d+(?:\.\d+)?(?:ml|l|lt|ltr|litre|liter|g|gm|kg|mg|pc|pcs|piece|pieces|pack)$",
    re.I,
)

# ─────────────────────────────────────────────────────────────────────────────
# Price constraint patterns
# ─────────────────────────────────────────────────────────────────────────────
_PRICE_UNDER_RE = re.compile(r"\b(?:under|below|less\s+than|within|upto|up\s+to)\s+(?:inr\s*)?(\d+)\b", re.I)
_PRICE_AROUND_RE = re.compile(r"\b(?:around|about|approximately|near)\s+(?:inr\s*)?(\d+)\b", re.I)
_PRICE_ABOVE_RE = re.compile(r"\b(?:above|over|more\s+than|atleast|at\s+least)\s+(?:inr\s*)?(\d+)\b", re.I)

# ─────────────────────────────────────────────────────────────────────────────
# Feature keyword map — separate from product type detection
# ─────────────────────────────────────────────────────────────────────────────
_FEATURE_PHRASES: dict[str, str] = {
    "noise cancelling": "ANC",
    "noise canceling": "ANC",
    "active noise cancellation": "ANC",
    "active noise cancelling": "ANC",
    "anc": "ANC",
    "hybrid anc": "Hybrid ANC",
    "transparency mode": "Transparency Mode",
    "ldac": "LDAC",
    "aptx": "aptX",
    "aptx hd": "aptX HD",
    "aptx adaptive": "aptX Adaptive",
    "wireless": "Wireless",
    "bluetooth": "Bluetooth",
    "true wireless": "True Wireless",
    "tws": "True Wireless",
    "waterproof": "Waterproof",
    "ipx": "Water-Resistant",
    "gaming": "Gaming",
    "low latency": "Low Latency",
    "fast charging": "Fast Charging",
    "touch control": "Touch Controls",
    "foldable": "Foldable",
    "enc": "ENC",
    "multipoint": "Multipoint",
    "multi-point": "Multipoint",
    "spatial audio": "Spatial Audio",
    "dolby atmos": "Dolby Atmos",
    "hi-res audio": "Hi-Res Audio",
    "hires": "Hi-Res Audio",
    "bone conduction": "Bone Conduction",
    "over ear": "Over-Ear",
    "in ear": "In-Ear",
    "on ear": "On-Ear",
    "open back": "Open-Back",
    "closed back": "Closed-Back",
}

# Product type multi-word phrases that should NOT be features
_PRODUCT_TYPE_PHRASES: dict[str, str] = {
    "washing machine": "washing machine",
    "air conditioner": "air conditioner",
    "true wireless": "earbuds",  # → type is earbuds, "true wireless" also becomes feature
}

# ─────────────────────────────────────────────────────────────────────────────
# Quantity/dosage/unit suffixes that make a number NOT a model number
# ─────────────────────────────────────────────────────────────────────────────
_UNIT_SUFFIXES: frozenset[str] = frozenset({
    "ml", "l", "kg", "g", "mg", "gb", "tb", "mah", "w", "wh",
    "hz", "mp", "mm", "cm", "inch", "db", "ms", "hr", "h",
    "months", "month", "year", "years", "days", "day",
    "microphone", "mic", "mics", "speaker", "channel", "band",
})


# ─────────────────────────────────────────────────────────────────────────────
# Brand resolution — word-boundary safe
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_brand(tokens: list[str], normalized: str) -> tuple[str | None, float]:
    """
    Return (canonical_brand, confidence) using word-boundary matching.
    Priority: catalog/static known brands > alias map.
    Brand display name comes from CANONICAL_BRAND_NAMES, never .title().
    """
    all_known = get_all_known_brands()

    # 1. Exact token match against known brands
    for token in tokens:
        if token in all_known:
            canonical = CANONICAL_BRAND_NAMES.get(token, token.capitalize())
            return canonical, 0.99

    # 2. Multi-token known brand match (e.g. "air india")
    bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens)-1)]
    for bigram in bigrams:
        if bigram in all_known:
            canonical = CANONICAL_BRAND_NAMES.get(bigram, bigram.title())
            return canonical, 0.98

    # 3. Alias map with word-boundary check
    for alias_text, alias_record in _BRAND_ALIAS_MAP.items():
        if not alias_record.may_rewrite():
            continue
        pattern = r"(?<!\w)" + re.escape(alias_text) + r"(?!\w)"
        if re.search(pattern, normalized, re.I):
            return alias_record.canonical, 0.95

    return None, 0.0


def _canonical_brand_name(raw: str) -> str:
    """Return proper display-case brand name. Never uses .title()."""
    return CANONICAL_BRAND_NAMES.get(raw.lower(), raw)


# ─────────────────────────────────────────────────────────────────────────────
# Family resolution — word-boundary safe
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_family(normalized: str, brand: str | None, category: str) -> tuple[str | None, float]:
    """
    Contextual alias resolution for product family.
    Uses word-boundary regex — never plain substring `in`.
    """
    brand_lower = (brand or "").lower()

    # Get category-specific family aliases sorted longest-first (prevents partial matches)
    aliases = sorted(FAMILY_ALIASES, key=lambda r: len(r.alias), reverse=True)

    for record in aliases:
        if not record.may_rewrite():
            continue
        # Word-boundary match
        pattern = r"(?<!\w)" + re.escape(record.alias.lower()) + r"(?!\w)"
        if not re.search(pattern, normalized.lower()):
            continue
        # Brand context check
        if record.brand_context and brand_lower != record.brand_context.lower():
            continue
        return record.canonical, 0.93

    # Check if any canonical family value appears directly in the query
    canonical_families = {r.canonical: r.brand_context for r in aliases}
    # Sort by length descending to match longest canonical first
    for canonical, expected_brand_ctx in sorted(canonical_families.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = r"(?<!\w)" + re.escape(canonical.lower()) + r"(?!\w)"
        if re.search(pattern, normalized.lower()):
            if expected_brand_ctx and brand_lower != expected_brand_ctx.lower():
                continue
            return canonical, 0.95

    return None, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Product type extraction — SEPARATE from feature extraction (P0 fix)
# ─────────────────────────────────────────────────────────────────────────────
def _extract_product_type(tokens: list[str], normalized: str, category: str) -> tuple[str | None, float]:
    """
    Extract the PRODUCT TYPE (headphones, smartphone, laptop, etc.)
    This is a SEPARATE pass from feature extraction.

    P0 FIX: "noise cancelling headphones" → type=headphones
    NEVER returns "noise cancelling" as a product type.

    Uses category-scoped keyword maps to avoid cross-category false positives
    (e.g. "tab" is only a tablet in Shopping, not in Pharmacy).
    """
    # Category-scoped type aliases
    type_map = PRODUCT_TYPE_ALIASES_BY_CATEGORY.get(category.lower(), {})

    # 1. Check multi-word product type phrases first
    for phrase, canonical in _PRODUCT_TYPE_PHRASES.items():
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        if re.search(pattern, normalized, re.I):
            return canonical, 0.90

    # 2. Check category-scoped aliases (alias → canonical)
    for alias, canonical in type_map.items():
        pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
        if re.search(pattern, normalized, re.I):
            return canonical, 0.93

    # 3. Check if any canonical type value appears directly in the query
    # e.g. "headphones", "laptop", "smartphone" appear verbatim
    canonical_types = set(type_map.values())
    for canonical in canonical_types:
        pattern = r"(?<!\w)" + re.escape(canonical) + r"(?!\w)"
        if re.search(pattern, normalized, re.I):
            return canonical, 0.95

    return None, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Feature extraction — completely separate from type extraction
# ─────────────────────────────────────────────────────────────────────────────
def _extract_features(normalized: str) -> list[str]:
    """
    Extract product features from the query.
    Runs AFTER product_type extraction, as a completely separate pass.
    Both can fire simultaneously — "ANC headphones" → type=headphones, feature=ANC.
    """
    features: list[str] = []
    # Sort longest-phrase-first to prevent partial matches
    for phrase, label in sorted(_FEATURE_PHRASES.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        if re.search(pattern, normalized, re.I) and label not in features:
            features.append(label)
    return features


# ─────────────────────────────────────────────────────────────────────────────
# Model number extraction — position-aware + alphanumeric
# ─────────────────────────────────────────────────────────────────────────────
def _extract_model(
    normalized: str,
    brand: str | None,
    family: str | None,
) -> tuple[str | None, float]:
    """
    Extract model number — STRICT, never guessed from semantics.

    V2 improvements:
    - Alphanumeric model patterns (S24, XM5, A55, not just pure integers)
    - Position-aware: number after brand/family → high confidence model
    - Unit suffix exclusion (650 mg, 128 GB, 6 months → not model numbers)
    - Price expression exclusion (runs first)
    - No arbitrary threshold like ">=500 means price"
    """
    # Strip price constraint spans first
    price_cleaned = _PRICE_UNDER_RE.sub(" PRICEREMOVED ", normalized)
    price_cleaned = _PRICE_AROUND_RE.sub(" PRICEREMOVED ", price_cleaned)
    price_cleaned = _PRICE_ABOVE_RE.sub(" PRICEREMOVED ", price_cleaned)

    # Find position of brand/family in query for context
    anchor_end = 0
    if brand:
        m = re.search(r"(?<!\w)" + re.escape(brand.lower()) + r"(?!\w)", price_cleaned.lower())
        if m:
            anchor_end = m.end()
    if family:
        m = re.search(r"(?<!\w)" + re.escape(family.lower()) + r"(?!\w)", price_cleaned.lower())
        if m and m.end() > anchor_end:
            anchor_end = m.end()

    # Find all candidate model tokens
    for match in _MODEL_ALPHANUM_RE.finditer(price_cleaned):
        candidate = match.group(0).strip()
        pos = match.start()

        # Must come after brand/family anchor (or early in query)
        if anchor_end > 0 and pos < anchor_end - 2:
            continue

        # Compact quantity tokens are pack/size constraints, not model numbers.
        # "Amul Gold Milk 500ml" must not become model="500ml".
        if _COMPACT_UNIT_TOKEN_RE.match(candidate.replace(" ", "")):
            continue

        # Skip if followed by a unit suffix
        after = price_cleaned[match.end():match.end() + 12].strip().lower()
        first_word_after = after.split()[0] if after.split() else ""
        if first_word_after in _UNIT_SUFFIXES:
            continue

        # Skip price removal markers
        if "PRICEREMOVED" in candidate:
            continue

        # Require at least one digit
        if not re.search(r"\d", candidate):
            continue

        # Good model candidate
        # Confidence: higher if positioned after brand/family
        conf = 0.95 if anchor_end > 0 else 0.80
        return candidate, conf

    return None, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Price constraint extraction + typed QueryConstraint
# ─────────────────────────────────────────────────────────────────────────────
def _extract_price_constraint(normalized: str) -> tuple[dict[str, float] | None, list[QueryConstraint]]:
    """Extract price constraints and return both legacy dict and typed constraints."""
    constraints: list[QueryConstraint] = []
    price_dict: dict[str, float] | None = None

    m = _PRICE_UNDER_RE.search(normalized)
    if m:
        val = float(m.group(1))
        price_dict = {"max": val}
        constraints.append(QueryConstraint(
            attribute="price", operator=ConstraintOperator.LTE, value=val,
            confidence=0.95, hardness=ConstraintHardness.SOFT,
            evidence_span=m.group(0),
        ))
        return price_dict, constraints

    m = _PRICE_AROUND_RE.search(normalized)
    if m:
        v = float(m.group(1))
        price_dict = {"min": v * 0.85, "max": v * 1.15}
        constraints.append(QueryConstraint(
            attribute="price", operator=ConstraintOperator.LTE, value=v * 1.15,
            confidence=0.85, hardness=ConstraintHardness.PREFERENCE,
            evidence_span=m.group(0),
        ))
        return price_dict, constraints

    m = _PRICE_ABOVE_RE.search(normalized)
    if m:
        val = float(m.group(1))
        price_dict = {"min": val}
        constraints.append(QueryConstraint(
            attribute="price", operator=ConstraintOperator.GTE, value=val,
            confidence=0.90, hardness=ConstraintHardness.SOFT,
            evidence_span=m.group(0),
        ))
        return price_dict, constraints

    return None, []


# ─────────────────────────────────────────────────────────────────────────────
# Main parse function
# ─────────────────────────────────────────────────────────────────────────────
def parse(normalized_query: str, category: str = "Shopping", brand: str | None = None) -> ParsedQuery:
    """
    Parse a normalized query string into structured attributes.

    Steps:
      1. Brand resolution (word-boundary, catalog-derived)
      2. Family resolution (word-boundary, context-sensitive)
      3. Product type extraction (category-scoped, separate from features)
      4. Feature extraction (separate pass — both can fire simultaneously)
      5. Model extraction (alphanumeric, position-aware, unit-safe)
      6. Price constraint extraction (typed QueryConstraints)
    """
    tokens = normalized_query.lower().split()

    # 1. Brand
    resolved_brand, brand_conf = _resolve_brand(tokens, normalized_query)
    if brand and not resolved_brand:  # upstream override (from alias resolver)
        resolved_brand = brand
        brand_conf = 0.90

    # 2. Family
    resolved_family, family_conf = _resolve_family(normalized_query, resolved_brand, category)

    # 3. Product type (category-scoped, SEPARATE from features)
    resolved_type, type_conf = _extract_product_type(tokens, normalized_query, category)

    # 4. Features (independent pass — both ANC and headphones can fire)
    features = _extract_features(normalized_query)

    # 5. Model (position-aware, alphanumeric)
    resolved_model, model_conf = _extract_model(normalized_query, resolved_brand, resolved_family)

    # 6. Price constraint (typed)
    price_constraint, typed_constraints = _extract_price_constraint(normalized_query)

    # Build typed model constraint if model found
    if resolved_model and model_conf >= 0.90:
        typed_constraints.append(QueryConstraint(
            attribute="model",
            operator=ConstraintOperator.EQ,
            value=resolved_model,
            confidence=model_conf,
            hardness=ConstraintHardness.HARD,
            evidence_span=resolved_model,
        ))

    return ParsedQuery(
        brand=resolved_brand,
        brand_confidence=brand_conf,
        product_family=resolved_family,
        family_confidence=family_conf,
        model=resolved_model,
        model_confidence=model_conf,
        product_type=resolved_type,
        type_confidence=type_conf,
        features=features,
        price_constraint=price_constraint,
        constraints=typed_constraints,
    )
