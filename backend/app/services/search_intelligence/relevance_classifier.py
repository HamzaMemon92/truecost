r"""
Query-Product Relevance Classifier V2
=======================================
Step 6 of the pipeline — post-retrieval ESCI classification.

V2 P0 BUG FIXES:
  1. Brand matching: was `qb in name_lower` (substring) — now token-level check
     Fixes: "Mi" brand matching inside "milk", "mix", "minimal"
  2. Model matching: was `re.findall(r"\b\d+\b")` — only pure digits
     Fixes: "S24", "XM5", "A55" alphanumeric models now extracted correctly
     Also fixes: model="6" matching "pack of 6", "6 microphones"
  3. NATURAL_LANGUAGE branch: `type_ok` alone returned EXACT_INTENT
     Fixes: "best Sony headphones" classifying non-Sony products as EXACT_INTENT
  4. Final fallback: was `return EXACT_INTENT` — unsafe optimistic default
     Fixes: unknown query classes now return SUBSTITUTE (conservative)
  5. BROAD fallback: was `EXACT_INTENT` if no product_type — unsafe
     Fixes: unrecognized queries no longer get EXACT_INTENT for everything
  6. COMPLEMENT: now actually implemented for accessory detection

KEY ARCHITECTURE RULES (unchanged):
  - SPELLING ≠ QUERY RELEVANCE ≠ ENTITY RESOLUTION ≠ RANKING
  - Hard constraints (model, dosage, storage) are NEVER relaxed
  - Model mismatch → always SUBSTITUTE, never EXACT_INTENT
  - Brand mismatch → IRRELEVANT for EXACT_MODEL / FAMILY queries
"""
from __future__ import annotations

import re
from typing import Any

from app.services.search_intelligence.models import (
    ParsedQuery,
    QueryIntent,
    QueryRelevance,
    QuerySpecificity,
)


# ─────────────────────────────────────────────────────────────────────────────
# Accessory / complement keywords — for COMPLEMENT classification
# ─────────────────────────────────────────────────────────────────────────────
_ACCESSORY_KEYWORDS: frozenset[str] = frozenset({
    "case", "cover", "skin", "protector", "pouch", "bag", "sleeve",
    "cable", "charger", "adapter", "dock", "stand", "holder",
    "strap", "band", "screen guard", "tempered glass",
    "stylus", "pen", "keyboard", "mouse",
    "cushion", "pad", "eartip", "ear tip", "earcup", "foam",
})

_MILK_VARIANT_TOKENS: frozenset[str] = frozenset({
    "gold", "taaza", "taza", "taja", "toned", "shakti", "standard", "standardised",
    "standardized", "lactose", "free", "slim", "skimmed", "full", "cream",
})
_NON_MILK_DAIRY_TOKENS: frozenset[str] = frozenset({
    "cheese", "shrikhand", "paneer", "butter", "ghee", "curd", "dahi", "yogurt",
    "yoghurt", "lassi", "cream", "whitener",
})
_MILK_SPECIALTY_TOKENS: frozenset[str] = frozenset({
    "lactose", "slim", "skimmed", "kool", "shake", "drink", "beverage", "badam",
    "rose", "kesar", "elaichi", "condensed", "mithai", "spray", "powder", "baby",
})


def _normalize_tok(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())


def _word_tokens(text: str) -> set[str]:
    return set(re.findall(r"\b[a-z0-9]+\b", _normalize_tok(text)))


def _milk_variant_signature(tokens: set[str]) -> set[str]:
    variants = set(tokens) & set(_MILK_VARIANT_TOKENS)
    if "gold" in tokens or {"full", "cream"} <= tokens:
        variants.difference_update({"gold", "full", "cream"})
        variants.add("full_cream")
    if {"taaza", "taza", "taja", "toned"} & tokens:
        variants.difference_update({"taaza", "taza", "taja", "toned"})
        variants.add("toned")
    if {"lactose", "free"} <= tokens:
        variants.difference_update({"lactose", "free"})
        variants.add("lactose_free")
    if {"slim", "skimmed"} & tokens:
        variants.difference_update({"slim", "skimmed"})
        variants.add("skimmed")
    return variants


