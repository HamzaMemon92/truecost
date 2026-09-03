"""
Universal Query Intelligence — Models
======================================
The QueryIntent is the single most important internal contract in TrueCost.
Everything downstream reads from it.

V2 CHANGES:
  - ParsedQuery → extensible attributes dict (category-agnostic)
  - QueryConstraint → typed with ConstraintOperator (EQ/LTE/GTE/CONTAINS)
  - AliasRelation enum → only SPELLING_VARIANT rewrites query
  - specificity_score: float added to QueryIntent
  - RetrievalHypothesis is a typed dataclass, not bare string
  - All hardcoded category-specific fields removed from ParsedQuery
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class QuerySpecificity(str, Enum):
    """How precise is the user's query?"""
    BROAD = "BROAD"                    # "headphones"
    CATEGORY_FEATURE = "CAT_FEATURE"   # "ANC headphones"
    BRAND = "BRAND"                    # "Noise headphones"
    FAMILY = "FAMILY"                  # "Noise Airwave"
    EXACT_MODEL = "EXACT_MODEL"        # "Noise Airwave Max 6"
    NATURAL_LANGUAGE = "NATURAL_LANG"  # "best headphones under 5000"
    IDENTIFIER = "IDENTIFIER"          # SKU/MPN/EAN — e.g. "WH-1000XM5"


class QueryRelevance(str, Enum):
    """Amazon ESCI-style query-product relevance — separate from ER identity."""
    EXACT_INTENT = "EXACT_INTENT"   # This is precisely what the user asked for
    SUBSTITUTE = "SUBSTITUTE"       # Close alternative / different model
    COMPLEMENT = "COMPLEMENT"       # Goes with what user asked (cases, cables)
    IRRELEVANT = "IRRELEVANT"       # Unrelated result


class CorrectionConfidence(str, Enum):
    HIGH = "HIGH"       # Auto-correct, show "Showing results for X"
    MEDIUM = "MEDIUM"   # Show "Did you mean X?"
    LOW = "LOW"         # Do not rewrite — search raw


class ConstraintOperator(str, Enum):
    """Typed comparison operator for query constraints."""
    EQ = "EQ"             # exact equal  (model = 6, storage = 128GB)
    LTE = "LTE"           # ≤  (price ≤ 5000)
    GTE = "GTE"           # ≥  (departure ≥ 18:00)
    CONTAINS = "CONTAINS" # substring / token match
    IN = "IN"             # value in set


class ConstraintHardness(str, Enum):
    HARD = "HARD"           # Must match — demotion if violated (model, dosage)
    SOFT = "SOFT"           # Strong preference (price, storage)
    PREFERENCE = "PREFERENCE"  # Nice-to-have (color, brand in BROAD queries)


class AliasRelation(str, Enum):
    """
    How the alias relates to its canonical form.
    Only SPELLING_VARIANT and PHONETIC_VARIANT are allowed to rewrite the query.
    Others must only inform discovery / expansion, never replace the original term.
    """
    SPELLING_VARIANT = "SPELLING_VARIANT"    # "noize" → "Noise"
    PHONETIC_VARIANT = "PHONETIC_VARIANT"    # "airmax" → "Airwave Max"
    ABBREVIATION = "ABBREVIATION"            # "BOM" → airport entity
    BRAND_ALIAS = "BRAND_ALIAS"              # "go noise" → "Noise"
    PRODUCT_FAMILY_ALIAS = "PRODUCT_FAMILY_ALIAS"  # "rockerz" → "Rockerz"
    GENERIC_EQUIVALENT = "GENERIC_EQUIVALENT"  # "brufen" HAS_INGREDIENT ibuprofen
    SUBSTITUTION = "SUBSTITUTION"            # "dal fry" ~ "dal tadka"
    RELATED_CONCEPT = "RELATED_CONCEPT"      # "airpods" → earbuds category
    LOCATION_ALIAS = "LOCATION_ALIAS"        # "bombay" → "Mumbai"
    AIRPORT_CODE = "AIRPORT_CODE"            # "BOM" city=Mumbai


# ─────────────────────────────────────────────────────────────────────────────
# Core data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CorrectionRecord:
    """Single token-level correction applied to the query."""
    original_span: str
    corrected_span: str
    confidence: float
    correction_type: str    # use AliasRelation.value
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryConstraint:
    """
    A typed query constraint extracted from the query.
    Replaces the weak dict[str, str] hard_constraints.

    Example:
        attribute="price", operator=LTE, value=5000, hardness=SOFT
        attribute="model", operator=EQ, value="6", hardness=HARD
        attribute="dosage_strength", operator=EQ, value="650mg", hardness=HARD
    """
    attribute: str
    operator: ConstraintOperator
    value: Any
    confidence: float
    hardness: ConstraintHardness
    source: str = "QUERY_EXTRACTOR"  # or "CATALOG", "INFERRED"
    evidence_span: str = ""           # the raw text that produced this constraint


