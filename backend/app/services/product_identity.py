from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Literal

from app.schemas.product import TrueCostProduct
from app.services.relevance import score_exact_product, score_product

MatchTier = Literal["exact", "probable", "related", "rejected"]


_WORD_RE = re.compile(r"\b[\w.-]+\b")
_SIZE_RE = re.compile(r"\b\d+(?:\.\d+)?\s?(?:ml|l|kg|g|gm|mg|mcg|tb|gb|mah|w|mm|cm|inch|inches|pack|pcs|piece|strip|tablet|capsule|capsules|tab|tabs)\b", re.I)
_ROUTE_RE = re.compile(r"\b([A-Za-z]{3}|[A-Za-z][A-Za-z ]{2,})\s+(?:to|->|-)\s+([A-Za-z]{3}|[A-Za-z][A-Za-z ]{2,})\b", re.I)
_GENERIC_WORDS = {
    "wireless", "bluetooth", "headphone", "headphones", "earphone", "earphones", "earbuds", "tws",
    "with", "for", "and", "the", "best", "new", "latest", "tablet", "tablets", "strip", "ride",
    "flight", "hotel", "stay", "room", "loan", "card", "plan", "subscription",
}

_NAME_ALIASES = {
    "mobility": {
        "ubergo": "economy",
        "ola mini": "economy",
        "rapido auto": "auto",
        "bike taxi": "bike",
    },
    "pharmacy": {
        "paracetamol": "acetaminophen",
        "crocin": "paracetamol",
        "dolo": "paracetamol",
    },
    "food": {
        "paneer makhani": "paneer butter masala",
        "dal fry": "dal tadka",
    },
    "travel": {
        "delhi": "DEL",
        "mumbai": "BOM",
    }
}

_CATEGORY_ALIASES = {
    "flights": "travel",
    "travel": "travel",
    "productivity": "services",
    "services": "services",
}
_IMPLIED_BRANDS = {
    "galaxy": "samsung",
    "pixel": "google",
    "iphone": "apple",
    "macbook": "apple",
    "ipad": "apple",
    "apple watch": "apple",
    "airpods": "apple",
}
_MARKETPLACE_BRANDS = {
    "amazon", "flipkart", "meesho", "myntra", "zepto", "blinkit", "swiggy", "bigbasket",
    "tata 1mg", "tata1mg", "pharmeasy", "apollo247", "netmeds", "bankbazaar", "canva",
    "notion", "slack", "figma",
}
_STRICT_VARIANT_TOKENS = {
    "low", "lite", "plus", "pro", "max", "butter", "cashew", "salt", "sodium", "gold", "full", "cream", "atta", "magic", "xt", "mini", "ultra", "air", "anc", "sugar", "free", "almond", "chocolate",
    "classic", "original", "masala", "tomato", "cheese", "onion", "salted", "unsalted", "diet",
    "zero", "dark", "milk", "white", "vanilla", "strawberry", "taaza", "taza", "taja",
    "toned", "standardised", "standardized", "homogenised", "homogenized", "shakti", "deshi",
    "neo", "ace", "millennia",
    "cashback", "platinum", "signature", "infinite", "business", "teams", "organization",
}


@dataclass(frozen=True)
class IdentityResult:
    identity_fingerprint: str
    match_score: float
    match_tier: MatchTier
    rejection_reason: str | None
    identity_factors: dict[str, Any]

    def model_dump(self) -> dict[str, Any]:
        return {
            "identity_fingerprint": self.identity_fingerprint,
            "match_score": self.match_score,
            "match_tier": self.match_tier,
            "rejection_reason": self.rejection_reason,
            "identity_factors": self.identity_factors,
        }


