"""
Retrieval Hypothesis Generator V2
====================================
Step 5 of the pipeline — multi-hypothesis retrieval planning.

V2 CHANGES:
  - Returns typed RetrievalHypothesis objects (not bare list[str])
  - Each hypothesis has confidence, reason, expected_precision, expected_recall
  - H0 now always the corrected/canonical query (not raw) when HIGH confidence
  - hypothesis_queries list maintained for backward compat
"""
from __future__ import annotations

from app.services.search_intelligence.models import (
    QueryIntent,
    QuerySpecificity,
    RetrievalHypothesis,
)


def generate_hypotheses(intent: QueryIntent) -> list[RetrievalHypothesis]:
    """
    Generate ranked retrieval hypotheses for a query.

    H0 — Best canonical query (corrected if HIGH confidence, else normalized)
    H1 — Brand + family + model (structured, without adjectives)
    H2 — Family + model (family-scoped fallback)
    H3 — Raw original query (last-resort recovery)

    The caller uses H0 first. If retrieval returns poor results (no EXACT_INTENT
    candidates), it should try H1, then H2, then H3.
    This preserves latency and provider traffic for the common case.
    """
    pq = intent.parsed
    hypotheses: list[RetrievalHypothesis] = []

    # H0 — Best canonical query
    h0_query = intent.best_retrieval_query()
    hypotheses.append(RetrievalHypothesis(
        query=h0_query,
        confidence=0.95,
        reason="corrected_canonical",
        expected_precision=0.85,
        expected_recall=0.70,
    ))

    # H1 — Structured brand + family + model
    h1_parts: list[str] = []
    if pq.brand:
        h1_parts.append(pq.brand)
    if pq.product_family:
        h1_parts.append(pq.product_family)
    if pq.model:
        h1_parts.append(pq.model)
    if pq.product_type:
        h1_parts.append(pq.product_type)
    h1_query = " ".join(h1_parts).strip()

    if h1_query and h1_query.lower() != h0_query.lower():
        hypotheses.append(RetrievalHypothesis(
            query=h1_query,
            confidence=0.82,
            reason="structured_brand_family_model",
            expected_precision=0.90,
            expected_recall=0.55,
        ))

    # H2 — Family + model (drops brand — wider net)
    if pq.product_family and pq.model:
        h2_query = f"{pq.product_family} {pq.model}"
        if h2_query.lower() not in [h.query.lower() for h in hypotheses]:
            hypotheses.append(RetrievalHypothesis(
                query=h2_query,
                confidence=0.70,
                reason="family_model_only",
                expected_precision=0.75,
                expected_recall=0.65,
            ))

    # H3 — Raw original query (last resort for recovery)
    raw = intent.raw_query
    if raw.lower() not in [h.query.lower() for h in hypotheses]:
        hypotheses.append(RetrievalHypothesis(
            query=raw,
            confidence=0.50,
            reason="raw_fallback",
            expected_precision=0.40,
            expected_recall=0.80,
        ))

    return hypotheses
