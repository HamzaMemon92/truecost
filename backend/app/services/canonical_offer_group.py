from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

_WORD_RE = re.compile(r"\b[a-z0-9]+\b", re.I)
_MILK_SPECIALTY_TERMS = {
    "badam",
    "baby",
    "beverage",
    "calci",
    "camel",
    "coffee",
    "condensed",
    "drink",
    "elaichi",
    "flavour",
    "flavored",
    "kesar",
    "kool",
    "lactose",
    "mate",
    "mithai",
    "rose",
    "shake",
    "skimmed",
    "slim",
    "spray",
    "powder",
    "tetra",
    "thandai",
    "uht",
}
_MILK_PACK_TERMS = {"fresh", "milk", "pouch", "pack"}
_MILK_VARIANT_PRIORITY = {
    "gold": 7,
    "full": 4,
    "cream": 4,
    "taaza": 5,
    "taza": 5,
    "taja": 5,
    "toned": 5,
    "shakti": 4,
    "standard": 3,
    "standardised": 3,
    "standardized": 3,
}
_PROVIDER_FAILURE_STATES = {
    "timeout",
    "blocked",
    "rate_limited",
    "auth_failure",
    "network_failure",
    "parser_failure",
    "provider_unavailable",
    "location_unavailable",
    "unavailable",
    "pending",
}
_DISPLAYABLE_IMAGE_STATUSES = {"EXACT_SKU_IMAGE", "COMPATIBLE_SKU_IMAGE"}


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_price(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _entity_id_from_selected(selected_identity: dict[str, Any], query: str, category: str) -> str:
    explicit = selected_identity.get("entity_id") or selected_identity.get("identity_fingerprint")
    if explicit:
        return str(explicit)
    stable = f"{category.casefold()}|{query.casefold().strip()}"
    return f"tc_selected_{hashlib.sha256(stable.encode('utf-8')).hexdigest()[:24]}"


def _norm_words(value: Any) -> list[str]:
    return [match.group(0).casefold() for match in _WORD_RE.finditer(_safe_text(value))]


def _offer_product_name(offer: dict[str, Any]) -> str:
    product = offer.get("product") or {}
    evidence = offer.get("evidence") or {}
    return _safe_text(evidence.get("product_name") or product.get("name") or product.get("title"))


def _offer_weight(offer: dict[str, Any]) -> str:
    product = offer.get("product") or {}
    return _safe_text(product.get("weightVolume") or product.get("weight_volume")).casefold()


def _normalized_quantity_key(value: Any) -> str:
    text = _safe_text(value).casefold()
    if not text:
        return ""

    candidates = re.findall(r"(\d+(?:\.\d+)?)\s*(ml|millilitre|milliliter|l|lt|ltr|litre|liter|litres|liters|g|gram|kg|kilogram|pc|pcs|piece|pieces|unit|pack)\b", text)
    if not candidates:
        return re.sub(r"\s+", " ", text)

    pack_multiplier = _pack_multiplier(text)

    # Prefer the quantity inside pack descriptions: "1 pack (500 ml)" should
    # group as 500 ml, not as 1 pack. Keep true multipacks separate:
    # "1 ltr x 12" is a case/carton, not comparable with a single 1 L pack.
    qty, unit = candidates[-1]
    amount = float(qty)
    unit = unit.lower()
    if unit in {"l", "lt", "ltr", "litre", "liter", "litres", "liters"}:
        amount *= 1000
        unit = "ml"
    elif unit in {"kg", "kilogram"}:
        amount *= 1000
        unit = "g"
    elif unit in {"millilitre", "milliliter"}:
        unit = "ml"
    elif unit == "gram":
        unit = "g"
    elif unit in {"piece", "pieces"}:
        unit = "pc"
    amount_text = str(int(amount)) if amount.is_integer() else str(amount)
    key = f"{amount_text}{unit}"
    if pack_multiplier > 1:
        key = f"{key}x{pack_multiplier}"
    return key


def _pack_multiplier(text: str) -> int:
    patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:ml|millilitre|milliliter|l|lt|ltr|litre|liter|litres|liters|g|gram|kg|kilogram|pc|pcs|piece|pieces|unit|pack)\s*x\s*(\d+)\b",
        r"\b(\d+)\s*x\s*\d+(?:\.\d+)?\s*(?:ml|millilitre|milliliter|l|lt|ltr|litre|liter|litres|liters|g|gram|kg|kilogram|pc|pcs|piece|pieces|unit|pack)\b",
        r"\bpack\s+of\s+(\d+)\b",
        r"\b(\d+)\s*pack\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        try:
            value = int(match.group(1))
        except (TypeError, ValueError):
            continue
        if value > 1:
            return value
    return 1


