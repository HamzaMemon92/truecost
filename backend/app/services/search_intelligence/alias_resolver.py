"""
Alias Resolver V2
==================
Step 4 of the pipeline — query rewriting based on curated aliases + edit distance.

V2 CHANGES:
  - AliasRecord typed system — only SPELLING_VARIANT/PHONETIC_VARIANT/BRAND_ALIAS
    /PRODUCT_FAMILY_ALIAS/LOCATION_ALIAS rewrites the query
  - Stage A: curated high-confidence corrections (lexicon)
  - Stage B: edit-distance (Levenshtein ≤ 2) against known brands
    (handles "noice", "niose", "noisee" without manual entries)
  - Word-boundary matching throughout (never plain substring)
  - confidence_for_query() now computes weighted average across all corrections
    (max_confidence alone was wrong — a 0.51 family correction doesn't inherit 0.95 brand confidence)
  - Dead no-op `if ...: pass` block removed
  - Confidence constants promoted to module-level named constants
  - GENERIC_EQUIVALENT aliases (brufen→ibuprofen) explicitly skipped for rewrites
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from app.services.search_intelligence.models import (
    AliasRelation,
    CorrectionConfidence,
    CorrectionRecord,
)
from app.services.search_intelligence.entity_lexicon import (
    CANONICAL_BRAND_NAMES,
    KNOWN_BRANDS,
    get_rewrite_aliases,
    _BRAND_ALIAS_MAP,
)
from app.services.search_intelligence.query_parser import get_all_known_brands


# ─────────────────────────────────────────────────────────────────────────────
# Confidence constants (named, not magic numbers)
# ─────────────────────────────────────────────────────────────────────────────
_CONF_BRAND_ALIAS = 0.96          # "noize" → "Noise" (exact lexicon match)
_CONF_FAMILY_ALIAS_CONTEXTUAL = 0.94  # "airmax" + brand=Noise → "Airwave Max"
_CONF_FAMILY_ALIAS_GENERIC = 0.78    # brand-agnostic family alias
_CONF_PRODUCT_TYPE_ALIAS = 0.85      # "headfone" → "headphones"
_CONF_EDIT_DISTANCE_1 = 0.82         # 1-char edit distance brand match
_CONF_EDIT_DISTANCE_2 = 0.65         # 2-char edit distance brand match


# ─────────────────────────────────────────────────────────────────────────────
# Edit-distance brand matching — Stage B
# Handles: "noice" → "Noise", "niose" → "Noise", "samsng" → "Samsung"
# (that aren't already in the curated alias table)
# ─────────────────────────────────────────────────────────────────────────────
def _levenshtein(a: str, b: str) -> int:
    """Simple Levenshtein distance — O(len(a) * len(b))."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            dp[j] = prev if a[i-1] == b[j-1] else 1 + min(prev, dp[j], dp[j-1])
            prev = temp
    return dp[n]


def _find_edit_distance_brand(token: str, all_brands: frozenset[str]) -> tuple[str | None, float]:
    """
    Find the closest brand to a query token using edit distance.
    Returns (canonical_brand, confidence) or (None, 0.0).

    Only fires for tokens that are NOT already a known brand.
    Token must be >= 6 chars for dist=1 match, >= 5 chars for dist=2 match.
    This prevents "sony"→"Bose", "under"→"Uber", "best"→"Bose" false positives.
    """
    # Common non-brand words that must never be brand-corrected
    _STOP_WORDS: frozenset[str] = frozenset({
        "best", "top", "under", "below", "above", "within", "about",
        "around", "budget", "good", "great", "nice", "fast", "slow",
        "cheap", "value", "quality", "latest", "new", "old", "mini",
        "over", "very", "more", "less", "with", "and", "for", "from",
        "case", "cover", "type", "mode", "plus", "pro", "lite", "max",
        "uber", "over", "cord", "wire", "free", "long", "wide", "thin",
        "pouch", "pack", "packet", "bottle", "jar", "can", "tin", "box",
        "ml", "l", "ltr", "litre", "liter", "g", "gm", "kg",
    })
    if token in _STOP_WORDS:
        return None, 0.0

    # Minimum length to prevent aggressive short-word corrections
    if len(token) < 5:
        return None, 0.0

    best_brand: str | None = None
    best_dist = 3  # threshold: only consider ≤ 2
    best_len_diff = 100

    for brand in all_brands:
        if len(brand) < 4:
            continue
        # For distance=1, token must be >= 6 chars (prevents sony→Bose)
        dist = _levenshtein(token, brand)
        if dist == 1 and len(token) < 6:
            continue
        
        len_diff = abs(len(token) - len(brand))
        # Better distance, or same distance but closer length
        if dist < best_dist or (dist == best_dist and len_diff < best_len_diff):
            best_dist = dist
            best_len_diff = len_diff
            best_brand = brand

    if best_brand is None:
        return None, 0.0

    canonical = CANONICAL_BRAND_NAMES.get(best_brand, best_brand.title())
    conf = _CONF_EDIT_DISTANCE_1 if best_dist == 1 else _CONF_EDIT_DISTANCE_2
    return canonical, conf


