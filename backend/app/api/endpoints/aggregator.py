from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import hashlib
import json
import logging
from uuid import UUID

from app.schemas.product import TrueCostProduct
from app.connectors.zepto import ZeptoConnector
from app.connectors.blinkit import BlinkitConnector
from app.connectors.swiggy import SwiggyInstamartConnector
from app.connectors.bigbasket import BigBasketConnector
from app.connectors.uber import UberConnector
from app.connectors.ola import OlaConnector
from app.connectors.swiggy_food import SwiggyFoodConnector
from app.connectors.zomato import ZomatoConnector
from app.connectors.tata1mg import Tata1mgConnector
from app.connectors.pharmeasy import PharmEasyConnector
from app.connectors.makemytrip import MakeMyTripConnector
from app.connectors.goibibo import GoibiboConnector
from app.connectors.bankbazaar import BankBazaarConnector
from app.connectors.rapido import RapidoConnector
from app.connectors.flipkart import FlipkartConnector
from app.connectors.notion import NotionConnector
from app.connectors.figma import FigmaConnector
from app.connectors.namma_yatri import NammaYatriConnector
from app.connectors.meesho import MeeshoConnector
from app.connectors.myntra import MyntraConnector
from app.connectors.magicpin import MagicPinConnector
from app.connectors.eatsure import EatSureConnector
from app.connectors.apollo247 import Apollo247Connector
from app.connectors.netmeds import NetmedsConnector
from app.connectors.ixigo import IxigoConnector
from app.connectors.cleartrip import CleartripConnector
from app.connectors.policybazaar import PolicyBazaarConnector
from app.connectors.paisabazaar import PaisaBazaarConnector
from app.connectors.creditmantri import CreditMantriConnector
from app.connectors.slack import SlackConnector
from app.connectors.canva import CanvaConnector

from app.connectors.amazon import AmazonConnector
from app.connectors.namma_yatri import NammaYatriConnector
from app.connectors.meesho import MeeshoConnector
from app.connectors.myntra import MyntraConnector
from app.connectors.magicpin import MagicPinConnector
from app.connectors.eatsure import EatSureConnector
from app.connectors.apollo247 import Apollo247Connector
from app.connectors.netmeds import NetmedsConnector
from app.connectors.ixigo import IxigoConnector
from app.connectors.cleartrip import CleartripConnector
from app.connectors.policybazaar import PolicyBazaarConnector
from app.connectors.paisabazaar import PaisaBazaarConnector
from app.connectors.creditmantri import CreditMantriConnector
from app.connectors.slack import SlackConnector
from app.connectors.canva import CanvaConnector

from app.services.merger import merge_products as _merge_products
from app.services.product_identity import identity_engine
from app.services.entity_resolution import ResolutionDecision, SourceRecord, entity_resolution_service
from app.services.canonical_offer_group import build_canonical_offer_groups
from app.services.truecost_optimizer import TrueCostOptimizer
from app.services.cache import cache  # The shared singleton
from app.api.endpoints.auth import bearer, decode_token
from app.db import get_db
from app.models import DecisionAuditTrail, EntityResolutionRecord, IngestedProviderResult, PriceObservation, PriceWatch, ProviderOperationalState, SearchSession, User, PriceObservation, PriceWatch, ProviderOperationalState, SearchSession, User
from app.category_catalog import KNOWN_PROVIDER_IDS, normalize_provider_key as canonical_provider_key, provider_ids_for_engine_category
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

KNOWN_PROVIDERS = list(KNOWN_PROVIDER_IDS)

# Maps any display name the mobile might send â†’ the connector dict key
# Handles spacing, capitalisation, and abbreviation variations
PROVIDER_ALIAS_MAP: dict = {
    # Grocery
    "zepto": "zepto",
    "blinkit": "blinkit",
    "swiggy": "swiggy",
    "swiggy instamart": "swiggy",
    "bigbasket": "bigbasket",
    "big basket": "bigbasket",
    # Mobility
    "uber": "uber",
    "ola": "ola",
    "rapido": "rapido",
    "namma yatri": "namma_yatri",
    "nammayatri": "namma_yatri",
    # Shopping
    "amazon": "amazon",
    "flipkart": "flipkart",
    "meesho": "meesho",
    "myntra": "myntra",
    # Food
    "swiggy food": "swiggy_food",
    "swiggy_food": "swiggy_food",
    "zomato": "zomato",
    "magicpin": "magicpin",
    "eatsure": "eatsure",
    # Pharmacy
    "tata 1mg": "tata1mg",
    "tata1mg": "tata1mg",
    "1mg": "tata1mg",
    "pharmeasy": "pharmeasy",
    "pharm easy": "pharmeasy",
    "apollo 247": "apollo247",
    "apollo247": "apollo247",
    "netmeds": "netmeds",
    # Travel
    "makemytrip": "makemytrip",
    "make my trip": "makemytrip",
    "goibibo": "goibibo",
    "ixigo": "ixigo",
    "cleartrip": "cleartrip",
    # Finance
    "bankbazaar": "bankbazaar",
    "bank bazaar": "bankbazaar",
    "policybazaar": "policybazaar",
    "paisabazaar": "paisabazaar",
    "creditmantri": "creditmantri",
    # Productivity
    "notion": "notion",
    "figma": "figma",
    "slack": "slack",
    "canva": "canva",
}

def normalize_provider_key(provider: str) -> str:
    """Resolve any provider display name to its canonical connector key."""
    return canonical_provider_key(provider)

# Instantiate connectors (Factory Pattern)
connectors = {
    "zepto": ZeptoConnector(),
    "blinkit": BlinkitConnector(),
    "swiggy": SwiggyInstamartConnector(),
    "bigbasket": BigBasketConnector(),
    "uber": UberConnector(),
    "ola": OlaConnector(),
    "rapido": RapidoConnector(),
    "namma_yatri": NammaYatriConnector(),
    "amazon": AmazonConnector() if "AmazonConnector" in dir() else None,
    "flipkart": FlipkartConnector(),
    "meesho": MeeshoConnector(),
    "myntra": MyntraConnector(),
    "swiggy_food": SwiggyFoodConnector(),
    "zomato": ZomatoConnector(),
    "magicpin": MagicPinConnector(),
    "eatsure": EatSureConnector(),
    "tata1mg": Tata1mgConnector(),
    "pharmeasy": PharmEasyConnector(),
    "apollo247": Apollo247Connector(),
    "netmeds": NetmedsConnector(),
    "makemytrip": MakeMyTripConnector(),
    "goibibo": GoibiboConnector(),
    "ixigo": IxigoConnector(),
    "cleartrip": CleartripConnector(),
    "bankbazaar": BankBazaarConnector(),
    "policybazaar": PolicyBazaarConnector(),
    "paisabazaar": PaisaBazaarConnector(),
    "creditmantri": CreditMantriConnector(),
    "notion": NotionConnector(),
    "figma": FigmaConnector(),
    "slack": SlackConnector(),
    "canva": CanvaConnector(),
}
# Remove any None entries (connectors not yet imported)
connectors = {k: v for k, v in connectors.items() if v is not None}