def _group_text(group: dict[str, Any]) -> str:
    parts = [_safe_text(group.get("title"))]
    for offer in group.get("offers") or []:
        parts.append(_offer_product_name(offer))
        parts.append(_offer_weight(offer))
    return " ".join(part for part in parts if part)


def _milk_intent_sort_bonus(query: str, group: dict[str, Any]) -> int:
    query_words = set(_norm_words(query))
    if "milk" not in query_words and not {"amul", "taaza", "gold"} & query_words:
        return 0

    words = set(_norm_words(_group_text(group)))
    if "milk" not in words:
        return -10

    score = 0
    if "amul" in query_words and "amul" not in words:
        score -= 20
    if "amul" in query_words and "amul" in words:
        score += 8
    if words & _MILK_PACK_TERMS:
        score += 2
    if "pouch" in words:
        score += 3
    for word in words & set(_MILK_VARIANT_PRIORITY):
        score += _MILK_VARIANT_PRIORITY[word]
    if {"full", "cream"} <= words:
        score += 3

    requested_variants = query_words & set(_MILK_VARIANT_PRIORITY)
    if requested_variants:
        score += 10 * len(words & requested_variants)
    elif words & _MILK_SPECIALTY_TERMS:
        score -= 12

    return score


def _common_milk_pack_bonus(group: dict[str, Any]) -> int:
    words = set(_norm_words(_group_text(group)))
    weights = {_normalized_quantity_key(_offer_weight(offer)) for offer in group.get("offers") or []}
    score = 0
    if "500ml" in weights:
        score += 10
    if "1000ml" in weights:
        score += 4
    if "200ml" in weights or "180ml" in weights or "150ml" in weights:
        score -= 4
    if "pouch" in words:
        score += 5
    if "tetra" in words:
        score -= 5
    return score


def _group_sort_key(query: str, group: dict[str, Any]) -> tuple[int, int, int, float]:
    best_price = (
        group["best_offer"]["price"]
        if group.get("best_offer") and group["best_offer"].get("price") is not None
        else float("inf")
    )
    return (
        -int(group["evidence_summary"].get("exact_providers") or 0),
        -(_milk_intent_sort_bonus(query, group) + _common_milk_pack_bonus(group)),
        -int(group["evidence_summary"].get("exact_offers") or 0),
        float(best_price),
    )


def _provider_key(provider: Any) -> str:
    text = _safe_text(provider).casefold()
    if "swiggy" in text or "instamart" in text:
        return "swiggy"
    if "blinkit" in text:
        return "blinkit"
    if "zepto" in text:
        return "zepto"
    if "bigbasket" in text or "big basket" in text:
        return "bigbasket"
    return text


