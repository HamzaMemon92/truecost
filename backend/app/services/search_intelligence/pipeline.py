"""
Search Intelligence Pipeline V2
=================================
Orchestrates the full query understanding flow.

V2 CHANGES:
  - resolve_aliases() no longer takes parsed_brand argument (simpler API)
  - compute_overall_confidence() replaces max() for confidence aggregation
  - specificity_score() populates QueryIntent.specificity_score float
  - hypotheses are now typed RetrievalHypothesis objects + backward-compat list
  - build_hard_constraints() includes typed constraints
  - Catalog brands loaded at startup for dynamic brand recognition
"""
from __future__ import annotations

import logging

from app.services.search_intelligence.models import (
    CorrectionConfidence,
    QueryIntent,
    QuerySpecificity,
)
from app.services.search_intelligence.query_normalizer import normalize
from app.services.search_intelligence.query_parser import parse, _load_catalog_brands
from app.services.search_intelligence.alias_resolver import (
    resolve_aliases,
    compute_overall_confidence,
    determine_correction_confidence,
)
from app.services.search_intelligence.query_specificity import (
    classify,
    build_hard_constraints,
    specificity_score as compute_specificity_score,
)
from app.services.search_intelligence.hypothesis_generator import generate_hypotheses

logger = logging.getLogger(__name__)


def search_intelligence(raw_query: str, category: str = "Shopping") -> QueryIntent:
    """
    Full search intelligence pipeline.

    Flow:
      1. normalize       — Unicode, commas, case, 5k/lakh expansion
      2. alias_resolver  — Stage A (curated) + Stage B (edit-distance)
      3. parse           — Brand/family/model/type/feature extraction
      4. re-parse        — On corrected query for better model extraction
      5. classify        — Specificity enum + float score
      6. hard_constraints — Typed constraints dict
      7. hypotheses       — Typed retrieval hypothesis list

    Returns QueryIntent — the universal contract passed to all downstream.
    """
    # ── 0. Load catalog brands (no-op if already loaded) ──────────────────
    _load_catalog_brands()

    # ── 1. Normalize ──────────────────────────────────────────────────────
    normalized = normalize(raw_query)

    # ── 2. Alias resolution (Stage A + Stage B) ────────────────────────────
    corrected, corrections = resolve_aliases(normalized, category)
    raw_conf = compute_overall_confidence(corrections)
    correction_confidence = determine_correction_confidence(raw_conf)
    effective_query = corrected if correction_confidence == CorrectionConfidence.HIGH else normalized

    # ── 3. Parse (on corrected query) ─────────────────────────────────────
    parsed = parse(effective_query, category=category)

    # ── 4. If corrected differs from normalized, re-parse on corrected ─────
    # (Correction may reveal brand/model not visible in raw)
    if effective_query.lower() != normalized.lower():
        re_parsed = parse(effective_query, category=category)
        # Prefer re-parsed if it found more information
        if re_parsed.brand and not parsed.brand:
            parsed = re_parsed
        elif re_parsed.model and not parsed.model:
            parsed.model = re_parsed.model
            parsed.model_confidence = re_parsed.model_confidence

    # ── 5. Specificity ────────────────────────────────────────────────────
    specificity = classify(parsed, effective_query)
    spec_score = compute_specificity_score(specificity, parsed)

    # ── 6. Correction confidence ──────────────────────────────────────────

    # ── 7. Hard constraints ────────────────────────────────────────────────
    hard_constraints = build_hard_constraints(parsed)

    # ── 8. Build intent ────────────────────────────────────────────────────
    intent = QueryIntent(
        raw_query=raw_query,
        normalized_query=normalized,
        category=category,
        corrected_query=corrected if corrections else normalized,
        correction_confidence=correction_confidence,
        corrections=corrections,
        parsed=parsed,
        specificity=specificity,
        specificity_score=spec_score,
        hard_constraints=hard_constraints,
    )

    # ── 9. Hypotheses ──────────────────────────────────────────────────────
    hypotheses = generate_hypotheses(intent)
    intent.hypotheses = hypotheses
    intent.hypothesis_queries = [h.query for h in hypotheses]  # backward compat

    # ── 10. UX correction banner ──────────────────────────────────────────
    if corrections and correction_confidence in (
        CorrectionConfidence.HIGH, CorrectionConfidence.MEDIUM
    ):
        corrected_display = corrected.title()
        intent.show_correction_banner = True
        if correction_confidence == CorrectionConfidence.HIGH:
            intent.correction_banner_text = f"Showing results for {corrected_display}"
            intent.correction_alt_text = f"Search instead for '{raw_query}'"
        else:
            intent.correction_banner_text = f"Did you mean {corrected_display}?"
            intent.correction_alt_text = corrected

    logger.debug(
        "SI[%s] raw=%r → corrected=%r | %s (%.2f) | conf=%s | %d corrections",
        category, raw_query, corrected, specificity.value, spec_score,
        correction_confidence.value, len(corrections),
    )

    return intent


def _trivial_intent(raw_query: str, category: str) -> QueryIntent:
    """
    Return a minimal intent for empty/whitespace queries.
    Safe fallback — never errors.
    """
    return QueryIntent(
        raw_query=raw_query,
        normalized_query="",
        category=category,
        corrected_query="",
        correction_confidence=CorrectionConfidence.LOW,
    )
