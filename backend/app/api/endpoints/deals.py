from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import IngestedProviderResult, SearchSession

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]


class Deal(BaseModel):
    id: str
    title: str
    provider: str
    category: str
    discount_pct: float | None = None
    cashback_pct: float | None = None
    cashback_amount: float | None = None
    min_order: float | None = None
    max_cashback: float | None = None
    valid_until: str | None = None
    payment_method: str | None = None
    deep_link: str
    terms: str
    is_expiring_soon: bool
    data_source: str


class DealsResponse(BaseModel):
    deals: list[Deal]
    total: int
    generated_at: str
    disclaimer: str


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return float(value)
    return None


def _expiring(value: str | None) -> bool:
    if not value:
        return False
    try:
        expiry = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        remaining = (expiry - datetime.now(timezone.utc)).total_seconds()
        return 0 <= remaining <= 3 * 24 * 60 * 60
    except ValueError:
        return False


def _deal_from_price(row: IngestedProviderResult, session: SearchSession, product: dict[str, Any], price: dict[str, Any], index: int) -> Deal | None:
    current = _number(price.get("price"))
    original = _number(price.get("originalPrice", price.get("original_price")))
    offers = product.get("offers") if isinstance(product.get("offers"), list) else []
    if not (current is not None and original is not None and original > current) and not offers:
        return None
    discount = round(((original - current) / original) * 100, 2) if current is not None and original else None
    provider = str(price.get("provider") or row.provider)
    valid_until = product.get("expiresAt") or product.get("expires_at")
    terms = "; ".join(str(item) for item in offers if item) or "Provider terms were not supplied with this observation. Verify eligibility at checkout."
    source = str(price.get("sourceType") or product.get("sourceType") or product.get("source_type") or "ingested_provider_result")
    return Deal(
        id=f"{row.id}:{index}",
        title=str(product.get("name") or product.get("title") or "Observed provider offer"),
        provider=provider,
        category=str(product.get("category") or session.category),
        discount_pct=discount,
        valid_until=str(valid_until) if valid_until else None,
        deep_link=str(price.get("deepLink") or price.get("deep_link") or product.get("sourceUrl") or product.get("source_url") or ""),
        terms=terms,
        is_expiring_soon=_expiring(str(valid_until) if valid_until else None),
        data_source=source,
    )


@router.get("", response_model=DealsResponse)
def list_observed_deals(
    db: Db,
    category: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
) -> DealsResponse:
    statement = (
        select(IngestedProviderResult, SearchSession)
        .join(SearchSession, IngestedProviderResult.search_session_id == SearchSession.id)
        .order_by(IngestedProviderResult.observed_at.desc())
        .limit(limit * 4)
    )
    if category:
        statement = statement.where(SearchSession.category.ilike(category))
    deals: list[Deal] = []
    seen: set[tuple[str, str]] = set()
    for row, session in db.execute(statement):
        product = row.product if isinstance(row.product, dict) else {}
        prices = product.get("prices") if isinstance(product.get("prices"), list) else []
        if not prices and isinstance(product, dict):
            prices = [product]
        for index, price in enumerate(prices):
            if not isinstance(price, dict):
                continue
            deal = _deal_from_price(row, session, product, price, index)
            if deal is None:
                continue
            key = (deal.provider.casefold(), deal.title.casefold())
            if key in seen:
                continue
            seen.add(key)
            deals.append(deal)
            if len(deals) >= limit:
                break
        if len(deals) >= limit:
            break
    return DealsResponse(
        deals=deals,
        total=len(deals),
        generated_at=datetime.now(timezone.utc).isoformat(),
        disclaimer="Deals are derived from persisted provider observations. Eligibility, terms, availability and final price must be confirmed with the provider.",
    )