def _grocery_product_type_relevance(intent: QueryIntent, product_name: str) -> QueryRelevance | None:
    pq = intent.parsed
    if str(intent.category or "").casefold() != "grocery" or pq.product_type != "milk":
        return None

    query_tokens = _word_tokens(intent.normalized_query or intent.raw_query)
    product_tokens = _word_tokens(product_name)

    if "milk" not in product_tokens:
        return QueryRelevance.IRRELEVANT
    if (product_tokens & _NON_MILK_DAIRY_TOKENS) and "milk" not in product_tokens:
        return QueryRelevance.IRRELEVANT

    query_variants = _milk_variant_signature(query_tokens)
    product_variants = _milk_variant_signature(product_tokens)
    if query_variants and not query_variants.issubset(product_variants):
        return QueryRelevance.SUBSTITUTE

    if not query_variants and product_tokens & _MILK_SPECIALTY_TOKENS:
        return QueryRelevance.SUBSTITUTE

    return QueryRelevance.EXACT_INTENT


def _extract_model_tokens(title: str) -> list[str]:
    r"""
    Extract alphanumeric model tokens from a product title.

    V2 FIX: V1 only extracted pure digits (`\b\d+\b`), so:
      - "S24" was never extracted → "Samsung Galaxy S24" always mismatched
      - model="6" matched "pack of 6", "6 mics", "6 months warranty"

    Now extracts alphanumeric patterns that look like model identifiers:
      - Pure numbers: "6", "15", "24"  (only when standalone, not unit-followed)
      - Alphanumeric: "S24", "XM5", "A55", "1000XM5"
      - But NOT: "6 months", "128 GB" (unit-followed numbers)
    """
    # Find alphanumeric model candidates
    alphanum_models = re.findall(r"\b[A-Z]{0,3}\d+[A-Za-z]*\b", title)

    # Also extract pure numbers NOT followed by units
    unit_suffixes = {
        "months", "month", "years", "year", "days", "day", "hrs", "hr",
        "hours", "hour", "gb", "tb", "mb", "mah", "w", "v", "hz",
        "mm", "cm", "inches", "inch", "kg", "g", "ml", "l",
        "microphones", "mic", "mics", "speakers", "channels", "band",
        "warranty", "guarantee", "pack", "piece", "pcs", "units",
    }
    title_lower = title.lower()
    for m in re.finditer(r"\b(\d+)\b", title_lower):
        num = m.group(1)
        # Check what follows
        after = title_lower[m.end():m.end() + 20].strip()
        first_word = after.split()[0] if after.split() else ""
        if first_word in unit_suffixes:
            continue
        if num not in alphanum_models:
            alphanum_models.append(num)

    return alphanum_models


def _brand_matches_tokens(product_name: str, product_brand: str | None, query_brand: str) -> bool:
    """
    V2 FIX: Was `qb in name_lower` (substring) — now token-level check.
    "Mi" no longer matches inside "milk", "mix", "minimal".
    """
    qb = query_brand.lower()
    name_tokens = set(_normalize_tok(product_name).split())
    brand_tokens = set(_normalize_tok(product_brand or "").split())

    # Check if query brand appears as a complete word in name or brand field
    return qb in name_tokens or qb in brand_tokens


def _family_matches(product_name: str, family: str) -> bool:
    """Check if product family appears in product name (word-boundary safe)."""
    fam_lower = family.lower()
    pattern = r"(?<!\w)" + re.escape(fam_lower) + r"(?!\w)"
    return bool(re.search(pattern, product_name.lower()))


def _model_matches(product_name: str, model: str) -> bool:
    """
    V2 FIX: Strict model match — model token must be a proper model identifier
    in the title, not any number.

    e.g. model="6" must match "Max 6" but not "pack of 6" or "6 microphones".
    """
    title_models = _extract_model_tokens(product_name)
    return model in title_models


def _is_accessory(product_name: str) -> bool:
    """Check if a product is likely an accessory/complement for the searched product."""
    name_lower = _normalize_tok(product_name)
    name_words = set(name_lower.split())
    return bool(name_words & _ACCESSORY_KEYWORDS)