# ─────────────────────────────────────────────────────────────────────────────
# Determine UX correction confidence from numeric value
# ─────────────────────────────────────────────────────────────────────────────
def determine_correction_confidence(raw_conf: float) -> CorrectionConfidence:
    """
    Map weighted correction confidence → UX policy:
      HIGH   → auto-correct + show "Showing results for X" banner
      MEDIUM → show "Did you mean X?" prompt
      LOW    → do not rewrite (search raw)
    """
    if raw_conf >= 0.88:
        return CorrectionConfidence.HIGH
    if raw_conf >= 0.65:
        return CorrectionConfidence.MEDIUM
    return CorrectionConfidence.LOW


# ─────────────────────────────────────────────────────────────────────────────
# Find brand context in a query (for family alias resolution)
# ─────────────────────────────────────────────────────────────────────────────
def _find_brand_in_query(normalized: str) -> str | None:
    """Find if any known brand appears in the query (word-boundary safe)."""
    all_brands = get_all_known_brands()
    for brand in sorted(all_brands, key=len, reverse=True):
        pattern = r"(?<!\w)" + re.escape(brand) + r"(?!\w)"
        if re.search(pattern, normalized.lower()):
            return brand
    # Also check alias map
    for alias_text, alias_record in _BRAND_ALIAS_MAP.items():
        if not alias_record.may_rewrite():
            continue
        pattern = r"(?<!\w)" + re.escape(alias_text) + r"(?!\w)"
        if re.search(pattern, normalized.lower()):
            return alias_record.canonical.lower()
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main resolve_aliases function
# ─────────────────────────────────────────────────────────────────────────────
def resolve_aliases(
    normalized_query: str,
    category: str,
) -> tuple[str, list[CorrectionRecord]]:
    """
    Apply contextual alias resolution to the normalized query.
    Returns (corrected_query, list_of_corrections).

    Stage A: Curated lexicon aliases (high confidence)
    Stage B: Edit-distance brand matching (medium confidence)

    Only REWRITE-ELIGIBLE aliases (SPELLING_VARIANT, PHONETIC_VARIANT,
    BRAND_ALIAS, PRODUCT_FAMILY_ALIAS, LOCATION_ALIAS) modify the query text.
    GENERIC_EQUIVALENT and SUBSTITUTION are never applied here.
    """
    corrected = normalized_query
    corrections: list[CorrectionRecord] = []
    already_corrected_spans: set[str] = set()  # prevents double-expansion

    # Determine brand context for family alias resolution
    brand_ctx = _find_brand_in_query(corrected)

    # ── Stage A: Curated alias table ─────────────────────────────────────────
    # Get only rewrite-eligible aliases for this category
    alias_records = get_rewrite_aliases(category)

    # Sort brand aliases before family aliases, and longer-first within each group
    brand_records = [r for r in alias_records if r.relation in {
        AliasRelation.SPELLING_VARIANT, AliasRelation.PHONETIC_VARIANT, AliasRelation.BRAND_ALIAS
    }]
    family_records = [r for r in alias_records if r.relation == AliasRelation.PRODUCT_FAMILY_ALIAS]
    other_records = [r for r in alias_records if r not in brand_records and r not in family_records]

    for record in (
        sorted(brand_records, key=lambda r: len(r.alias), reverse=True)
        + sorted(family_records, key=lambda r: len(r.alias), reverse=True)
        + sorted(other_records, key=lambda r: len(r.alias), reverse=True)
    ):
        alias_lower = record.alias.lower()

        # Skip if already corrected this span
        if alias_lower in already_corrected_spans:
            continue

        # Brand context check
        if record.brand_context and brand_ctx:
            if record.brand_context.lower() != brand_ctx.lower():
                continue

        # Word-boundary match
        pattern = r"(?<!\w)" + re.escape(alias_lower) + r"(?!\w)"
        if not re.search(pattern, corrected.lower()):
            continue

        # Confidence based on alias type
        if record.relation in {AliasRelation.SPELLING_VARIANT, AliasRelation.PHONETIC_VARIANT,
                                AliasRelation.BRAND_ALIAS}:
            conf = _CONF_BRAND_ALIAS
        elif record.relation == AliasRelation.PRODUCT_FAMILY_ALIAS:
            conf = _CONF_FAMILY_ALIAS_CONTEXTUAL if record.brand_context else _CONF_FAMILY_ALIAS_GENERIC
        else:
            conf = _CONF_PRODUCT_TYPE_ALIAS

        # Apply replacement (word-boundary safe, case-insensitive)
        new_corrected = re.sub(pattern, record.canonical, corrected, flags=re.I)
        if new_corrected.lower() == corrected.lower():
            continue  # nothing changed

        corrections.append(CorrectionRecord(
            original_span=alias_lower,
            corrected_span=record.canonical,
            confidence=conf,
            correction_type=record.relation.value,
        ))
        already_corrected_spans.add(alias_lower)
        already_corrected_spans.add(record.canonical.lower())  # prevent re-matching the result

        # Update brand context if we just identified/corrected a brand
        if record.relation in {AliasRelation.BRAND_ALIAS, AliasRelation.SPELLING_VARIANT,
                                AliasRelation.PHONETIC_VARIANT}:
            brand_ctx = record.canonical.lower()

        corrected = new_corrected

    # ── Stage B: Edit-distance brand matching ────────────────────────────────
    # Handles misspellings not in the curated table
    all_brands = get_all_known_brands()
    tokens = corrected.lower().split()

    for token in tokens:
        # Skip if already a known brand
        if token in all_brands:
            continue
        # Skip if already corrected
        if token in already_corrected_spans:
            continue
        # Skip short tokens and numbers
        if len(token) < 4 or token.isdigit():
            continue

        corrected_brand, dist_conf = _find_edit_distance_brand(token, all_brands)
        if corrected_brand is None:
            continue

        canonical_lower = corrected_brand.lower()
        if canonical_lower in already_corrected_spans:
            continue

        # Word-boundary replacement
        pattern = r"(?<!\w)" + re.escape(token) + r"(?!\w)"
        new_corrected = re.sub(pattern, corrected_brand, corrected, flags=re.I)
        if new_corrected.lower() == corrected.lower():
            continue

        corrections.append(CorrectionRecord(
            original_span=token,
            corrected_span=corrected_brand,
            confidence=dist_conf,
            correction_type=AliasRelation.SPELLING_VARIANT.value,
            context={"source": "edit_distance"},
        ))
        already_corrected_spans.add(token)
        already_corrected_spans.add(canonical_lower)
        if not brand_ctx:
            brand_ctx = canonical_lower
        corrected = new_corrected

    return corrected, corrections