def _group_provider_status(group: dict[str, Any], provider_status: dict[str, Any] | None) -> dict[str, Any]:
    offer_counts: dict[str, int] = {}
    available_counts: dict[str, int] = {}
    sold_out_counts: dict[str, int] = {}
    offer_labels: dict[str, str] = {}
    for offer in group.get("offers") or []:
        provider = _safe_text(offer.get("provider"))
        key = _provider_key(provider)
        if not key:
            continue
        offer_counts[key] = offer_counts.get(key, 0) + 1
        if _offer_is_available(offer):
            available_counts[key] = available_counts.get(key, 0) + 1
        else:
            sold_out_counts[key] = sold_out_counts.get(key, 0) + 1
        offer_labels.setdefault(key, provider)

    scoped: dict[str, Any] = {}
    global_status = provider_status or {}
    for provider, status in global_status.items():
        provider_key = _provider_key(provider)
        if not provider_key:
            continue
        base = dict(status or {}) if isinstance(status, dict) else {"state": str(status)}
        label = offer_labels.get(provider_key) or provider
        if provider_key in offer_counts:
            scoped[label] = {
                **base,
                "state": base.get("state") or "responded",
                "exact_matches": offer_counts[provider_key],
                "observed": offer_counts[provider_key],
                "available_matches": available_counts.get(provider_key, 0),
                "sold_out": sold_out_counts.get(provider_key, 0),
                "match_status": "exact",
            }
            continue

        state = str(base.get("state") or "").casefold()
        if state in _PROVIDER_FAILURE_STATES:
            scoped[label] = {
                **base,
                "exact_matches": 0,
                "observed": 0,
                "match_status": "unknown" if state in {"timeout", "pending"} else "no_match",
            }
        elif state == "responded":
            scoped[label] = {
                **base,
                "exact_matches": 0,
                "observed": 0,
                "match_status": "no_match",
            }

    for provider_key, count in offer_counts.items():
        if any(_provider_key(provider) == provider_key for provider in scoped):
            continue
        label = offer_labels[provider_key]
        scoped[label] = {
            "state": "responded",
            "exact_matches": count,
            "observed": count,
            "available_matches": available_counts.get(provider_key, 0),
            "sold_out": sold_out_counts.get(provider_key, 0),
            "match_status": "exact",
        }

    return scoped


def _offer_is_available(offer: dict[str, Any]) -> bool:
    return offer.get("in_stock") is not False and offer.get("serviceable") is not False


def _unknown_attributes(product: dict[str, Any]) -> dict[str, Any]:
    raw = product.get("unknown_attributes") or product.get("unknownAttributes") or {}
    return raw if isinstance(raw, dict) else {}


def _product_image_url(product: dict[str, Any]) -> str:
    return _safe_text(product.get("imageUrl") or product.get("image_url"))


def _provider_sku(product: dict[str, Any]) -> str:
    return _safe_text(
        product.get("providerSku")
        or product.get("provider_sku")
        or product.get("sku")
        or product.get("sku_id")
        or product.get("id")
    )


def _image_status(product: dict[str, Any]) -> str:
    image_url = _product_image_url(product)
    if not image_url:
        return "NO_IMAGE"
    unknown = _unknown_attributes(product)
    status = _safe_text(unknown.get("image_match_status") or unknown.get("imageMatchStatus")).upper()
    if status:
        return status
    return "EXACT_SKU_IMAGE"


def _image_integrity_payload(product: dict[str, Any]) -> dict[str, Any]:
    unknown = _unknown_attributes(product)
    image_url = _product_image_url(product)
    status = _image_status(product)
    source_variant_id = _safe_text(
        unknown.get("image_source_variant_id")
        or unknown.get("imageSourceVariantId")
        or _provider_sku(product)
    )
    source_product_id = _safe_text(
        unknown.get("image_source_product_id")
        or unknown.get("imageSourceProductId")
        or product.get("id")
    )
    payload = {
        "image_url": image_url if status in _DISPLAYABLE_IMAGE_STATUSES else None,
        "raw_image_url": image_url or None,
        "image_match_status": status,
        "image_source_provider": unknown.get("image_source_provider") or unknown.get("imageSourceProvider"),
        "image_source_product_id": source_product_id or None,
        "image_source_variant_id": source_variant_id or None,
    }
    if image_url and status not in _DISPLAYABLE_IMAGE_STATUSES:
        print(
            "SKU_IMAGE_INTEGRITY_FAILURE",
            {
                "provider": product.get("provider") or (product.get("prices") or [{}])[0].get("provider"),
                "product_id": product.get("id"),
                "expected_size": product.get("weightVolume") or product.get("weight_volume"),
                "image_match_status": status,
            },
        )
    return payload


def _select_group_image(group: dict[str, Any]) -> str | None:
    for offer in group.get("offers") or []:
        status = _safe_text(offer.get("image_match_status")).upper()
        image_url = _safe_text(offer.get("image_url"))
        if image_url and status in _DISPLAYABLE_IMAGE_STATUSES:
            return image_url
    return None


