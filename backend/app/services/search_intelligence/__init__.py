"""
TrueCost Universal Search Intelligence Platform
================================================
Sits above Entity Resolution and below the consumer UI.

Pipeline:
  Raw Query
    → QueryNormalizer
    → CategoryRouter
    → QueryParser (structured attributes)
    → SpecificityClassifier
    → CorrectionEngine (spell / phonetic / alias)
    → HypothesisGenerator (multi-hypothesis retrieval)
    → QueryProductRelevanceClassifier
    → SearchRanker
    → ER (existing)
"""

from app.services.search_intelligence.models import (
    QueryIntent,
    QuerySpecificity,
    QueryRelevance,
    QueryConstraint,
    ConstraintOperator,
    ConstraintHardness,
    AliasRelation,
    ParsedQuery,
    ParsedAttribute,
    RetrievalHypothesis,
    CorrectionConfidence,
    CorrectionRecord,
    SearchIntelligenceResult,
)
from app.services.search_intelligence.pipeline import search_intelligence

__all__ = [
    "QueryIntent",
    "QuerySpecificity",
    "QueryRelevance",
    "ParsedQuery",
    "SearchIntelligenceResult",
    "search_intelligence",
]