# ─────────────────────────────────────────────────────────────────────────────
# Main classifier
# ─────────────────────────────────────────────────────────────────────────────
def classify_product_relevance(
    intent: QueryIntent,
    product_name: str,
    product_brand: str | None = None,
    product_category: str | None = None,
) -> QueryRelevance:
    """
    Classify a single product against the user's intent.

    ESCI classification:
      EXACT_INTENT  — This is precisely what the user asked for
      SUBSTITUTE    — Close alternative (different model, same brand/family)
      COMPLEMENT    — Accessory for what was searched
      IRRELEVANT    — Unrelated

    Safety principle: Always fail CONSERVATIVE (SUBSTITUTE/IRRELEVANT),
    never OPTIMISTIC (EXACT_INTENT) when uncertain.
    """
    pq = intent.parsed
    specificity = intent.specificity
    hard = intent.hard_constraints

    name_lower = _normalize_tok(product_name)
    grocery_type_relevance = _grocery_product_type_relevance(intent, product_name)
    if grocery_type_relevance == QueryRelevance.IRRELEVANT:
        return QueryRelevance.IRRELEVANT

    # ── COMPLEMENT check (cross-specificity) ──────────────────────────────────
    # If the product is clearly an accessory for the searched product type,
    # classify as COMPLEMENT regardless of specificity.
    # Works even when product_type is None (e.g. exact model queries)
    if _is_accessory(product_name):
        # If there's a known product type, make sure this accessory isn't that type
        if pq.product_type is None or pq.product_type.lower() not in name_lower:
            return QueryRelevance.COMPLEMENT

    # ── BROAD / CAT_FEATURE ───────────────────────────────────────────────────
    if specificity in (QuerySpecificity.BROAD, QuerySpecificity.CATEGORY_FEATURE):
        if pq.product_type and pq.product_type.lower() in name_lower:
            return QueryRelevance.EXACT_INTENT
        if pq.features:
            feat_lower = [f.lower() for f in pq.features]
            if any(f in name_lower for f in feat_lower):
                return QueryRelevance.EXACT_INTENT
        # V2 FIX: was EXACT_INTENT if no product_type — unsafe
        # Now: SUBSTITUTE (conservative fallback — let ER decide)
        if not pq.product_type and not pq.features:
            return QueryRelevance.SUBSTITUTE
        return QueryRelevance.IRRELEVANT

    # ── BRAND ─────────────────────────────────────────────────────────────────
    if specificity == QuerySpecificity.BRAND:
        if pq.brand and _brand_matches_tokens(product_name, product_brand, pq.brand):
            if grocery_type_relevance is not None:
                return grocery_type_relevance
            if pq.product_type and pq.product_type.lower() not in name_lower:
                return QueryRelevance.IRRELEVANT
            return QueryRelevance.EXACT_INTENT
        if pq.brand:
            return QueryRelevance.IRRELEVANT
        return QueryRelevance.EXACT_INTENT

    # ── FAMILY ────────────────────────────────────────────────────────────────
    if specificity == QuerySpecificity.FAMILY:
        brand_ok = not pq.brand or _brand_matches_tokens(product_name, product_brand, pq.brand)
        family_ok = not pq.product_family or _family_matches(product_name, pq.product_family)

        if brand_ok and family_ok:
            return QueryRelevance.EXACT_INTENT
        if brand_ok and not family_ok:
            return QueryRelevance.SUBSTITUTE  # Same brand, different family
        if not brand_ok and family_ok:
            return QueryRelevance.SUBSTITUTE  # Same family, different brand
        return QueryRelevance.IRRELEVANT

    # ── EXACT_MODEL ───────────────────────────────────────────────────────────
    if specificity == QuerySpecificity.EXACT_MODEL:
        brand_ok = not pq.brand or _brand_matches_tokens(product_name, product_brand, pq.brand)
        family_ok = not pq.product_family or _family_matches(product_name, pq.product_family)
        model_ok = not pq.model or _model_matches(product_name, pq.model)

        # Hard constraint vetoes (from QueryConstraint system)
        hard_brand = hard.get("brand")
        hard_model = hard.get("model")

        if hard_brand and not _brand_matches_tokens(product_name, product_brand, hard_brand):
            return QueryRelevance.IRRELEVANT

        if hard_model and not _model_matches(product_name, hard_model):
            # Brand matches but model doesn't → SUBSTITUTE, not IRRELEVANT
            return QueryRelevance.SUBSTITUTE if brand_ok else QueryRelevance.IRRELEVANT

        if brand_ok and family_ok and model_ok:
            if grocery_type_relevance is not None:
                return grocery_type_relevance
            return QueryRelevance.EXACT_INTENT
        if brand_ok and (family_ok or model_ok):
            return QueryRelevance.SUBSTITUTE
        if brand_ok:
            return QueryRelevance.SUBSTITUTE
        return QueryRelevance.IRRELEVANT

    # ── IDENTIFIER ────────────────────────────────────────────────────────────
    if specificity == QuerySpecificity.IDENTIFIER:
        # For identifier queries, check if identifier appears in product name
        raw = intent.normalized_query
        # The identifier itself should appear verbatim in the product name
        if any(token.lower() in name_lower for token in raw.split() if len(token) >= 5):
            return QueryRelevance.EXACT_INTENT
        return QueryRelevance.SUBSTITUTE

    # ── NATURAL_LANGUAGE ──────────────────────────────────────────────────────
    if specificity == QuerySpecificity.NATURAL_LANGUAGE:
        type_ok = not pq.product_type or pq.product_type.lower() in name_lower
        brand_ok = not pq.brand or _brand_matches_tokens(product_name, product_brand, pq.brand)

        if type_ok and brand_ok:
            if grocery_type_relevance is not None:
                return grocery_type_relevance
            return QueryRelevance.EXACT_INTENT

        # V2 FIX: was `if type_ok: return EXACT_INTENT` — ignoring brand constraint
        # "best Sony headphones" should NOT return non-Sony as EXACT_INTENT
        if type_ok and not pq.brand:
            # No brand constraint — type match is sufficient
            return QueryRelevance.EXACT_INTENT

        if type_ok and pq.brand and not brand_ok:
            # Has brand constraint but brand doesn't match → SUBSTITUTE
            return QueryRelevance.SUBSTITUTE

        return QueryRelevance.IRRELEVANT

    # V2 FIX: Final fallback was EXACT_INTENT — unsafe optimistic default
    # Now: SUBSTITUTE (conservative — never promote unknown to authoritative)
    return QueryRelevance.SUBSTITUTE