def _entity_payload(product: dict[str, Any], selected_identity: dict[str, Any], fallback_entity_id: str) -> dict[str, Any]:
    resolution = product.get("entityResolution") or product.get("identity") or {}
    selected_entity = resolution.get("selected_entity") if isinstance(resolution, dict) else None
    canonical_entity = resolution.get("canonical_entity") if isinstance(resolution, dict) else None
    candidate_entity = resolution.get("candidate_entity") if isinstance(resolution, dict) else None
    selected_specific = _selected_grocery_signature_is_specific(selected_entity or selected_identity or {})
    candidate_compatible = _candidate_signature_contains_selected(selected_entity or selected_identity or {}, candidate_entity or {})
    decision = _safe_text(resolution.get("decision") if isinstance(resolution, dict) else "").upper()
    if decision == "EXACT" and selected_specific and candidate_compatible:
        entity = selected_entity or selected_identity or canonical_entity or candidate_entity or {}
    else:
        entity = candidate_entity or canonical_entity or selected_entity or selected_identity or {}
    return {
        "entity_id": entity.get("entity_id") or entity.get("identity_fingerprint") or fallback_entity_id,
        "entity_type": entity.get("entity_type") or selected_identity.get("entity_type"),
        "attributes": entity.get("attributes") or selected_identity.get("attributes") or {},
        "resolver_version": resolution.get("resolver_version") if isinstance(resolution, dict) else selected_identity.get("resolver_version"),
    }


def _signature_set(entity: dict[str, Any]) -> set[str]:
    attrs = entity.get("attributes") or {}
    raw = attrs.get("product_signature") or []
    if isinstance(raw, str):
        return set(_norm_words(raw))
    if isinstance(raw, list):
        return {_safe_text(item).casefold() for item in raw if _safe_text(item)}
    return set()


def _selected_grocery_signature_is_specific(entity: dict[str, Any]) -> bool:
    signature = _signature_set(entity)
    generic = {"milk", "bread", "soap", "chips", "flour", "atta", "dal", "rice", "oil"}
    return bool(signature - generic)


def _candidate_signature_contains_selected(selected_entity: dict[str, Any], candidate_entity: dict[str, Any]) -> bool:
    selected = _signature_set(selected_entity)
    candidate = _signature_set(candidate_entity)
    return bool(selected) and selected.issubset(candidate)


def _offer_payload(product: dict[str, Any], offer: dict[str, Any], *, entity_id: str, index: int) -> dict[str, Any]:
    provider = _safe_text(offer.get("provider") or product.get("provider") or "unknown")
    price = _safe_price(offer.get("price"))
    entity_observed_at = None
    if isinstance(product.get("entityResolution"), dict):
        entity_observed_at = (product.get("entityResolution") or {}).get("provider_offer", {}).get("freshness", {}).get("observed_at")
    observed_at = (
        product.get("observedAt")
        or product.get("observed_at")
        or offer.get("observedAt")
        or offer.get("observed_at")
        or entity_observed_at
        or datetime.now(timezone.utc).isoformat()
    )
    stable = f"{entity_id}|{provider.casefold()}|{product.get('id')}|{price}|{index}"
    image_payload = _image_integrity_payload(product)
    return {
        "offer_id": offer.get("offer_id") or f"tc_group_offer_{hashlib.sha256(stable.encode('utf-8')).hexdigest()[:24]}",
        "provider": provider,
        "price": price,
        "original_price": offer.get("originalPrice") or offer.get("original_price"),
        "currency": offer.get("currency") or "INR",
        "delivery_time": offer.get("deliveryTime") or offer.get("delivery_time"),
        "deep_link": offer.get("deepLink") or offer.get("deep_link") or offer.get("url") or product.get("url"),
        "product_url": offer.get("productUrl") or offer.get("product_url") or offer.get("url") or product.get("url"),
        "app_deep_link": offer.get("appDeepLink") or offer.get("app_deep_link"),
        "fallback_search_url": offer.get("fallbackSearchUrl") or offer.get("fallback_search_url"),
        "in_stock": offer.get("inStock") if isinstance(offer.get("inStock"), bool) else offer.get("in_stock"),
        "serviceable": offer.get("serviceable") if isinstance(offer.get("serviceable"), bool) else None,
        **image_payload,
        "freshness": {
            "observed_at": observed_at,
            "source": "ingested_provider_results",
        },
        "evidence": {
            "match_tier": product.get("matchTier"),
            "match_score": product.get("matchScore"),
            "product_id": product.get("id"),
            "product_name": product.get("name") or product.get("title"),
            "brand": product.get("brand"),
        },
        "product": product,
    }


