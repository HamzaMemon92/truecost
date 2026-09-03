from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.schemas.product import ProviderPrice, TrueCostProduct
from app.services.product_identity import identity_engine
from app.services.llm_extractor import extractor


class EntityType(str, Enum):
    PRODUCT = "PRODUCT"
    GROCERY_SKU = "GROCERY_SKU"


class ResolutionDecision(str, Enum):
    EXACT = "EXACT"
    PROBABLE = "PROBABLE"
    RELATED = "RELATED"
    REJECTED = "REJECTED"


class EvidenceResult(str, Enum):
    MATCH = "MATCH"
    CONFLICT = "CONFLICT"
    MISSING_SELECTED = "MISSING_SELECTED"
    MISSING_CANDIDATE = "MISSING_CANDIDATE"
    INFO = "INFO"


class ExtractedAttribute(BaseModel):
    name: str
    normalized_value: str
    raw_value: str | None = None
    source: str = "deterministic"
    identity_weight: str = "unknown"


class BoundedLLMAttributeOutput(BaseModel):
    attributes: list[ExtractedAttribute] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)


@dataclass(frozen=True)
class IdentityContract:
    resolver_version: str
    entity_type: EntityType
    critical: tuple[str, ...]
    variant: tuple[str, ...] = ()
    informational: tuple[str, ...] = ()
    generic_terms: tuple[str, ...] = ()
    llm_extractable: tuple[str, ...] = ()
    category_aliases: tuple[str, ...] = ()
    rollout_state: str = "shadow"


@dataclass
class SourceRecord:
    provider: str
    product: TrueCostProduct
    observed_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderOfferV3:
    offer_id: str
    provider: str
    provider_sku: str | None
    entity_id: str
    price: float | None
    availability: str | None
    freshness: dict[str, Any]
    raw_offer: dict[str, Any]

    def model_dump(self) -> dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "provider": self.provider,
            "provider_sku": self.provider_sku,
            "entity_id": self.entity_id,
            "price": self.price,
            "availability": self.availability,
            "freshness": self.freshness,
            "raw_offer": self.raw_offer,
        }


@dataclass
class CanonicalEntityV3:
    entity_id: str
    entity_type: EntityType
    attributes: dict[str, Any]
    unknown_attributes: list[dict[str, Any]]

    def model_dump(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "attributes": self.attributes,
            "unknown_attributes": self.unknown_attributes,
        }


@dataclass
class ResolutionResultV3:
    decision: ResolutionDecision
    confidence: float
    canonical_entity: CanonicalEntityV3
    provider_offer: ProviderOfferV3
    evidence: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]
    missing_factors: list[dict[str, Any]]
    resolver_version: str
    legacy_decision: str | None = None
    disagreement: bool = False
    llm_extraction: dict[str, Any] | None = None
    selected_entity: CanonicalEntityV3 | None = None
    candidate_entity: CanonicalEntityV3 | None = None

    def model_dump(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "confidence": self.confidence,
            "canonical_entity": self.canonical_entity.model_dump(),
            "selected_entity": (self.selected_entity or self.canonical_entity).model_dump(),
            "candidate_entity": (self.candidate_entity or self.canonical_entity).model_dump(),
            "provider_offer": self.provider_offer.model_dump(),
            "evidence": self.evidence,
            "conflicts": self.conflicts,
            "missing_factors": self.missing_factors,
            "resolver_version": self.resolver_version,
            "legacy_decision": self.legacy_decision,
            "disagreement": self.disagreement,
            "llm_extraction": self.llm_extraction,
        }


_WORD_RE = re.compile(r"\b[\w.-]+\b")
_SIZE_RE = re.compile(r"\b(?P<value>\d+(?:\.\d+)?)\s?(?P<unit>ml|l|kg|g|gm|mg|mcg|tb|gb|mah|w|mm|cm|inch|inches|pack|pcs|piece|pieces)\b", re.I)
_IDENTIFIER_KEYS = ("gtin", "ean", "upc", "isbn", "mpn")
_PROVIDER_ID_KEYS = ("provider_sku", "sku", "sku_id", "source_id", "product_id")
_MARKETPLACE_BRANDS = {
    "amazon", "flipkart", "meesho", "myntra", "zepto", "blinkit", "swiggy", "bigbasket",
}