class ProductIdentityEngine:
    """Category-aware identity interface for exact TrueCost comparison.

    This module is intentionally the single public seam for identity decisions.
    It keeps older token scoring as an internal implementation detail while
    adding category factors and stable fingerprints for observability.
    """

    def compare(
        self,
        *,
        user_query: str,
        selected_product: dict[str, Any] | None,
        category: str,
        provider_product: TrueCostProduct,
        observed_metadata: dict[str, Any] | None = None,
    ) -> IdentityResult:
        category_key = self._category_key(category)
        selected_name = str((selected_product or {}).get("name") or (selected_product or {}).get("title") or user_query)
        selected_brand = str((selected_product or {}).get("brand") or "")
        candidate_name = provider_product.name
        candidate_brand = provider_product.brand or ""
        factors = self._factors(category_key, selected_name, selected_brand, candidate_name, candidate_brand, provider_product, observed_metadata or {})

        exact_score = score_exact_product(selected_name or user_query, candidate_name, candidate_brand)
        broad_score = score_product(user_query, candidate_name, candidate_brand)
        score = max(exact_score, broad_score if exact_score >= 0.35 else exact_score)
        hard_reason = self._hard_rejection(category_key, factors)
        if hard_reason:
            return IdentityResult(
                identity_fingerprint=self._fingerprint(category_key, factors["candidate"]),
                match_score=min(score, 0.34),
                match_tier="rejected",
                rejection_reason=hard_reason,
                identity_factors=factors,
            )
        score = max(score, self._identity_evidence_score(category_key, factors))

        if score >= 0.82:
            tier: MatchTier = "exact"
            reason = None
        elif score >= 0.55:
            tier = "probable"
            reason = "Near-exact product identity; verify final variant at provider handoff"
        elif score >= 0.35:
            tier = "related"
            reason = "Related result, not safe enough for exact price comparison"
        else:
            tier = "rejected"
            reason = "Different model/brand/route or weak exact-title coverage"

        return IdentityResult(
            identity_fingerprint=self._fingerprint(category_key, factors["candidate"]),
            match_score=round(float(score), 4),
            match_tier=tier,
            rejection_reason=reason,
            identity_factors=factors,
        )

    def selected_identity(self, *, user_query: str, selected_product: dict[str, Any] | None, category: str) -> dict[str, Any]:
        category_key = self._category_key(category)
        selected_name = str((selected_product or {}).get("name") or (selected_product or {}).get("title") or user_query)
        selected_brand = str((selected_product or {}).get("brand") or "")
        factors = self._selected_factors(category_key, selected_name, selected_brand, selected_product or {})
        return {"identity_fingerprint": self._fingerprint(category_key, factors), "identity_factors": factors}

    def _category_key(self, category: str) -> str:
        key = category.casefold().strip()
        return _CATEGORY_ALIASES.get(key, key)

    def _factors(self, category: str, selected_name: str, selected_brand: str, candidate_name: str, candidate_brand: str, product: TrueCostProduct, metadata: dict[str, Any]) -> dict[str, Any]:
        selected = self._selected_factors(category, selected_name, selected_brand, metadata)
        candidate = self._selected_factors(category, candidate_name, candidate_brand, product.model_dump())
        return {"category": category, "selected": selected, "candidate": candidate}

    def _selected_factors(self, category: str, name: str, brand: str, source: dict[str, Any]) -> dict[str, Any]:
        structured_size = source.get("weight_volume") or source.get("weightVolume") or source.get("pack_size") or source.get("packSize") or ""
        # Apply aliases
        alias_dict = _NAME_ALIASES.get(self._category_key(category), {})
        n = name.casefold()
        for k, v in alias_dict.items():
            if k in n:
                if self._category_key(category) == 'travel' and k in ('delhi', 'mumbai'):
                    name = re.sub(rf"\b{k}\b", v, name, flags=re.I)
                else:
                    name = re.sub(rf"\b{k}\b", v, name, flags=re.I)
        # Normalize travel IATA
        if self._category_key(category) == 'travel':
            name = name.upper()
        
        tokens = self._tokens(f"{brand} {name} {structured_size}")
        raw_brand = self._norm(brand)
        normalized_brand = "" if raw_brand in _MARKETPLACE_BRANDS else raw_brand
        normalized_brand = normalized_brand or self._implied_brand(tokens)
        model_tokens = [token for token in tokens if token not in _GENERIC_WORDS]
        route = self._route(name)
        size_or_strength = [self._norm(match.group(0)).replace(" ", "") for match in _SIZE_RE.finditer(f"{name} {structured_size}")]
        identity_numbers = sorted({token for token in tokens if any(char.isdigit() for char in token)} | set(size_or_strength))
        return {
            "name": name,
            "brand": normalized_brand,
            "model_tokens": model_tokens[:10],
            "identity_numbers": identity_numbers,
            "size_or_strength": size_or_strength,
            "route": route,
            "travel_date": source.get("departure_date") or source.get("checkin_date") or source.get("date"),
            "class_or_plan": source.get("cabin_class") or source.get("room_type") or source.get("plan") or source.get("weight_volume"),
        }

    def _hard_rejection(self, category: str, factors: dict[str, Any]) -> str | None:
        selected = factors["selected"]
        candidate = factors["candidate"]
        selected_numbers = set(selected.get("identity_numbers") or [])
        candidate_numbers = set(candidate.get("identity_numbers") or [])
        if selected_numbers and candidate_numbers and not selected_numbers.issubset(candidate_numbers):
            return "Model, strength, route or variant number does not match"

        selected_route = selected.get("route")
        candidate_route = candidate.get("route")
        if category in {"travel", "mobility"} and selected_route and candidate_route and selected_route != candidate_route:
            return "Route does not match"

        if category in {"grocery", "pharmacy", "shopping", "finance", "services"}:
            selected_tokens = set(selected.get("model_tokens") or [])
            candidate_tokens = set(candidate.get("model_tokens") or [])
            selected_variants = self._variant_signature_tokens(selected_tokens)
            candidate_variants = self._variant_signature_tokens(candidate_tokens)
            if selected_variants != candidate_variants:
                mismatch = selected_variants ^ candidate_variants
                return f"Variant modifier does not match: {', '.join(sorted(mismatch))}"

        selected_brand = selected.get("brand")
        candidate_brand = candidate.get("brand")
        if selected_brand and candidate_brand and selected_brand != candidate_brand:
            shared = set(selected.get("model_tokens") or []) & set(candidate.get("model_tokens") or [])
            if len(shared) < 2:
                return "Brand does not match"
        return None

    def _identity_evidence_score(self, category: str, factors: dict[str, Any]) -> float:
        selected = factors["selected"]
        candidate = factors["candidate"]
        selected_tokens = set(selected.get("model_tokens") or [])
        candidate_tokens = set(candidate.get("model_tokens") or [])
        if not selected_tokens or not candidate_tokens:
            return 0.0
        selected_numbers = set(selected.get("identity_numbers") or [])
        candidate_numbers = set(candidate.get("identity_numbers") or [])
        selected_brand = selected.get("brand")
        candidate_brand = candidate.get("brand")
        shared = selected_tokens & candidate_tokens
        coverage = len(shared) / max(len(selected_tokens), 1)
        number_match = not selected_numbers or selected_numbers.issubset(candidate_numbers)
        brand_match = not selected_brand or not candidate_brand or selected_brand == candidate_brand
        if category in {"shopping", "grocery", "pharmacy", "finance", "services"} and coverage >= 0.75 and number_match and brand_match:
            return 0.86
        if coverage >= 0.55 and number_match and brand_match:
            return 0.58
        return 0.0

    def _implied_brand(self, tokens: list[str]) -> str:
        for token in tokens:
            if token in _IMPLIED_BRANDS:
                return _IMPLIED_BRANDS[token]
        return ""

    def _variant_signature_tokens(self, tokens: set[str]) -> set[str]:
        variants = set(tokens) & _STRICT_VARIANT_TOKENS
        if "gold" in tokens or {"full", "cream"}.issubset(tokens):
            variants.difference_update({"gold", "full", "cream"})
            variants.add("full_cream")
        if {"taaza", "taza", "taja", "toned"} & tokens:
            variants.difference_update({"taaza", "taza", "taja", "toned"})
            variants.add("toned")
        return variants

    def _fingerprint(self, category: str, factors: dict[str, Any]) -> str:
        stable = "|".join([
            category,
            str(factors.get("brand") or ""),
            " ".join(factors.get("model_tokens") or []),
            " ".join(factors.get("identity_numbers") or []),
            " ".join(factors.get("size_or_strength") or []),
            str(factors.get("route") or ""),
            str(factors.get("class_or_plan") or ""),
        ])
        return hashlib.sha256(stable.encode("utf-8")).hexdigest()[:24]

    def _tokens(self, text: str) -> list[str]:
        text = str(text or "").replace("-", " ")
        return [self._norm(match.group(0)) for match in _WORD_RE.finditer(text) if self._norm(match.group(0))]

    def _route(self, text: str) -> dict[str, str] | None:
        match = _ROUTE_RE.search(text)
        if not match:
            return None
        return {"origin": self._norm(match.group(1)), "destination": self._norm(match.group(2))}

    def _norm(self, value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").casefold().strip())


identity_engine = ProductIdentityEngine()