@dataclass
class ParsedAttribute:
    """
    A single extracted attribute — extensible across all categories.
    Category schemas declare which attributes matter for them.

    Shopping:   brand, product_family, model, storage, color, generation
    Pharmacy:   brand, molecule, strength, dosage_form, pack_size
    Travel:     origin, destination, date, cabin, airline
    Mobility:   pickup, destination, ride_class
    Finance:    issuer, product_type, annual_fee
    Food:       dish, restaurant, cuisine, portion
    Grocery:    brand, variant, quantity, unit
    """
    key: str
    value: Any
    normalized_value: Any = None
    confidence: float = 0.0
    source: str = "PARSER"    # "PARSER", "CATALOG", "ALIAS_RESOLVER"
    constraint_strength: ConstraintHardness = ConstraintHardness.SOFT
    evidence_span: str = ""


@dataclass
class ParsedQuery:
    """
    Structured attributes extracted from the raw query.

    V2: Uses extensible attributes dict instead of hardcoded fields.
    Backward-compat convenience properties expose brand/model/etc directly.
    """
    # Core attributes (always extracted, cross-category)
    brand: str | None = None
    brand_confidence: float = 0.0
    product_family: str | None = None
    family_confidence: float = 0.0
    model: str | None = None
    model_confidence: float = 0.0
    product_type: str | None = None
    type_confidence: float = 0.0
    features: list[str] = field(default_factory=list)
    price_constraint: dict[str, float] | None = None  # {"max": 5000, "min": 0}

    # Extensible per-category attributes
    # These hold domain-specific data without polluting the schema:
    # e.g. {"dosage_strength": ParsedAttribute(...), "origin_airport": ParsedAttribute(...)}
    attributes: dict[str, ParsedAttribute] = field(default_factory=dict)

    # Typed constraints derived from the query
    constraints: list[QueryConstraint] = field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        """Get any attribute by key — checks both core fields and attributes dict."""
        core = {
            "brand": self.brand, "product_family": self.product_family,
            "model": self.model, "product_type": self.product_type,
        }
        if key in core:
            return core[key]
        attr = self.attributes.get(key)
        return attr.value if attr else default


@dataclass
class RetrievalHypothesis:
    """
    A candidate retrieval query with reasoning.
    Replaces bare list[str] hypotheses.
    """
    query: str
    confidence: float
    reason: str           # "corrected", "raw", "brand+model", "family+model"
    expected_precision: float = 0.5  # estimated precision of retrieval
    expected_recall: float = 0.5


@dataclass
class QueryIntent:
    """
    The Universal Query Intelligence object.
    One per search request; created by the pipeline; passed to all downstream.
    """
    # ── Raw state ──────────────────────────────────────────────────────────
    raw_query: str
    normalized_query: str
    category: str

    # ── Corrected query ────────────────────────────────────────────────────
    corrected_query: str
    correction_confidence: CorrectionConfidence = CorrectionConfidence.LOW
    corrections: list[CorrectionRecord] = field(default_factory=list)

    # ── Structured understanding ───────────────────────────────────────────
    parsed: ParsedQuery = field(default_factory=ParsedQuery)
    specificity: QuerySpecificity = QuerySpecificity.BROAD
    specificity_score: float = 0.1   # 0.0 (very broad) → 1.0 (exact identifier)

    # ── Typed constraints ──────────────────────────────────────────────────
    # Derived from parsed.constraints — convenience shortcut for ER/ranker
    hard_constraints: dict[str, str] = field(default_factory=dict)
    # e.g. {"brand": "Noise", "model": "6"} — must never be fuzzed away

    # ── Retrieval hypotheses ───────────────────────────────────────────────
    hypotheses: list[RetrievalHypothesis] = field(default_factory=list)
    # Also expose as plain strings for backward compat
    hypothesis_queries: list[str] = field(default_factory=list)

    # ── UX metadata ───────────────────────────────────────────────────────
    show_correction_banner: bool = False
    correction_banner_text: str = ""     # "Showing results for Noise Airwave Max 6"
    correction_alt_text: str = ""        # "Search instead for 'noise airmax 6'"

    def best_retrieval_query(self) -> str:
        """Return the best query to send to providers."""
        if self.correction_confidence == CorrectionConfidence.HIGH:
            return self.corrected_query
        return self.normalized_query

    def to_response_meta(self) -> dict[str, Any]:
        """Serialise for inclusion in API response."""
        return {
            "raw_query": self.raw_query,
            "corrected_query": self.corrected_query,
            "specificity": self.specificity.value,
            "specificity_score": self.specificity_score,
            "correction_confidence": self.correction_confidence.value,
            "show_correction_banner": self.show_correction_banner,
            "correction_banner_text": self.correction_banner_text,
            "correction_alt_text": self.correction_alt_text,
            "hypotheses": [h.query for h in self.hypotheses] if self.hypotheses else self.hypothesis_queries,
            "hard_constraints": self.hard_constraints,
            "parsed": {
                "brand": self.parsed.brand,
                "product_family": self.parsed.product_family,
                "model": self.parsed.model,
                "product_type": self.parsed.product_type,
                "features": self.parsed.features,
                "price_constraint": self.parsed.price_constraint,
            },
            "corrections": [
                {
                    "original": c.original_span,
                    "corrected": c.corrected_span,
                    "confidence": c.confidence,
                    "type": c.correction_type,
                }
                for c in self.corrections
            ],
        }


@dataclass
class SearchIntelligenceResult:
    """Full output from the search_intelligence pipeline for a single query."""
    intent: QueryIntent
    query_relevance_scores: dict[str, QueryRelevance] = field(default_factory=dict)