_CONTRACTS_PATH = Path(__file__).with_name("entity_resolution_contracts.json")


def _contract_from_dict(raw: dict[str, Any]) -> IdentityContract:
    try:
        entity_type = EntityType(str(raw["entity_type"]))
    except Exception as exc:
        raise ValueError(f"Invalid entity type in resolution contract: {raw.get('entity_type')}") from exc

    return IdentityContract(
        resolver_version=str(raw["resolver_version"]),
        entity_type=entity_type,
        critical=tuple(str(item) for item in raw.get("critical", ())),
        variant=tuple(str(item) for item in raw.get("variant", ())),
        informational=tuple(str(item) for item in raw.get("informational", ())),
        generic_terms=tuple(str(item).casefold() for item in (raw.get("ignored_descriptive_terms") or raw.get("generic_terms") or ())),
        llm_extractable=tuple(str(item) for item in raw.get("llm_extractable", ())),
        category_aliases=tuple(str(item).casefold().strip() for item in raw.get("category_aliases", ())),
        rollout_state=str(raw.get("rollout_state") or "shadow"),
    )


def _load_data_driven_contracts() -> dict[str, IdentityContract]:
    """Load versioned identity contracts from data, not runtime product patches."""
    try:
        payload = json.loads(_CONTRACTS_PATH.read_text(encoding="utf-8"))
        contracts = [_contract_from_dict(item) for item in payload.get("contracts", [])]
        return {contract.resolver_version: contract for contract in contracts}
    except FileNotFoundError:
        return {}
    except Exception as exc:
        raise RuntimeError(f"Entity resolution contract file is invalid: {_CONTRACTS_PATH}") from exc


_DATA_DRIVEN_CONTRACTS = _load_data_driven_contracts()


_SHOPPING_FALLBACK_CONTRACT = IdentityContract(
    resolver_version="shopping.product.v3",
    entity_type=EntityType.PRODUCT,
    critical=("brand", "model_signature", "identity_numbers"),
    variant=("storage", "color", "variant_signature"),
    informational=("title_terms",),
    generic_terms=(
        "with", "for", "and", "the", "new", "latest", "wireless", "bluetooth", "headphone",
        "headphones", "earphone", "earphones", "earbuds", "tws",
    ),
    llm_extractable=("storage", "color", "variant_signature", "model_signature", "identity_numbers", "pack_size"),
    category_aliases=("shopping",),
    rollout_state="fallback",
)

_GROCERY_FALLBACK_CONTRACT = IdentityContract(
    resolver_version="grocery.sku.v3",
    entity_type=EntityType.GROCERY_SKU,
    critical=("brand", "product_signature", "pack_size"),
    variant=("variant_signature",),
    informational=("title_terms",),
    generic_terms=(
        "with", "for", "and", "the", "pack", "pcs", "piece", "pieces",
    ),
    llm_extractable=("variant_signature", "product_signature", "pack_size"),
    category_aliases=("grocery",),
    rollout_state="fallback",
)


SHOPPING_CONTRACT = _DATA_DRIVEN_CONTRACTS.get("shopping.product.v3", _SHOPPING_FALLBACK_CONTRACT)
GROCERY_CONTRACT = _DATA_DRIVEN_CONTRACTS.get("grocery.sku.v3", _GROCERY_FALLBACK_CONTRACT)


FOOD_CONTRACT = IdentityContract(
    resolver_version="food.delivery.v1",
    entity_type=EntityType.PRODUCT,
    critical=("restaurant_name", "dish_name"),
    variant=("cuisine", "price", "eta"),
)

PHARMACY_CONTRACT = IdentityContract(
    resolver_version="pharmacy.medicine.v1",
    entity_type=EntityType.PRODUCT,
    critical=("medicine_name", "dosage"),
    variant=("brand", "pack_size", "price"),
)