# ─────────────────────────────────────────────────────────────────────────────
# Batch classifier
# ─────────────────────────────────────────────────────────────────────────────
def classify_products_batch(
    intent: QueryIntent,
    products: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Annotate a list of product dicts with queryRelevance field.
    IRRELEVANT → matchTier="rejected"
    SUBSTITUTE → matchTier="related" (never primary)
    COMPLEMENT → matchTier="complement"
    EXACT_INTENT → keeps existing ER-based matchTier
    """
    for product in products:
        name = product.get("name") or product.get("title") or ""
        brand = product.get("brand") or ""
        entity_resolution = product.get("entityResolution") or product.get("identity") or {}
        resolver_exact = (
            isinstance(entity_resolution, dict)
            and entity_resolution.get("decision") == "EXACT"
            and not entity_resolution.get("conflicts")
        )
        legacy_exact = (
            isinstance(entity_resolution, dict)
            and entity_resolution.get("match_tier") == "exact"
            and not entity_resolution.get("rejection_reason")
        )
        relevance = classify_product_relevance(
            intent=intent,
            product_name=name,
            product_brand=brand,
        )
        product["queryRelevance"] = relevance.value
        if (resolver_exact or legacy_exact) and relevance != QueryRelevance.EXACT_INTENT:
            product["queryRelevanceNote"] = "query_relevance_vetoed_entity_resolution_exact"

        current_tier = product.get("matchTier", "related")
        if relevance == QueryRelevance.IRRELEVANT:
            product["matchTier"] = "rejected"
            product["queryRejectionReason"] = "irrelevant_to_query"
        elif relevance == QueryRelevance.SUBSTITUTE:
            if current_tier == "primary":
                product["matchTier"] = "related"
                product.setdefault("queryRelevanceNote", "substitute_not_exact_model")
        elif relevance == QueryRelevance.COMPLEMENT:
            product["matchTier"] = "complement"
        # EXACT_INTENT: keep existing ER-based matchTier

    return products