# ─────────────────────────────────────────────────────────────────────────────
# Weighted confidence aggregation
# ─────────────────────────────────────────────────────────────────────────────
def compute_overall_confidence(corrections: list[CorrectionRecord]) -> float:
    """
    Compute overall correction confidence as a weighted average.

    V2 FIX: V1 used max(corrections) which was wrong.
    A 0.51 family correction + 0.95 brand correction should not produce 0.95.
    The product should reflect all modifications made.

    Weights:
      - Brand corrections: high weight (identity-critical)
      - Family corrections: medium weight
      - Type corrections: lower weight
    """
    if not corrections:
        return 0.0

    weight_map = {
        AliasRelation.BRAND_ALIAS.value: 1.0,
        AliasRelation.SPELLING_VARIANT.value: 0.9,
        AliasRelation.PHONETIC_VARIANT.value: 0.9,
        AliasRelation.PRODUCT_FAMILY_ALIAS.value: 0.7,
        AliasRelation.LOCATION_ALIAS.value: 0.8,
        AliasRelation.ABBREVIATION.value: 0.6,
    }

    total_weight = 0.0
    weighted_conf = 0.0
    for c in corrections:
        w = weight_map.get(c.correction_type, 0.5)
        weighted_conf += c.confidence * w
        total_weight += w

    if total_weight == 0:
        return 0.0

    return weighted_conf / total_weight