MOBILITY_CONTRACT = IdentityContract(
    resolver_version="mobility.ride.v1",
    entity_type=EntityType.PRODUCT,
    critical=("ride_class",),
    variant=("price", "eta", "capacity"),
)

TRAVEL_CONTRACT = IdentityContract(
    resolver_version="travel.flight.v1",
    entity_type=EntityType.PRODUCT,
    critical=("origin", "destination", "date"),
    variant=("airline", "price", "duration", "stops"),
)

FINANCE_CONTRACT = IdentityContract(
    resolver_version="finance.product.v1",
    entity_type=EntityType.PRODUCT,
    critical=("product_type",),
    variant=("interest_rate", "tenure", "benefits"),
)

PRODUCTIVITY_CONTRACT = IdentityContract(
    resolver_version="productivity.saas.v1",
    entity_type=EntityType.PRODUCT,
    critical=("tool_name",),
    variant=("tier", "price", "features"),
)

CONTRACT_REGISTRY = {
    SHOPPING_CONTRACT.resolver_version: SHOPPING_CONTRACT,
    GROCERY_CONTRACT.resolver_version: GROCERY_CONTRACT,
    FOOD_CONTRACT.resolver_version: FOOD_CONTRACT,
    PHARMACY_CONTRACT.resolver_version: PHARMACY_CONTRACT,
    MOBILITY_CONTRACT.resolver_version: MOBILITY_CONTRACT,
    TRAVEL_CONTRACT.resolver_version: TRAVEL_CONTRACT,
    FINANCE_CONTRACT.resolver_version: FINANCE_CONTRACT,
    PRODUCTIVITY_CONTRACT.resolver_version: PRODUCTIVITY_CONTRACT,
}

_CATEGORY_CONTRACT_INDEX = {
    alias: contract
    for contract in (SHOPPING_CONTRACT, GROCERY_CONTRACT)
    for alias in contract.category_aliases
}

def get_contract_by_version(version: str) -> IdentityContract | None:
    return CONTRACT_REGISTRY.get(version)



EntityCandidate = SourceRecord
CanonicalEntity = CanonicalEntityV3
ProviderOffer = ProviderOfferV3
ResolutionEvidence = dict[str, Any]
ResolutionConflict = dict[str, Any]
ResolutionReport = ResolutionResultV3