def build_canonical_offer_groups(
    *,
    query: str,
    category: str,
    selected_identity: dict[str, Any],
    exact_results: list[dict[str, Any]],
    probable_results: list[dict[str, Any]] | None = None,
    related_results: list[dict[str, Any]] | None = None,
    rejected_results: list[dict[str, Any]] | None = None,
    provider_status: dict[str, Any] | None = None,
    resolution_mode: str = "shadow",
) -> list[dict[str, Any]]:
    """Compose exact entity matches into premium comparison groups.

    The interface deliberately accepts already-classified lanes. It never
    promotes PROBABLE/RELATED/REJECTED results into authoritative offers.
    """
    fallback_entity_id = _entity_id_from_selected(selected_identity or {}, query, category)
    groups: dict[str, dict[str, Any]] = {}

    for product in exact_results:
        entity = _entity_payload(product, selected_identity or {}, fallback_entity_id)
        entity_id = str(entity.get("entity_id") or fallback_entity_id)
        product_weight = _safe_text(product.get("weightVolume") or product.get("weight_volume"))
        size_key = _normalized_quantity_key(product_weight)
        group_key = f"{entity_id}|size:{size_key}" if size_key else entity_id
        group = groups.setdefault(
            group_key,
            {
                "group_id": f"tc_comparison_{hashlib.sha256(group_key.encode('utf-8')).hexdigest()[:24]}",
                "entity": entity,
                "title": product.get("name") or product.get("title") or query,
                "image_url": None,
                "category": category,
                "offers": [],
                "best_offer": None,
                "evidence_summary": {
                    "providers_checked": len(provider_status or {}),
                    "exact_offers": 0,
                    "probable_offers": len(probable_results or []),
                    "related_results": len(related_results or []),
                    "rejected_results": len(rejected_results or []),
                    "resolution_mode": resolution_mode,
                    "authoritative": resolution_mode == "v3",
                },
                "provider_status": {},
                "explanation": "",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        prices = product.get("prices") or []
        for index, offer in enumerate(prices):
            if isinstance(offer, dict):
                group["offers"].append(_offer_payload(product, offer, entity_id=entity_id, index=index))

    for group in groups.values():
        deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
        for offer in group["offers"]:
            key = (
                _safe_text(offer.get("provider")).casefold(),
                " ".join(_norm_words(_offer_product_name(offer))),
                _offer_weight(offer),
            )
            current = deduped.get(key)
            if current is None or (
                offer.get("price") is not None
                and (current.get("price") is None or float(offer["price"]) < float(current["price"]))
            ):
                deduped[key] = offer
        group["offers"] = list(deduped.values())
        group["offers"].sort(
            key=lambda item: (
                0 if _offer_is_available(item) else 1,
                item["price"] if item["price"] is not None else float("inf"),
            )
        )
        group["evidence_summary"]["exact_offers"] = len(group["offers"])
        group["evidence_summary"]["exact_providers"] = len({_safe_text(offer.get("provider")).casefold() for offer in group["offers"]})
        group["provider_status"] = _group_provider_status(group, provider_status)
        group["best_offer"] = next((offer for offer in group["offers"] if offer["price"] is not None and _offer_is_available(offer)), None)
        if group["best_offer"] is None:
            group["best_offer"] = next((offer for offer in group["offers"] if offer["price"] is not None), None)
        group["image_url"] = _select_group_image(group)
        if group["best_offer"]:
            group["explanation"] = (
                f"{group['best_offer']['provider']} has the lowest observed exact-offer price. "
                "Possible and related matches remain separated from this winner."
            )
        else:
            group["explanation"] = "Exact products were found, but no comparable price was present."

    return sorted(
        groups.values(),
        key=lambda group: _group_sort_key(query, group),
    )