class IngestLocation(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    postal_code: str | None = None
    display: str | None = None
    source: str | None = None


class IngestPayload(BaseModel):
    provider: str
    query: str
    category: str = "Grocery"
    raw_data: Union[dict, list]   # scrapers may send list[] or dict — accept both
    search_session_id: str | None = None
    provider_query: str | None = None
    exact_discovery_attempt: int | None = None
    selected_location: IngestLocation | None = None
    selected_product_hint: dict[str, Any] | None = None


def _location_payload(location: IngestLocation | None) -> dict[str, Any] | None:
    return location.model_dump(exclude_none=True) if location else None


def _product_ingestion_key(session_id: str, provider: str, product: dict[str, Any]) -> str:
    parts = [
        session_id,
        provider.casefold().strip(),
        str(product.get("name") or product.get("title") or "").casefold().strip(),
        str(product.get("brand") or "").casefold().strip(),
        str(product.get("weightVolume") or product.get("weight_volume") or "").casefold().strip(),
    ]
    stable = "|".join(parts)
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()

    @classmethod
    def model_validator(cls, values):
        return values

class OptimizePayload(BaseModel):
    basket: List[List[TrueCostProduct]]


class SearchSuggestion(BaseModel):
    query: str
    category: str
    kind: str = "observed_product"
    product_id: str | None = None
    brand: str | None = None
    image_url: str | None = None
    provider_count: int = 0


def _valid_client_session_id(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError):
        return None


def _lowest_price(product: dict[str, Any]) -> float:
    prices = product.get("prices") or []
    observed = [float(offer["price"]) for offer in prices if isinstance(offer, dict) and offer.get("price") is not None]
    return min(observed) if observed else 999999999.0


def _best_observed(products: list[dict[str, Any]]) -> dict[str, Any] | None:
    offers: list[dict[str, Any]] = []
    for product in products:
        for offer in product.get("prices") or []:
            if isinstance(offer, dict) and offer.get("price") is not None:
                offers.append({"product": product, "offer": offer})
    if not offers:
        return None
    return min(offers, key=lambda item: float(item["offer"]["price"]))


def _decision_explanation(primary: list[dict[str, Any]], related: list[dict[str, Any]], rejected_count: int, pending: list[str]) -> str:
    best = _best_observed(primary)
    if best:
        offer = best["offer"]
        return (
            f"{offer.get('provider', 'A provider')} currently has the lowest observed exact-match price. "
            f"{len(related)} related result(s) and {rejected_count} rejected result(s) were not used for this decision."
        )
    if pending:
        return "No exact provider price is verified yet. Some providers are still pending or unavailable."
    return "Providers responded, but none returned a safely comparable exact product."


def _entity_v3_active(category: str, exact_match: bool) -> bool:
    if not exact_match:
        return False
    if str(category or "").casefold().strip() not in {"shopping", "grocery"}:
        return False
    if settings.entity_resolution_rollback_to_legacy:
        return False
    if settings.entity_resolution_mode == "legacy":
        return False
    return entity_resolution_service.supports(category)


def _legacy_decision_from_tier(tier: str) -> str:
    if tier == "exact":
        return "EXACT"
    if tier == "probable":
        return "PROBABLE"
    if tier == "related":
        return "RELATED"
    return "REJECTED"


def _is_discovery_query(intent: Any) -> bool:
    specificity = getattr(getattr(intent, "specificity", None), "value", getattr(intent, "specificity", ""))
    return str(specificity or "").upper() in {"BROAD", "CATEGORY_FEATURE", "NATURAL_LANGUAGE"}


def _selected_product_from_intent(query: str, intent: Any) -> dict[str, Any]:
    parsed = getattr(intent, "parsed", None)
    selected = {"name": query}
    brand = getattr(parsed, "brand", None)
    if brand:
        selected["brand"] = brand
    product_type = getattr(parsed, "product_type", None)
    if product_type:
        selected["product_type"] = product_type
    return selected


def _product_provider_keys(product: dict[str, Any]) -> list[str]:
    prices = product.get("prices") if isinstance(product, dict) else []
    providers: list[str] = []
    if isinstance(prices, list):
        for offer in prices:
            if isinstance(offer, dict):
                provider = str(offer.get("provider") or "").strip()
                if provider:
                    providers.append(normalize_provider_key(provider))
    direct_provider = str(product.get("provider") or "").strip() if isinstance(product, dict) else ""
    if direct_provider:
        providers.append(normalize_provider_key(direct_provider))
    return list(dict.fromkeys(provider for provider in providers if provider))


def _lead_provider_key(product: dict[str, Any]) -> str:
    prices = product.get("prices") if isinstance(product, dict) else []
    if isinstance(prices, list) and prices and isinstance(prices[0], dict):
        provider = str(prices[0].get("provider") or "").strip()
        if provider:
            return normalize_provider_key(provider)
    direct_provider = str(product.get("provider") or "").strip() if isinstance(product, dict) else ""
    return normalize_provider_key(direct_provider) if direct_provider else "unknown"


def _price_sort_value(product: dict[str, Any]) -> float:
    prices = product.get("prices") if isinstance(product, dict) else []
    if isinstance(prices, list) and prices and isinstance(prices[0], dict):
        try:
            return float(prices[0].get("price") or 999999)
        except (TypeError, ValueError):
            return 999999
    return 999999


def _comparison_sort_key(product: dict[str, Any]) -> tuple[int, float]:
    return (-len(_product_provider_keys(product)), _price_sort_value(product))


def _balance_discovery_results(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Interleave broad discovery results so one provider does not own the first screen.

    True multi-provider comparison groups still lead the list. Single-provider
    discoveries are then round-robin ordered by provider while preserving the
    existing per-provider ranking.
    """
    compared: list[dict[str, Any]] = []
    buckets: dict[str, list[dict[str, Any]]] = {}
    provider_order: list[str] = []

    for product in products:
        providers = _product_provider_keys(product)
        if len(providers) > 1:
            compared.append(product)
            continue
        provider = providers[0] if providers else "unknown"
        if provider not in buckets:
            buckets[provider] = []
            provider_order.append(provider)
        buckets[provider].append(product)

    balanced: list[dict[str, Any]] = []
    while any(buckets.values()):
        for provider in provider_order:
            bucket = buckets.get(provider) or []
            if bucket:
                balanced.append(bucket.pop(0))

    return compared + balanced


def _result_identity_key(product: dict[str, Any]) -> str:
    if not isinstance(product, dict):
        return ""
    providers = ",".join(_product_provider_keys(product))
    return "|".join([
        str(product.get("id") or "").strip(),
        str(product.get("name") or "").casefold().strip(),
        str(product.get("brand") or "").casefold().strip(),
        str(product.get("weightVolume") or product.get("weight_volume") or "").casefold().strip(),
        providers,
    ])


def _promote_discovery_provider_coverage(
    primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    *,
    per_missing_provider: int = 3,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """For broad discovery, surface a few relevant items from providers hidden in review."""
    primary_providers = {_lead_provider_key(product) for product in primary}
    secondary_buckets: dict[str, list[dict[str, Any]]] = {}
    for product in secondary:
        if product.get("matchTier") == "rejected" or product.get("queryRelevance") == "COMPLEMENT":
            continue
        if float(product.get("matchScore") or 0) < 0.3:
            continue
        provider = _lead_provider_key(product)
        if provider not in primary_providers:
            secondary_buckets.setdefault(provider, []).append(product)

    promoted_keys: set[str] = set()
    promoted: list[dict[str, Any]] = []
    for provider in sorted(secondary_buckets):
        for product in secondary_buckets[provider][:per_missing_provider]:
            key = _result_identity_key(product)
            promoted_keys.add(key)
            promoted.append(product)

    if not promoted:
        return primary, secondary
    remaining = [product for product in secondary if _result_identity_key(product) not in promoted_keys]
    return primary + promoted, remaining


def _recount_provider_match_stats(
    diagnostics: dict[str, Any],
    *,
    primary: list[dict[str, Any]],
    probable: list[dict[str, Any]],
    related: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
) -> None:
    provider_stats = diagnostics.setdefault("providers", {})
    for stats in provider_stats.values():
        if isinstance(stats, dict):
            stats["exact_matches"] = 0
            stats["probable"] = 0
            stats["related"] = 0
            stats["rejected"] = 0

    def bump(product: dict[str, Any], field: str) -> None:
        for provider in _product_provider_keys(product) or [_lead_provider_key(product)]:
            stats = provider_stats.setdefault(provider, {
                "observed": 0,
                "exact_matches": 0,
                "probable": 0,
                "related": 0,
                "rejected": 0,
                "best_rejected": [],
            })
            stats[field] = int(stats.get(field) or 0) + 1

    for product in primary:
        bump(product, "exact_matches")
    for product in probable:
        bump(product, "probable")
    for product in related:
        bump(product, "related")
    for product in rejected:
        bump(product, "rejected")


def _resolution_summary(resolutions: list[dict[str, Any]], *, mode: str) -> dict[str, Any]:
    counts = {"EXACT": 0, "PROBABLE": 0, "RELATED": 0, "REJECTED": 0}
    disagreements = 0
    unknown_attributes = 0
    completeness_scores: list[float] = []
    for item in resolutions:
        decision = item.get("decision") or "REJECTED"
        counts[decision] = counts.get(decision, 0) + 1
        disagreements += 1 if item.get("disagreement") else 0
        entity = item.get("canonical_entity") or {}
        attrs = entity.get("attributes") or {}
        unknown_attributes += len(entity.get("unknown_attributes") or [])
        required = 3
        completeness_scores.append(min(1.0, len([value for value in attrs.values() if value not in (None, "", [], {})]) / required))
    total = max(1, len(resolutions))
    return {
        "resolver": "entity_resolution_v3",
        "mode": mode,
        "counts": counts,
        "legacy_v3_disagreements": disagreements,
        "resolver_disagreement_rate": round(disagreements / total, 4),
        "unknown_attribute_count": unknown_attributes,
        "identity_completeness": round(sum(completeness_scores) / total, 4) if completeness_scores else 0,
        "authoritative_decisions": ["EXACT"],
        "probable_authoritative": False,
    }


def _build_discovery_report(
    *,
    query: str,
    category: str,
    session_id: str | None,
    selected_product: dict[str, Any] | None,
    primary: list[dict[str, Any]],
    related: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    provider_status: dict[str, Any],
    provider_attempts: list[dict[str, Any]],
    probable: list[dict[str, Any]] | None = None,
    resolution_summary: dict[str, Any] | None = None,
    canonical_entities: list[dict[str, Any]] | None = None,
    provider_offers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    probable_results = probable or []
    selected_identity = (
        entity_resolution_service.selected_entity(query=query, selected_product=selected_product, category=category)
        if entity_resolution_service.supports(category)
        else identity_engine.selected_identity(user_query=query, selected_product=selected_product, category=category)
    )
    canonical_offer_groups = build_canonical_offer_groups(
        query=query,
        category=category,
        selected_identity=selected_identity,
        exact_results=primary,
        probable_results=probable_results,
        related_results=related,
        rejected_results=rejected,
        provider_status=provider_status,
        resolution_mode=settings.entity_resolution_mode,
    )
    return {
        "query": query,
        "category": category,
        "session_id": session_id,
        "selected_identity": selected_identity,
        "provider_attempts": provider_attempts,
        "exact_results": primary,
        "probable_results": probable_results,
        "related_results": related,
        "rejected_results": rejected[:20],
        "provider_status": provider_status,
        "best_observed": _best_observed(primary),
        "canonical_offer_groups": canonical_offer_groups,
        "decision_explanation": _decision_explanation(primary, probable_results + related, len(rejected), [key for key, value in provider_status.items() if value.get("state") in {"pending", "unavailable"}]),
        "resolution_summary": resolution_summary,
        "canonical_entities": canonical_entities or [],
        "provider_offers": provider_offers or [],
    }


def _audit_hash(report: dict[str, Any]) -> str:
    stable_payload = {
        "query": report.get("query"),
        "category": report.get("category"),
        "selected_identity": report.get("selected_identity"),
        "provider_attempts": report.get("provider_attempts"),
        "exact_ids": [
            {"id": item.get("id"), "name": item.get("name"), "prices": item.get("prices")}
            for item in report.get("exact_results") or []
        ],
        "related_ids": [
            {"id": item.get("id"), "name": item.get("name")}
            for item in report.get("related_results") or []
        ],
        "probable_ids": [
            {"id": item.get("id"), "name": item.get("name")}
            for item in report.get("probable_results") or []
        ],
        "rejected_ids": [
            {"id": item.get("id"), "name": item.get("name"), "reason": (item.get("identity") or {}).get("rejection_reason")}
            for item in report.get("rejected_results") or []
        ],
        "best_observed": report.get("best_observed"),
        "canonical_offer_groups": [
            {
                "group_id": group.get("group_id"),
                "entity": group.get("entity"),
                "offers": [
                    {"provider": offer.get("provider"), "price": offer.get("price"), "product_id": offer.get("evidence", {}).get("product_id")}
                    for offer in group.get("offers") or []
                ],
            }
            for group in report.get("canonical_offer_groups") or []
        ],
    }
    return hashlib.sha256(json.dumps(stable_payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _persist_entity_resolution_records(db: Session, *, search_session: SearchSession, records: list[dict[str, Any]]) -> None:
    for record in records:
        llm_payload = record.get("llm_extraction") or {}
        audit = EntityResolutionRecord(
            search_session_id=search_session.id,
            selected_entity=record.get("selected_entity") or record.get("canonical_entity", {}),
            candidate_entity=record.get("candidate_entity") or record.get("canonical_entity", {}),
            provider_offer=record.get("provider_offer", {}),
            legacy_decision=record.get("legacy_decision", "rejected"),
            v3_decision=record.get("decision", "rejected"),
            disagreement=record.get("disagreement", False),
            evidence=record.get("evidence", []),
            conflicts=record.get("conflicts", []),
            missing_factors=record.get("missing_factors", []),
            unknown_attributes=record.get("canonical_entity", {}).get("unknown_attributes", {}),
            resolver_version=record.get("resolver_version", "v3"),
            confidence_inputs=record.get("confidence", 0.0),
            extraction_provenance={"llm": llm_payload} if llm_payload else {},
            llm_used=bool(llm_payload.get("attempted")) if isinstance(llm_payload, dict) else False
        )
        db.add(audit)
    db.commit()

def _persist_decision_audit(db: Session, *, search_session: SearchSession, report: dict[str, Any]) -> None:
    """Persist the explainability artifact for a session-scoped decision.

    The report is intentionally decomposed into stable JSON columns so an
    operator can answer "why did TrueCost show this?" without replaying a live
    provider search. The unique hash makes refresh/rerun idempotent.
    """
    artifact_hash = _audit_hash(report)
    best = report.get("best_observed") or {}
    canonical_groups = report.get("canonical_offer_groups") or []
    final_decision = {
        "canonical_offer_group": canonical_groups[0] if canonical_groups else None,
        "winner": best.get("product"),
        "best_offer": best.get("offer"),
        "provider_status": report.get("provider_status") or {},
        "confidence": "high" if report.get("exact_results") else "low",
    }
    freshness = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "ingested_provider_results",
        "provider_status": report.get("provider_status") or {},
    }
    def _safe_json(obj: Any) -> Any:
        """Sanitize an object to be JSON-serializable (converts MagicMock and other non-serializable objects)."""
        try:
            return json.loads(json.dumps(obj, default=str))
        except Exception:
            return {}

    audit = DecisionAuditTrail(
        search_session_id=search_session.id,
        user_id=search_session.user_id,
        artifact_type="exact_discovery",
        artifact_hash=artifact_hash,
        selected_identity=_safe_json(report.get("selected_identity") or {}),
        provider_attempts=_safe_json(report.get("provider_attempts") or []),
        exact_results=_safe_json(report.get("exact_results") or []),
        related_results=_safe_json(report.get("related_results") or []),
        rejected_results=_safe_json(report.get("rejected_results") or []),
        final_decision=_safe_json(final_decision),
        freshness=_safe_json(freshness),
        explanation=report.get("decision_explanation"),
    )
    try:
        existing = db.query(DecisionAuditTrail).filter(
            DecisionAuditTrail.search_session_id == search_session.id,
            DecisionAuditTrail.artifact_type == "exact_discovery",
            DecisionAuditTrail.artifact_hash == artifact_hash,
        ).first()

        if existing:
            existing.selected_identity = _safe_json(report.get("selected_identity") or {})
            existing.provider_attempts = _safe_json(report.get("provider_attempts") or [])
            existing.exact_results = _safe_json(report.get("exact_results") or [])
            existing.related_results = _safe_json(report.get("related_results") or [])
            existing.rejected_results = _safe_json(report.get("rejected_results") or [])
            existing.final_decision = _safe_json(final_decision)
            existing.freshness = _safe_json(freshness)
            existing.explanation = report.get("decision_explanation")
        else:
            db.add(audit)
        db.commit()
    except IntegrityError:
        db.rollback()
    except Exception as e:
        logger.warning("entity_resolution_persist_failed", exc_info=e)
        db.rollback()


@router.get("/decision-audits/{search_session_id}")
def get_decision_audits(
    search_session_id: str,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict[str, Any]:
    session = db.get(SearchSession, search_session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Search session not found")
    if session.user_id is not None:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Not authenticated")
        payload = decode_token(credentials.credentials, "access")
        if payload.get("sub") != session.user_id:
            raise HTTPException(status_code=403, detail="Decision audit belongs to another user")
    rows = db.scalars(
        select(DecisionAuditTrail)
        .where(DecisionAuditTrail.search_session_id == search_session_id)
        .order_by(DecisionAuditTrail.created_at.desc())
    ).all()
    return {
        "search_session_id": search_session_id,
        "query": session.query,
        "category": session.category,
        "audits": [
            {
                "id": row.id,
                "artifact_type": row.artifact_type,
                "artifact_hash": row.artifact_hash,
                "selected_identity": row.selected_identity,
                "provider_attempts": row.provider_attempts,
                "exact_results": row.exact_results,
                "related_results": row.related_results,
                "rejected_results": row.rejected_results,
                "final_decision": row.final_decision,
                "freshness": row.freshness,
                "explanation": row.explanation,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
    }


@router.get("/suggestions", response_model=list[SearchSuggestion])
def search_suggestions(
    q: str = Query(..., min_length=2, max_length=120),
    category: str = Query("Grocery", min_length=1, max_length=100),
    limit: int = Query(6, ge=1, le=10),
    db: Session = Depends(get_db),
) -> list[SearchSuggestion]:
    """Return only suggestions backed by previously trusted ingestion rows.

    Raw user queries are deliberately not exposed. Product names, images and
    brands come from the sanitized canonical product payload persisted by the
    ingest endpoint, so an empty catalog correctly returns no suggestions.
    """
    needle = " ".join(q.casefold().split())
    candidates = db.execute(
        select(IngestedProviderResult, SearchSession.category)
        .join(SearchSession, SearchSession.id == IngestedProviderResult.search_session_id)
        .where(func.lower(SearchSession.category) == category.casefold())
        .order_by(IngestedProviderResult.observed_at.desc())
        .limit(500)
    ).all()
    suggestions: list[SearchSuggestion] = []
    seen: set[str] = set()
    for row, observed_category in candidates:
        product = row.product if isinstance(row.product, dict) else {}
        name = str(product.get("name") or "").strip()
        brand = str(product.get("brand") or "").strip()
        searchable = f"{name} {brand}".casefold()
        key = " ".join(name.casefold().split())
        if not name or needle not in searchable or key in seen:
            continue
        prices = product.get("prices")
        suggestions.append(SearchSuggestion(
            query=name,
            category=str(product.get("category") or observed_category),
            product_id=str(product.get("id") or row.product_id),
            brand=brand or None,
            image_url=str(product.get("imageUrl") or product.get("image_url") or "").strip() or None,
            provider_count=len(prices) if isinstance(prices, list) else 0,
        ))
        seen.add(key)
        if len(suggestions) >= limit:
            break
    return suggestions


@router.get("/search", response_model=dict)
async def search_cache(
    q: str = Query(..., description="Search query"),
    category: str = Query("Grocery", description="Agent category"),
    session_id: str = Query(None, description="Active search session ID for session-scoped results"),
    exact_match: bool = Query(False, description="Use strict selected-product matching"),
    db: Session = Depends(get_db),
):
    """
    Intelligent Search Endpoint.
    1. If session_id is provided, queries ONLY that session's products from DB (fresh, scoped).
    2. Otherwise, falls back to cache for instant results.
    3. Returns structured response: { primary_results, recommendations, providers_responded, providers_pending }
    """
    from app.services.relevance import score_product
    from app.services.merger import merge_products as _merge_session_products
    from app.schemas.product import TrueCostProduct

    # ── Universal Search Intelligence ──────────────────────────────────────
    # Run BEFORE any retrieval. Corrects query, extracts intent, classifies
    # specificity. corrected_q replaces q for all ER and identity calls.
    try:
        from app.services.search_intelligence import search_intelligence
        from app.services.search_intelligence.relevance_classifier import classify_products_batch
        _si_intent = search_intelligence(raw_query=q, category=category)
        corrected_q = _si_intent.best_retrieval_query()
    except Exception as _si_err:
        import logging
        logging.getLogger(__name__).warning(f"[SI] pipeline error: {_si_err}")
        _si_intent = None
        corrected_q = q
    selected_product_for_match = _selected_product_from_intent(corrected_q, _si_intent)

    # For non-Grocery/non-Shopping categories: also run through the category workflow
    if not session_id and category.lower() in ('food', 'pharmacy', 'mobility', 'travel', 'finance', 'productivity', 'services'):
        try:
            from app.repositories.search_cache import search_cache
            cached_items = search_cache.search(category.lower(), q)
            if cached_items:
                # Return them directly, sorted by price
                def _price(item):
                    p = item.get('prices', [])
                    return p[0].get('price', 9999) if p else 9999
                sorted_items = sorted(cached_items, key=_price)
                return {
                    'primary_results': sorted_items,
                    'recommendations': sorted_items[:3],
                    'providers_responded': list({i.get('brand','') for i in sorted_items}),
                    'providers_pending': [],
                    'session_id': session_id,
                    'data_source': 'search_cache',
                }
        except Exception:
            pass

    # --- Path A: Session-scoped DB query (preferred, most accurate) ---
    if session_id:
        session = db.get(SearchSession, session_id)
        if session:
            rows = db.execute(
                select(IngestedProviderResult)
                .where(IngestedProviderResult.search_session_id == session_id)
                .order_by(IngestedProviderResult.observed_at.desc())
            ).scalars().all()

            discovery_query = _is_discovery_query(_si_intent)
            use_entity_v3 = _entity_v3_active(category, exact_match and not discovery_query)
            flat_products: List[TrueCostProduct] = []
            providers_responded = set()
            diagnostics: dict[str, Any] = {
                "exact_match": exact_match,
                "discovery_query": discovery_query,
                "providers": {},
                "entity_resolution": {"enabled": use_entity_v3, "mode": settings.entity_resolution_mode},
            }
            rejected: list[dict[str, Any]] = []
            primary, secondary = [], []
            resolution_records: list[dict[str, Any]] = []
            canonical_entities_by_id: dict[str, dict[str, Any]] = {}
            provider_offers: list[dict[str, Any]] = []
            for row in rows:
                try:
                    product_data = row.product if isinstance(row.product, dict) else {}
                    tp = TrueCostProduct.model_validate(product_data)
                    flat_products.append(tp)
                    providers_responded.add(row.provider)
                    provider_stats = diagnostics["providers"].setdefault(row.provider, {
                        "observed": 0,
                        "exact_matches": 0,
                        "related": 0,
                        "rejected": 0,
                        "probable": 0,
                        "best_rejected": [],
                    })
                    provider_stats["observed"] += 1
                    if use_entity_v3:
                        resolution = entity_resolution_service.resolve(
                            query=corrected_q,
                            selected_product=selected_product_for_match,
                            category=category,
                            source_record=SourceRecord(
                                provider=row.provider,
                                product=tp,
                                observed_metadata={"observed_at": row.observed_at.isoformat() if row.observed_at else None},
                            ),
                            enable_llm_extraction=settings.entity_resolution_llm_extraction_enabled,
                        )
                        resolution_payload = resolution.model_dump()
                        resolution_records.append(resolution_payload)
                        canonical_entities_by_id[resolution.canonical_entity.entity_id] = resolution.canonical_entity.model_dump()
                        provider_offers.append(resolution.provider_offer.model_dump())
                        
                    # Determine authoritative engine based on mode
                    if use_entity_v3 and settings.entity_resolution_mode == "v3":
                        product_payload = tp.model_dump(by_alias=True)
                        product_payload["identity"] = resolution_payload
                        product_payload["entityResolution"] = resolution_payload
                        product_payload["matchScore"] = resolution.confidence
                        product_payload["provider"] = row.provider
                        if resolution.decision == ResolutionDecision.EXACT:
                            product_payload["matchTier"] = "primary"
                            primary.append(product_payload)
                            provider_stats["exact_matches"] += 1
                        elif resolution.decision == ResolutionDecision.PROBABLE:
                            # CRITICAL CORRECTION #2: PROBABLE is non-authoritative
                            product_payload["matchTier"] = "probable"
                            secondary.append(product_payload)
                            provider_stats["probable"] += 1
                        elif resolution.decision == ResolutionDecision.RELATED:
                            product_payload["matchTier"] = "related"
                            secondary.append(product_payload)
                            provider_stats["related"] += 1
                        else:
                            product_payload["matchTier"] = "rejected"
                            rejected.append(product_payload)
                            provider_stats["rejected"] += 1
                            if len(provider_stats["best_rejected"]) < 3:
                                provider_stats["best_rejected"].append({"name": tp.name, "brand": tp.brand, "score": resolution.confidence, "reason": "v3 Rejected"})
                    else:
                        identity = identity_engine.compare(
                            user_query=corrected_q,
                            selected_product=selected_product_for_match,
                            category=category,
                            provider_product=tp,
                            observed_metadata={"observed_at": row.observed_at.isoformat() if row.observed_at else None},
                        )
                        s = identity.match_score if identity else score_product(corrected_q, tp.name, tp.brand or "")
                        product_payload = tp.model_dump(by_alias=True)
                        product_payload["matchScore"] = s
                        product_payload["provider"] = row.provider
                        
                        # Add v3 diagnostics to the legacy payload if running in dual/shadow
                        if use_entity_v3:
                            product_payload["entityResolution"] = resolution_payload
                            
                        if identity:
                            product_payload["identity"] = identity.model_dump()
                            product_payload["matchTier"] = "primary" if identity.match_tier in {"exact", "probable"} else identity.match_tier
                        else:
                            product_payload["matchTier"] = "primary" if s >= 0.55 else "related" if s >= 0.35 else "discard"
                            
                        if product_payload["matchTier"] == "primary":
                            primary.append(product_payload)
                            provider_stats["exact_matches"] += 1
                        elif product_payload["matchTier"] == "related":
                            secondary.append(product_payload)
                            provider_stats["related"] += 1
                        else:
                            provider_stats["rejected"] += 1
                            product_payload["matchTier"] = "rejected"
                            rejected.append(product_payload)
                            if len(provider_stats["best_rejected"]) < 3:
                                provider_stats["best_rejected"].append({"name": tp.name, "brand": tp.brand, "score": s, "reason": identity.rejection_reason if identity else "Discarded"})
                except Exception:
                    continue

            if not use_entity_v3:
                merge_threshold = 0.93 if discovery_query else 0.72
                merged = _merge_session_products(flat_products, threshold=merge_threshold)

                primary, secondary = [], []
                for product in merged:
                    identity = identity_engine.compare(user_query=corrected_q, selected_product=selected_product_for_match, category=category, provider_product=product) if exact_match and not discovery_query else None
                    s = identity.match_score if identity else score_product(corrected_q, product.name, product.brand or "")
                    product_payload = product.model_dump(by_alias=True)
                    product_payload["matchScore"] = s
                    if identity:
                        product_payload["identity"] = identity.model_dump()
                        product_payload["matchTier"] = "primary" if identity.match_tier in {"exact", "probable"} else identity.match_tier
                    else:
                        product_payload["matchTier"] = "primary" if s >= 0.55 else "related" if s >= 0.35 else "discard"
                    if product_payload["matchTier"] == "primary":
                        primary.append(product_payload)
                    elif product_payload["matchTier"] == "related":
                        secondary.append(product_payload)
                    # Discard noise (s < 0.35)

            # ── Query-Product Relevance Classification (ESCI) ─────────────────
            # Re-score primary/secondary using the QueryIntent's hard constraints.
            # This enforces: model mismatch → demoted from primary even if ER said exact.
            if _si_intent is not None:
                try:
                    primary = classify_products_batch(_si_intent, primary)
                    secondary = classify_products_batch(_si_intent, secondary)
                    # Move any newly rejected products from primary/secondary → rejected
                    newly_rejected_p = [p for p in primary if p.get("matchTier") == "rejected"]
                    primary = [p for p in primary if p.get("matchTier") != "rejected"]
                    rejected.extend(newly_rejected_p)
                    newly_rejected_s = [p for p in secondary if p.get("matchTier") == "rejected"]
                    secondary = [p for p in secondary if p.get("matchTier") != "rejected"]
                    rejected.extend(newly_rejected_s)
                    # Move substitutes to secondary if they ended up in primary
                    new_substitutes = [p for p in primary if p.get("queryRelevance") == "SUBSTITUTE"]
                    primary = [p for p in primary if p.get("queryRelevance") != "SUBSTITUTE"]
                    secondary = new_substitutes + secondary
                    if discovery_query:
                        discoverable = [
                            p for p in secondary
                            if p.get("matchTier") != "rejected"
                            and p.get("queryRelevance") != "COMPLEMENT"
                            and float(p.get("matchScore") or 0) >= 0.3
                        ]
                        if discoverable and not primary:
                            primary = discoverable[:20]
                            secondary = [p for p in secondary if p not in primary]
                        primary, secondary = _promote_discovery_provider_coverage(primary, secondary)
                except Exception:
                    pass  # Non-blocking

            # Sort true comparisons first, then keep broad discovery visually provider-balanced.
            primary.sort(key=_comparison_sort_key)
            secondary.sort(key=_comparison_sort_key)
            if discovery_query:
                primary = _balance_discovery_results(primary)
                secondary = _balance_discovery_results(secondary)
            probable_results = [p for p in secondary if p.get("matchTier") == "probable"]
            related_results = [p for p in secondary if p.get("matchTier") != "probable"]
            _recount_provider_match_stats(
                diagnostics,
                primary=primary,
                probable=probable_results,
                related=related_results,
                rejected=rejected,
            )

            expected = set(provider_ids_for_engine_category(category) or KNOWN_PROVIDERS)
            providers_pending = list(expected - providers_responded)
            provider_status = {
                provider: {
                    "state": "responded" if provider in providers_responded else "pending",
                    "observed": diagnostics["providers"].get(provider, {}).get("observed", 0),
                    "exact_matches": diagnostics["providers"].get(provider, {}).get("exact_matches", 0),
                    "probable": diagnostics["providers"].get(provider, {}).get("probable", 0),
                    "related": diagnostics["providers"].get(provider, {}).get("related", 0),
                    "rejected": diagnostics["providers"].get(provider, {}).get("rejected", 0),
                }
                for provider in expected
            }
            resolution_summary = _resolution_summary(resolution_records, mode=settings.entity_resolution_mode) if use_entity_v3 else None
            if resolution_summary:
                diagnostics["entity_resolution"].update(resolution_summary)
            provider_attempts = [{"provider": provider, "query": corrected_q, "state": status["state"]} for provider, status in sorted(provider_status.items())]
            discovery_report = _build_discovery_report(
                query=corrected_q,
                category=category,
                session_id=session_id,
                selected_product=selected_product_for_match,
                primary=primary,
                related=related_results[:20],
                rejected=rejected,
                provider_status=provider_status,
                provider_attempts=provider_attempts,
                probable=probable_results[:20],
                resolution_summary=resolution_summary,
                canonical_entities=list(canonical_entities_by_id.values()),
                provider_offers=provider_offers,
            )
            _persist_decision_audit(db, search_session=session, report=discovery_report)
            if resolution_records:
                _persist_entity_resolution_records(db, search_session=session, records=resolution_records)

            return {
                "query": q,
                "corrected_query": corrected_q,
                "category": category,
                "session_id": session_id,
                "primary_results": primary,
                "probable_results": probable_results[:20],
                "recommendations": secondary[:20],  # legacy compatibility: probable + related, capped at 20
                "total_primary": len(primary),
                "total_recommendations": len(secondary),
                "providers_responded": list(providers_responded),
                "providers_pending": providers_pending,
                "diagnostics": diagnostics,
                "search_intelligence": _si_intent.to_response_meta() if _si_intent else None,
                "discovery_report": discovery_report,
                # Legacy compatibility: cache_hits / cache_misses
                "cache_hits": {},
                "cache_misses": [],
            }

    # --- Path B: Cache fallback (for backwards compatibility) ---
    result = cache.get_all_providers(q, category, KNOWN_PROVIDERS)
    hits = {p: data for p, data in result.items() if data is not None}
    misses = [p for p, data in result.items() if data is None]

    # Build structured response from cache hits as well
    all_cached: List[dict] = []
    for provider_products in hits.values():
        if isinstance(provider_products, list):
            all_cached.extend(provider_products)

    primary_cache, secondary_cache = [], []
    discovery_query = _is_discovery_query(_si_intent)
    cache_diagnostics: dict[str, Any] = {"exact_match": exact_match, "discovery_query": discovery_query, "providers": {}}
    rejected_cache: list[dict[str, Any]] = []
    for product in all_cached:
        identity = None
        if exact_match and not discovery_query:
            try:
                identity = identity_engine.compare(user_query=q, selected_product=_selected_product_from_intent(q, _si_intent), category=category, provider_product=TrueCostProduct.model_validate(product))
            except Exception:
                identity = None
        s = identity.match_score if identity else score_product(q, product.get("name", ""), product.get("brand", "") or "")
        primary_threshold = 0.3 if discovery_query else 0.55
        related_threshold = 0.2 if discovery_query else 0.35
        match_tier = "primary" if identity and identity.match_tier in {"exact", "probable"} else identity.match_tier if identity else "primary" if s >= primary_threshold else "related" if s >= related_threshold else "discard"
        enriched = {**product, "matchScore": s, "matchTier": match_tier, **({"identity": identity.model_dump()} if identity else {})}
        prices = product.get("prices") if isinstance(product, dict) else []
        provider = "unknown"
        if isinstance(prices, list) and prices and isinstance(prices[0], dict):
            provider = str(prices[0].get("provider") or "unknown").strip().lower()
        provider_stats = cache_diagnostics["providers"].setdefault(provider, {"observed": 0, "exact_matches": 0, "related": 0, "rejected": 0, "best_rejected": []})
        provider_stats["observed"] += 1
        if match_tier == "primary":
            primary_cache.append(enriched)
            provider_stats["exact_matches"] += 1
        elif match_tier == "related":
            secondary_cache.append(enriched)
            provider_stats["related"] += 1
        else:
            provider_stats["rejected"] += 1
            rejected_cache.append(enriched)
            if len(provider_stats["best_rejected"]) < 3:
                provider_stats["best_rejected"].append({"name": product.get("name", ""), "brand": product.get("brand", ""), "score": s, "reason": identity.rejection_reason if identity else "Different model/brand or weak exact-title coverage"})

    if _si_intent is not None:
        try:
            primary_cache = classify_products_batch(_si_intent, primary_cache)
            secondary_cache = classify_products_batch(_si_intent, secondary_cache)
            newly_rejected_primary = [p for p in primary_cache if p.get("matchTier") == "rejected"]
            primary_cache = [p for p in primary_cache if p.get("matchTier") != "rejected"]
            rejected_cache.extend(newly_rejected_primary)
            newly_rejected_secondary = [p for p in secondary_cache if p.get("matchTier") == "rejected"]
            secondary_cache = [p for p in secondary_cache if p.get("matchTier") != "rejected"]
            rejected_cache.extend(newly_rejected_secondary)
            substitutes = [p for p in primary_cache if p.get("queryRelevance") == "SUBSTITUTE"]
            primary_cache = [p for p in primary_cache if p.get("queryRelevance") != "SUBSTITUTE"]
            secondary_cache = substitutes + secondary_cache
        except Exception:
            pass
    probable_cache = [p for p in secondary_cache if p.get("matchTier") == "probable"]
    related_cache = [p for p in secondary_cache if p.get("matchTier") != "probable"]
    _recount_provider_match_stats(
        cache_diagnostics,
        primary=primary_cache,
        probable=probable_cache,
        related=related_cache,
        rejected=rejected_cache,
    )

    cache_provider_status = {
        provider: {"state": "responded", **stats}
        for provider, stats in cache_diagnostics["providers"].items()
    }

    return {
        "query": q,
        "corrected_query": corrected_q,
        "search_intelligence": _si_intent.to_response_meta() if _si_intent else None,
        "category": category,
        "session_id": None,
        "primary_results": _balance_discovery_results(primary_cache) if discovery_query else primary_cache,
        "recommendations": (_balance_discovery_results(secondary_cache) if discovery_query else secondary_cache)[:20],
        "total_primary": len(primary_cache),
        "total_recommendations": len(secondary_cache),
        "providers_responded": list(hits.keys()),
        "providers_pending": misses,
        "diagnostics": cache_diagnostics,
        "discovery_report": _build_discovery_report(
            query=q,
            category=category,
            session_id=None,
            selected_product=_selected_product_from_intent(q, _si_intent),
            primary=primary_cache,
            related=secondary_cache[:20],
            rejected=rejected_cache,
            provider_status=cache_provider_status,
            provider_attempts=[{"provider": provider, "query": q, "state": "responded"} for provider in hits.keys()],
        ),
        # Legacy compatibility
        "cache_hits": hits,
        "cache_misses": misses,
        "stats": cache.stats(),
    }



@router.post("/ingest", response_model=List[TrueCostProduct], response_model_by_alias=True)
async def ingest_scraped_data(payload: IngestPayload, response: Response, db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    """
    Ingest raw scraped data from the Mobile Edge Scrapers.
    Normalizes via the typed Connector, caches the result, returns camelCase JSON.
    """

    provider_key = normalize_provider_key(payload.provider)

    if provider_key not in connectors:
        raise HTTPException(status_code=400, detail=f"Unknown provider: '{payload.provider}' (resolved to '{provider_key}'). Available: {list(connectors.keys())}")

    connector = connectors[provider_key]

    # ── Normalize raw_data shape ──────────────────────────────────────────────
    # Scrapers may send either a dict (provider internal API JSON) or a list of
    # product objects extracted by the WebView JS. Wrap list → dict so every
    # connector.parse_search_results() always receives a dict.
    raw = payload.raw_data
    if isinstance(raw, list):
        raw = {"items": raw, "_list_wrapped": True}

    logger.info(
        "ingest_received provider=%s category=%s raw_type=%s raw_len=%s selected_location=%s",
        provider_key,
        payload.category,
        "list" if payload.raw_data != raw else "dict",
        len(str(raw)),
        payload.selected_location.model_dump(exclude_none=True) if payload.selected_location else None,
    )

    try:
        normalized_products = connector.parse_search_results(raw)
        
        if not normalized_products:
            logger.warning("ingest_normalization_empty provider=%s category=%s query_len=%s", provider_key, payload.category, len(payload.query or ""))
        else:
            logger.info("ingest_normalized provider=%s category=%s count=%s", provider_key, payload.category, len(normalized_products))

        if normalized_products:
            # Cache stores camelCase so it's ready to serve directly to mobile
            serialized = [p.model_dump(by_alias=True) for p in normalized_products]
            
            user_id = None
            if credentials and credentials.scheme.lower() == "bearer":
                user_id = decode_token(credentials.credentials, "access")["sub"]
                if db.get(User, user_id) is None:
                    raise HTTPException(status_code=401, detail="User no longer exists")
            client_session_id = _valid_client_session_id(payload.search_session_id)
            session = db.get(SearchSession, client_session_id) if client_session_id else None
            if session is not None and session.user_id not in {None, user_id}:
                raise HTTPException(status_code=403, detail="Search session belongs to another user")
            if session is None:
                session = SearchSession(id=client_session_id, user_id=user_id, query=payload.query, category=payload.category) if client_session_id else SearchSession(user_id=user_id, query=payload.query, category=payload.category)
                db.add(session); db.flush()
            elif session.user_id is None and user_id is not None:
                session.user_id = user_id
            from app.services.entity_resolution import ResolutionDecision, SourceRecord, entity_resolution_service
            from app.repositories.grocery_observation_repository import grocery_observations
            
            resolved_serialized = []
            resolution_records = []
            selected_product = payload.selected_product_hint or {"name": payload.query}
            location = _location_payload(payload.selected_location)
            
            for tp in normalized_products:
                observed_at = datetime.now(timezone.utc).isoformat()
                product = tp.model_dump(by_alias=True)
                product["observedAt"] = observed_at
                # 6. Entity Resolution Shadow at Ingestion Boundary
                v3_ingest_active = (
                    settings.entity_resolution_mode != "legacy"
                    and not settings.entity_resolution_rollback_to_legacy
                    and str(payload.category or "").casefold().strip() in {"shopping", "grocery"}
                )
                if v3_ingest_active:
                    try:
                        if entity_resolution_service.supports(payload.category):
                            resolution = entity_resolution_service.resolve(
                                query=payload.query,
                                selected_product=selected_product,
                                category=payload.category,
                                source_record=SourceRecord(
                                    provider=provider_key,
                                    product=tp,
                                    observed_metadata={"observed_at": observed_at}
                                ),
                                enable_llm_extraction=settings.entity_resolution_llm_extraction_enabled,
                            )
                            resolution_payload = resolution.model_dump()
                            product["entityResolution"] = resolution_payload
                            product["matchScore"] = resolution.confidence
                            if resolution.decision == ResolutionDecision.EXACT:
                                product["matchTier"] = "primary"
                            elif resolution.decision == ResolutionDecision.PROBABLE:
                                product["matchTier"] = "probable"
                            elif resolution.decision == ResolutionDecision.RELATED:
                                product["matchTier"] = "related"
                            else:
                                product["matchTier"] = "rejected"
                            
                            resolution_records.append(resolution_payload)
                        else:
                            identity = identity_engine.compare(
                                user_query=payload.query,
                                selected_product=selected_product,
                                category=payload.category,
                                provider_product=tp,
                                observed_metadata={"observed_at": observed_at}
                            )
                            decision = identity.match_tier.upper() if identity else "REJECTED"
                            score = identity.match_score if identity else 0.0
                            product["matchScore"] = score
                            product["matchTier"] = "primary" if decision in {"EXACT", "PROBABLE"} else "related" if decision == "RELATED" else "rejected"
                            if identity:
                                product["identity"] = identity.model_dump()
                            record_payload = {
                                "decision": decision,
                                "confidence": score,
                                "resolver_version": f"{payload.category.lower()}.identity.v1",
                                "canonical_entity": {"attributes": {"name": payload.query, "category": payload.category}},
                                "provider_offer": {"provider": provider_key, "price": tp.prices[0].price if tp.prices else 0},
                                "raw_offer": product,
                                "legacy_decision": decision,
                                "disagreement": False,
                                "evidence": [{"factor": "identity", "result": "MATCH" if decision == "EXACT" else "REJECTED"}],
                                "conflicts": [],
                                "missing_factors": []
                            }
                            resolution_records.append(record_payload)
                    except Exception as e:
                        logger.warning("ingest_entity_resolution_failed provider=%s product_id=%s", provider_key, tp.id, exc_info=e)
                
                resolved_serialized.append(product)
            
            # Universal write to distributed / memory cache
            cache.set(payload.query, provider_key, payload.category, resolved_serialized, location=location)
            
            # Write to Grocery Observation Repository if Grocery category
            if payload.category.lower() == "grocery":
                grocery_observations.write_observations(payload.query, provider_key, resolved_serialized, location=location)
            else:
                from app.repositories.search_cache import search_cache as in_memory_search_cache
                in_memory_search_cache.store(payload.category, payload.query, resolved_serialized)
            
            for product in resolved_serialized:
                ingestion_key = _product_ingestion_key(session.id, provider_key, product)
                stmt = insert(IngestedProviderResult).values(
                    search_session_id=session.id,
                    provider=provider_key,
                    product_id=product.get("id", ""),
                    product=product,
                    ingestion_key=ingestion_key
                )
                stmt = stmt.on_conflict_do_nothing(index_elements=["search_session_id", "provider", "product_id", "ingestion_key"])
                db.execute(stmt)

                offers = product.get("prices") or []
                observed_prices = [float(offer["price"]) for offer in offers if isinstance(offer, dict) and offer.get("price") is not None]
                if observed_prices:
                    observed_price = min(observed_prices)
                    watches = db.scalars(select(PriceWatch).where(PriceWatch.active.is_(True), func.lower(PriceWatch.title) == str(product.get("name", "")).strip().lower())).all()
                    for watch in watches:
                        if watch.provider and watch.provider.strip().lower() not in {payload.provider.strip().lower(), provider_key}:
                            continue
                        watch.current_price = observed_price
                        db.add(PriceObservation(watch_id=watch.id, provider=provider_key, price=observed_price, source_session_id=session.id))
            
            db.commit()
            operation = db.get(ProviderOperationalState, provider_key)
            if operation is None:
                operation = ProviderOperationalState(provider_id=provider_key)
                db.add(operation)
            operation.last_ingested_at = datetime.now(timezone.utc)
            db.commit()
            if resolution_records:
                _persist_entity_resolution_records(db, search_session=session, records=resolution_records)
            response.headers["X-Search-Session-Id"] = session.id

        return normalized_products
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        detail = f"Error parsing data: {str(e)}" if settings.app_env.lower() in {"development", "test"} else "Provider data could not be normalized"
        raise HTTPException(status_code=500, detail=detail)


@router.post("/optimize")
async def optimize_basket(payload: OptimizePayload):
    """
    Takes a full basket across all platforms and returns the mathematically
    cheapest split, factoring in delivery fees.
    """
    try:
        result = TrueCostOptimizer.optimize_basket(payload.basket)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing basket: {str(e)}")


@router.get("/cache/stats")
async def get_cache_stats():
    """Developer endpoint to inspect the distributed cache state."""
    return cache.stats()


class MergePayload(BaseModel):
    products: List[TrueCostProduct]
    threshold: float = 0.75

@router.post("/merge", response_model=List[TrueCostProduct], response_model_by_alias=True)
async def merge_provider_results(payload: MergePayload):
    """
    Takes a flat list of products from multiple providers and merges
    them into canonical products with all provider prices compared side-by-side.
    Marks the cheapest price as isBest. Returns camelCase JSON.
    """
    try:
        merged = _merge_products(payload.products, payload.threshold)
        return merged
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Merge error: {str(e)}")




from app.graph.food_pharmacy_workflow import compile_food_pharmacy_workflow
from app.graph.evaluation_workflow import compile_evaluation_workflow

food_pharmacy_workflow = compile_food_pharmacy_workflow()
evaluation_workflow = compile_evaluation_workflow()

class GeneralSearchRequest(BaseModel):
    query: str
    category: str
    location: Optional[str] = None

@router.post("/search")
async def general_search(req: GeneralSearchRequest):
    # Unified search endpoint
    try:
        if req.category in ["food", "pharmacy"]:
            state = {"query": req.query, "category": req.category, "items": [], "ranked_options": [], "errors": []}
            result = await food_pharmacy_workflow.ainvoke(state)
            return {"status": "success", "engine": "food_pharmacy_workflow", "results": result.get("ranked_options", [])}
        elif req.category in ["finance", "services", "productivity"]:
            state = {"requirements": req.query, "domain": req.category, "candidates": [], "comparison_matrix": {}}
            result = await evaluation_workflow.ainvoke(state)
            return {"status": "success", "engine": "evaluation_workflow", "results": result.get("comparison_matrix", {})}
        else:
            raise HTTPException(status_code=400, detail="Category not supported in general search. Use specific endpoints.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