class EntityOfferResolutionService:
    """Evidence-first entity + offer resolver for exact TrueCost comparison.

    v3 intentionally resolves the entity before comparing offers. The current
    legacy identity engine is called only for shadow/rollback disagreement data.
    """

    def supports(self, category: str) -> bool:
        return self._contract(category) is not None

    def selected_entity(self, *, query: str, selected_product: dict[str, Any] | None, category: str) -> dict[str, Any]:
        contract = self._contract(category)
        if contract is None:
            return identity_engine.selected_identity(user_query=query, selected_product=selected_product, category=category)
        attrs = self._extract_attributes(contract, selected_product or {"name": query}, query=query, provider="")
        entity = self._canonical_entity(contract, attrs)
        return {
            "identity_fingerprint": entity.entity_id,
            "entity_id": entity.entity_id,
            "entity_type": entity.entity_type.value,
            "attributes": entity.attributes,
            "unknown_attributes": entity.unknown_attributes,
            "resolver_version": contract.resolver_version,
        }

    def resolve(
        self,
        *,
        query: str,
        selected_product: dict[str, Any] | None,
        category: str,
        source_record: SourceRecord,
        enable_llm_extraction: bool = False,
    ) -> ResolutionResultV3:
        contract = self._contract(category)
        if contract is None:
            raise ValueError(f"Entity resolver v3 does not support category: {category}")

        selected_attrs = self._extract_attributes(contract, selected_product or {"name": query}, query=query, provider="")
        candidate_attrs = self._extract_attributes(contract, source_record.product.model_dump(), query=source_record.product.name, provider=source_record.provider)
        llm_payload = None
        evidence, conflicts, missing = self._compare_attributes(contract, selected_attrs, candidate_attrs)
        decision, confidence = self._decision(contract, evidence, conflicts, missing)
        
        # Only call LLM if there's no critical conflict and we have missing factors
        # wait, if decision is REJECTED due to conflicts, we shouldn't call LLM.
        # if decision is EXACT, we shouldn't call LLM.
        # if decision is PROBABLE or REJECTED due to MISSING, then call LLM.
        if enable_llm_extraction and decision != ResolutionDecision.EXACT and not conflicts:
            llm_payload = self._bounded_llm_attribute_extraction(contract, selected_attrs, candidate_attrs)
            if llm_payload and llm_payload.get("success") and llm_payload.get("attributes_extracted", 0) > 0:
                # Recompute
                evidence, conflicts, missing = self._compare_attributes(contract, selected_attrs, candidate_attrs)
                decision, confidence = self._decision(contract, evidence, conflicts, missing)

        
        # LLM cannot directly produce final EXACT authority
        if decision == ResolutionDecision.EXACT and llm_payload and llm_payload.get("success") and llm_payload.get("attributes_extracted", 0) > 0:
            decision = ResolutionDecision.PROBABLE
            confidence = min(confidence, 0.7)
            
        selected_entity = self._canonical_entity(contract, selected_attrs)
        candidate_entity = self._canonical_entity(contract, candidate_attrs)
        canonical_source = candidate_attrs if decision == ResolutionDecision.EXACT else selected_attrs
        entity = self._canonical_entity(contract, canonical_source)
        offer = self._provider_offer(source_record, entity.entity_id)
        legacy = identity_engine.compare(
            user_query=query,
            selected_product=selected_product or {"name": query},
            category=category,
            provider_product=source_record.product,
            observed_metadata=source_record.observed_metadata,
        )
        legacy_decision = self._legacy_decision(legacy.match_tier)
        return ResolutionResultV3(
            decision=decision,
            confidence=confidence,
            canonical_entity=entity,
            provider_offer=offer,
            evidence=evidence,
            conflicts=conflicts,
            missing_factors=missing,
            resolver_version=contract.resolver_version,
            legacy_decision=legacy_decision,
            disagreement=legacy_decision != decision.value,
            llm_extraction=llm_payload,
            selected_entity=selected_entity,
            candidate_entity=candidate_entity,
        )

    def _contract(self, category: str) -> IdentityContract | None:
        key = str(category or "").casefold().strip()
        if key in _CATEGORY_CONTRACT_INDEX:
            return _CATEGORY_CONTRACT_INDEX[key]
        if key in ("food", "food delivery"): return FOOD_CONTRACT
        if key == "pharmacy": return PHARMACY_CONTRACT
        if key in ("mobility", "rides"): return MOBILITY_CONTRACT
        if key in ("travel", "flights"): return TRAVEL_CONTRACT
        if key in ("finance", "financial products"): return FINANCE_CONTRACT
        if key in ("productivity", "saas", "services"): return PRODUCTIVITY_CONTRACT
        return None

    def _extract_attributes(self, contract: IdentityContract, source: dict[str, Any], *, query: str, provider: str) -> dict[str, Any]:
        source = dict(source or {})
        unknown = source.get("unknown_attributes", {})
        if isinstance(unknown, dict):
            source.update(unknown)
        name = str(source.get("name") or source.get("title") or query or "")
        brand = self._normalize_brand(str(source.get("brand") or ""), name=name, provider=provider)
        tokens = self._tokens(f"{brand} {name}")
        size = self._size(name, source)
        identifiers = self._identifiers(source)
        provider_ids = self._provider_ids(source)
        stripped = self._strip_size_tokens(tokens)
        stripped = [token for token in stripped if token not in contract.generic_terms and token != brand]
        attrs: dict[str, Any] = {
            "brand": brand,
            "title_terms": sorted(set(tokens)),
            "identity_numbers": sorted({token for token in stripped if any(char.isdigit() for char in token)}),
            "identifiers": identifiers,
            "provider_scoped_ids": provider_ids,
        }
        if contract.entity_type == EntityType.GROCERY_SKU:
            attrs["pack_size"] = size
            attrs["product_signature"] = self._signature([token for token in stripped if not any(char.isdigit() for char in token)])
            attrs["variant_signature"] = self._signature([token for token in stripped if not any(char.isdigit() for char in token)][2:])
        else:
            attrs["storage"] = self._storage(name, source)
            attrs["color"] = self._color(source)
            color_tokens = set(self._tokens(attrs["color"]))
            attrs["model_signature"] = self._signature([token for token in stripped if token not in {attrs["storage"]} and token not in color_tokens])
            attrs["variant_signature"] = self._signature([token for token in stripped if token not in set(attrs["identity_numbers"])])
        attrs["unknown_attributes"] = self._unknown_attributes(source, known_keys=set(attrs) | {"id", "name", "title", "brand", "category", "prices", "image_url", "imageUrl", "weight_volume", "weightVolume", "color", "storage", "capacity"})
        return attrs

    def _compare_attributes(self, contract: IdentityContract, selected: dict[str, Any], candidate: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        evidence: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        missing: list[dict[str, Any]] = []
        strong_selected = selected.get("identifiers") or {}
        strong_candidate = candidate.get("identifiers") or {}
        shared_identifier = {
            key: strong_selected[key]
            for key in strong_selected.keys() & strong_candidate.keys()
            if strong_selected[key] and strong_selected[key] == strong_candidate[key]
        }
        for key in sorted(strong_selected.keys() & strong_candidate.keys()):
            result = EvidenceResult.MATCH if strong_selected[key] == strong_candidate[key] else EvidenceResult.CONFLICT
            item = {"factor": key, "selected": strong_selected[key], "candidate": strong_candidate[key], "result": result.value, "source": "strong_identifier"}
            evidence.append(item)
            if result == EvidenceResult.CONFLICT:
                conflicts.append(item)
        if shared_identifier:
            evidence.append({"factor": "strong_identifier", "selected": shared_identifier, "candidate": shared_identifier, "result": EvidenceResult.MATCH.value, "source": "identifier_hierarchy"})
            return evidence, conflicts, missing

        for factor in (*contract.critical, *contract.variant):
            selected_value = selected.get(factor)
            candidate_value = candidate.get(factor)
            if self._empty(selected_value):
                missing.append({"factor": factor, "side": "selected", "result": EvidenceResult.MISSING_SELECTED.value})
                continue
            if self._empty(candidate_value):
                missing.append({"factor": factor, "side": "candidate", "result": EvidenceResult.MISSING_CANDIDATE.value})
                continue
            if factor == "brand" and self._norm(selected_value) != self._norm(candidate_value) and self._norm(selected_value) in set(candidate.get("title_terms") or []):
                missing.append({"factor": factor, "side": "selected", "result": EvidenceResult.MISSING_SELECTED.value, "reason": "Selected text appears to contain product family, not explicit brand"})
                continue
            compatible = self._compatible(factor, selected_value, candidate_value, contract=contract, selected_brand=selected.get("brand"))
            item = {"factor": factor, "selected": selected_value, "candidate": candidate_value, "result": EvidenceResult.MATCH.value if compatible else EvidenceResult.CONFLICT.value, "source": "structured_attribute"}
            evidence.append(item)
            if not compatible:
                conflicts.append(item)
        return evidence, conflicts, missing

    def _decision(self, contract: IdentityContract, evidence: list[dict[str, Any]], conflicts: list[dict[str, Any]], missing: list[dict[str, Any]]) -> tuple[ResolutionDecision, float]:
        if conflicts:
            return ResolutionDecision.REJECTED, 0.12
        
        has_strong = any(item.get("factor") == "strong_identifier" and item.get("result") == EvidenceResult.MATCH.value for item in evidence)
        if has_strong:
            return ResolutionDecision.EXACT, 0.99
            
        critical_factors = set(contract.critical)
        selected_missing = {item["factor"] for item in missing if item.get("factor") in critical_factors and item.get("side") == "selected"}
        required_critical = critical_factors - selected_missing
        matched_critical = {item["factor"] for item in evidence if item.get("factor") in critical_factors and item.get("result") == EvidenceResult.MATCH.value}
        missing_critical = {item["factor"] for item in missing if item.get("factor") in required_critical}
        if required_critical and matched_critical.issuperset(required_critical):
            return ResolutionDecision.EXACT, round(min(0.99, 0.78 + (len(evidence) * 0.035)), 4)
        if matched_critical and len(matched_critical) >= max(1, len(required_critical) - 1) and len(missing_critical) <= 1:
            return ResolutionDecision.PROBABLE, 0.68
        if evidence:
            return ResolutionDecision.RELATED, 0.42
        return ResolutionDecision.REJECTED, 0.0

    def _canonical_entity(self, contract: IdentityContract, attrs: dict[str, Any]) -> CanonicalEntityV3:
        stable_attrs = {
            key: attrs.get(key)
            for key in (*contract.critical, *contract.variant)
            if not self._empty(attrs.get(key))
        }
        stable = f"{contract.entity_type.value}|{contract.resolver_version}|{stable_attrs}"
        return CanonicalEntityV3(
            entity_id=f"tc_entity_{hashlib.sha256(stable.encode('utf-8')).hexdigest()[:24]}",
            entity_type=contract.entity_type,
            attributes=stable_attrs,
            unknown_attributes=[item.model_dump() if isinstance(item, ExtractedAttribute) else item for item in attrs.get("unknown_attributes", [])],
        )

    def _provider_offer(self, source_record: SourceRecord, entity_id: str) -> ProviderOfferV3:
        product = source_record.product
        offers = product.prices or []
        first = offers[0] if offers else ProviderPrice(provider=source_record.provider, price=0)
        provider_sku = self._provider_ids(product.model_dump()).get("sku") or product.id
        stable = f"{source_record.provider}|{provider_sku}|{entity_id}|{first.price}"
        return ProviderOfferV3(
            offer_id=f"tc_offer_{hashlib.sha256(stable.encode('utf-8')).hexdigest()[:24]}",
            provider=source_record.provider,
            provider_sku=provider_sku,
            entity_id=entity_id,
            price=first.price if offers else None,
            availability=None,
            freshness={"observed_at": source_record.observed_metadata.get("observed_at"), "source": "ingested_provider_results"},
            raw_offer=first.model_dump(by_alias=True) if offers else {},
        )

    def _bounded_llm_attribute_extraction(self, contract: IdentityContract, selected: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        unresolved = [
            factor for factor in contract.critical
            if self._empty(selected.get(factor)) or self._empty(candidate.get(factor))
        ]
        if not unresolved:
            return {"attempted": False, "reason": "No unresolved identity-critical factors", "unresolved_factors": unresolved}
        
        try:
            import threading
            import asyncio

            result: dict[str, Any] = {"output": None, "error": None}

            def run_async():
                loop = asyncio.new_event_loop()
                try:
                    result["output"] = loop.run_until_complete(extractor.extract_missing_factors(unresolved, selected, candidate))
                except Exception as exc:
                    result["error"] = exc
                finally:
                    loop.close()

            thread = threading.Thread(target=run_async, daemon=True)
            thread.start()
            thread.join(timeout=2.5)
            if thread.is_alive():
                return {"attempted": True, "success": False, "reason": "LLM extraction timeout", "unresolved_factors": unresolved}
            if result["error"] is not None:
                raise result["error"]
            output = result["output"]
            if output is None:
                return {"attempted": True, "success": False, "reason": "LLM returned None / timeout", "unresolved_factors": unresolved}
            
            raw_evidence = getattr(output, "evidence", []) or []
            raw_attributes = getattr(output, "attributes", []) or []
            if raw_attributes and not raw_evidence:
                return {
                    "attempted": True,
                    "success": False,
                    "reason": "LLM output rejected: missing source evidence",
                    "unresolved_factors": unresolved,
                    "ignored_attributes": [str(getattr(attr, "factor", "")) for attr in raw_attributes],
                }

            applied: list[dict[str, Any]] = []
            ignored: list[dict[str, Any]] = []
            for attr in raw_attributes:
                factor = str(getattr(attr, "factor", getattr(attr, "name", "")) or "")
                side = str(getattr(attr, "side", "") or "")
                value = getattr(attr, "value", getattr(attr, "normalized_value", None))
                try:
                    confidence = float(getattr(attr, "confidence", 1.0))
                except Exception:
                    confidence = 0.0

                if factor not in contract.llm_extractable:
                    ignored.append({"factor": factor, "side": side, "reason": "factor_not_contract_extractable"})
                    continue
                if side not in {"selected", "candidate"}:
                    ignored.append({"factor": factor, "side": side, "reason": "invalid_side"})
                    continue
                if confidence < 0.6:
                    ignored.append({"factor": factor, "side": side, "reason": "low_confidence"})
                    continue
                target = selected if side == "selected" else candidate
                if not self._empty(target.get(factor)):
                    ignored.append({"factor": factor, "side": side, "reason": "explicit_attribute_not_overridden"})
                    continue
                target[factor] = value
                applied.append({"factor": factor, "side": side, "value": value, "confidence": confidence})

            evidence = [
                item if isinstance(item, dict) else {"source": "llm", "text": str(item)}
                for item in raw_evidence
            ]
            return {
                "attempted": True,
                "success": bool(applied),
                "attributes_extracted": len(applied),
                "applied_attributes": applied,
                "ignored_attributes": ignored,
                "evidence": evidence,
                "unresolved_factors": unresolved,
            }
        except Exception as e:
            return {"attempted": True, "success": False, "reason": f"Malformed LLM response: {str(e)}", "unresolved_factors": unresolved}

    def _legacy_decision(self, tier: str) -> str:
        if tier == "exact":
            return ResolutionDecision.EXACT.value
        if tier == "probable":
            return ResolutionDecision.PROBABLE.value
        if tier == "related":
            return ResolutionDecision.RELATED.value
        return ResolutionDecision.REJECTED.value

    def _identifiers(self, source: dict[str, Any]) -> dict[str, str]:
        return {
            key: self._norm(source.get(key))
            for key in _IDENTIFIER_KEYS
            if self._norm(source.get(key))
        }

    def _provider_ids(self, source: dict[str, Any]) -> dict[str, str]:
        result = {
            key: self._norm(source.get(key))
            for key in _PROVIDER_ID_KEYS
            if self._norm(source.get(key))
        }
        if self._norm(source.get("id")):
            result["sku"] = self._norm(source.get("id"))
        return result

    def _unknown_attributes(self, source: dict[str, Any], *, known_keys: set[str]) -> list[ExtractedAttribute]:
        unknown: list[ExtractedAttribute] = []
        for key, value in source.items():
            if key in known_keys or key in _IDENTIFIER_KEYS or key in _PROVIDER_ID_KEYS or value in (None, "", [], {}):
                continue
            if isinstance(value, (str, int, float, bool)):
                unknown.append(ExtractedAttribute(name=str(key), raw_value=str(value), normalized_value=self._norm(value), source="provider", identity_weight="unknown"))
        return unknown

    def _size(self, name: str, source: dict[str, Any]) -> dict[str, Any] | str:
        explicit = source.get("weight_volume") or source.get("weightVolume") or source.get("pack_size") or source.get("packSize") or ""
        text = f"{name} {explicit}"
        match = _SIZE_RE.search(text)
        if not match:
            return ""
        unit = match.group("unit").casefold()
        value = float(match.group("value"))
        
        if unit in {"l", "liter", "liters", "litre"}:
            return {"dimension": "volume", "base_value": value * 1000, "base_unit": "ml", "raw": f"{value}{unit}"}
        elif unit in {"ml", "milliliter"}:
            return {"dimension": "volume", "base_value": value, "base_unit": "ml", "raw": f"{value}{unit}"}
        elif unit in {"kg", "kilogram"}:
            return {"dimension": "weight", "base_value": value * 1000, "base_unit": "g", "raw": f"{value}{unit}"}
        elif unit in {"g", "gm", "gram"}:
            return {"dimension": "weight", "base_value": value, "base_unit": "g", "raw": f"{value}{unit}"}
        elif unit in {"mg"}:
            return {"dimension": "weight", "base_value": value / 1000, "base_unit": "g", "raw": f"{value}{unit}"}
        elif unit in {"pack", "pcs", "piece", "pieces"}:
            return {"dimension": "count", "base_value": value, "base_unit": "pcs", "raw": f"{value}{unit}"}
        
        return f"{value}{unit}"

    def _storage(self, name: str, source: dict[str, Any]) -> str:
        for value in (source.get("storage"), source.get("capacity")):
            if value:
                return self._norm(value).replace(" ", "")
        for match in _SIZE_RE.finditer(name):
            unit = match.group("unit").casefold()
            if unit in {"gb", "tb"}:
                return f"{match.group('value')}{unit}"
        return ""

    def _color(self, source: dict[str, Any]) -> str:
        return self._norm(source.get("color") or source.get("colour") or "")

    def _normalize_brand(self, brand: str, *, name: str, provider: str) -> str:
        normalized = self._norm(brand)
        if normalized and normalized not in _MARKETPLACE_BRANDS:
            return normalized
        provider_norm = self._norm(provider)
        first = self._tokens(name)[:1]
        return first[0] if first else ""

    def _signature(self, tokens: list[str]) -> list[str]:
        return sorted(set(token for token in tokens if token))

    def _strip_size_tokens(self, tokens: list[str]) -> list[str]:
        size_parts = set()
        units = {"ml", "l", "kg", "g", "gm", "mg", "mcg", "tb", "gb", "mah", "w", "mm", "cm", "inch", "inches", "pack", "pcs", "piece", "pieces", "liter", "liters", "litre", "milliliter", "kilogram", "gram"}
        for i, token in enumerate(tokens):
            if _SIZE_RE.fullmatch(token):
                size_parts.add(token)
            elif token in units and i > 0 and any(char.isdigit() for char in tokens[i-1]):
                size_parts.add(token)
                size_parts.add(tokens[i-1])
        return [token for token in tokens if token not in size_parts]

    def _compatible(self, factor: str, selected: Any, candidate: Any, *, contract: IdentityContract, selected_brand: str | None = None) -> bool:
        if isinstance(selected, dict) and isinstance(candidate, dict):
            if "dimension" in selected and "dimension" in candidate:
                return selected["dimension"] == candidate["dimension"] and abs(selected["base_value"] - candidate["base_value"]) < 0.01
        if isinstance(selected, list) or isinstance(candidate, list):
            selected_set = set(selected or [])
            candidate_set = set(candidate or [])
            if not selected_set:
                return True
            if not selected_set.issubset(candidate_set):
                return False
            extra = candidate_set - selected_set
            if selected_brand and extra == {self._norm(selected_brand)}:
                extra = set()
            if factor == "product_signature" and contract.entity_type == EntityType.GROCERY_SKU:
                return True
            if factor in {"variant_signature"} and contract.entity_type == EntityType.GROCERY_SKU:
                return len(extra) == 0
            if factor in {"model_signature"} and contract.entity_type == EntityType.PRODUCT:
                return len(extra) == 0
            return True
        return self._norm(selected) == self._norm(candidate)

    def _tokens(self, text: str) -> list[str]:
        return [self._norm(match.group(0)) for match in _WORD_RE.finditer(str(text or "").replace("-", " ")) if self._norm(match.group(0))]

    def _norm(self, value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").casefold().strip())

    def _empty(self, value: Any) -> bool:
        return value in (None, "", [], {}, ())


EntityResolutionService = EntityOfferResolutionService
entity_offer_resolution_service = EntityOfferResolutionService()
entity_resolution_service = entity_offer_resolution_service
