from __future__ import annotations

from datetime import datetime
import secrets
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.endpoints.auth import current_user
from app.db import get_db
from app.category_catalog import CATEGORY_CATALOG
from app.models import (
    Cart,
    CartItem,
    CartOptimization,
    Notification,
    PriceObservation,
    PriceWatch,
    SavedCollection,
    SavedCollectionItem,
    SavedItem,
    SearchSession,
    User,
    UserActivity,
)
from app.schemas.product import ProviderPrice, TrueCostProduct
from app.services.truecost_optimizer import TrueCostOptimizer

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(current_user)]


class SavedItemInput(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    source_url: str | None = None
    provider: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, ge=0)
    currency: str = Field(default="INR", min_length=1, max_length=12)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SavedItemResponse(SavedItemInput):
    id: str
    created_at: datetime
    updated_at: datetime


class PriceWatchInput(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    target_price: float = Field(ge=0)
    current_price: float | None = Field(default=None, ge=0)
    currency: str = Field(default="INR", min_length=1, max_length=12)
    source_url: str | None = None
    provider: str | None = Field(default=None, max_length=100)
    active: bool = True


class PriceWatchResponse(PriceWatchInput):
    id: str
    created_at: datetime
    updated_at: datetime


class PriceObservationResponse(BaseModel):
    id: str
    watch_id: str
    provider: str | None
    price: float
    source_session_id: str | None
    observed_at: datetime


class CartInput(BaseModel):
    name: str = Field(default="My cart", min_length=1, max_length=120)
    currency: str = Field(default="INR", min_length=1, max_length=12)


class CartItemInput(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    quantity: int = Field(default=1, ge=1, le=999)
    unit_price: float | None = Field(default=None, ge=0)
    provider: str | None = Field(default=None, max_length=100)
    source_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CartItemResponse(CartItemInput):
    id: str
    created_at: datetime
    updated_at: datetime


class CartResponse(CartInput):
    id: str
    created_at: datetime
    updated_at: datetime
    items: list[CartItemResponse]
    item_count: int
    estimated_total: float


class CartOptimizationInput(BaseModel):
    objective: str = Field(default="balanced", pattern="^(cheapest|balanced|fastest|single_retailer)$")


class CartOptimizationResponse(BaseModel):
    id: str
    cart_id: str
    version: int
    objective: str
    result: dict[str, Any]
    created_at: datetime


class HandoffInput(BaseModel):
    provider: str = Field(min_length=1, max_length=100)
    destination_url: str = Field(min_length=1, max_length=2000)
    expected_total: float | None = Field(default=None, ge=0)
    currency: str = Field(default="INR", max_length=12)
    source: str = Field(default="cart_optimization", max_length=80)
    reference_id: str | None = Field(default=None, max_length=100)


class ActivityResponse(BaseModel):
    id: str
    event_type: str
    title: str
    details: dict[str, Any]
    created_at: datetime


class DashboardSummary(BaseModel):
    saved_item_count: int
    active_price_watch_count: int
    cart_count: int
    cart_item_count: int
    estimated_cart_total: float
    recent_activity: list[ActivityResponse]


class NotificationResponse(BaseModel):
    id: str
    category: str
    title: str
    body: str
    deep_link: str | None
    read_at: datetime | None
    created_at: datetime


class CollectionInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class CollectionItemInput(BaseModel):
    saved_item_id: str
    note: str | None = Field(default=None, max_length=500)


class CollectionItemResponse(BaseModel):
    id: str
    note: str | None
    created_at: datetime
    item: SavedItemResponse


class CollectionResponse(CollectionInput):
    id: str
    is_shared: bool
    share_token: str | None
    item_count: int
    items: list[CollectionItemResponse]
    created_at: datetime
    updated_at: datetime


class PublicSavedItemResponse(BaseModel):
    id: str
    title: str
    source_url: str | None
    provider: str | None
    price: float | None
    currency: str
    created_at: datetime


class PublicCollectionItemResponse(BaseModel):
    id: str
    note: str | None
    created_at: datetime
    item: PublicSavedItemResponse


class SharedCollectionResponse(BaseModel):
    id: str
    name: str
    description: str | None
    item_count: int
    items: list[PublicCollectionItemResponse]
    updated_at: datetime


class ComparisonSummaryResponse(BaseModel):
    id: str
    query: str
    category: str
    provider_count: int
    result_count: int
    providers: list[str]
    created_at: datetime


class ComparisonObservationResponse(BaseModel):
    id: str
    provider: str
    product_id: str
    product: dict[str, Any]
    observed_at: datetime


class ComparisonDetailResponse(ComparisonSummaryResponse):
    observations: list[ComparisonObservationResponse]


class NotificationStatsResponse(BaseModel):
    total: int
    unread: int
    categories: dict[str, int]


class ActivitySummaryResponse(BaseModel):
    total_events: int
    event_groups: dict[str, int]
    comparison_count: int
    recent_comparisons: list[ComparisonSummaryResponse]


class CategoryCatalogResponse(BaseModel):
    id: str
    name: str
    engine_category: str
    capability: str
    providers: list[str]
    availability_verified: bool = False


def _saved_response(item: SavedItem) -> SavedItemResponse:
    return SavedItemResponse(id=item.id, title=item.title, source_url=item.source_url, provider=item.provider, price=item.price, currency=item.currency, metadata=item.metadata_ or {}, created_at=item.created_at, updated_at=item.updated_at)


def _watch_response(watch: PriceWatch) -> PriceWatchResponse:
    return PriceWatchResponse(id=watch.id, title=watch.title, target_price=watch.target_price, current_price=watch.current_price, currency=watch.currency, source_url=watch.source_url, provider=watch.provider, active=watch.active, created_at=watch.created_at, updated_at=watch.updated_at)


def _item_response(item: CartItem) -> CartItemResponse:
    return CartItemResponse(id=item.id, title=item.title, quantity=item.quantity, unit_price=item.unit_price, provider=item.provider, source_url=item.source_url, metadata=item.metadata_ or {}, created_at=item.created_at, updated_at=item.updated_at)


def _cart_response(cart: Cart) -> CartResponse:
    items = [_item_response(item) for item in cart.items]
    return CartResponse(id=cart.id, name=cart.name, currency=cart.currency, created_at=cart.created_at, updated_at=cart.updated_at, items=items, item_count=sum(item.quantity for item in cart.items), estimated_total=round(sum((item.unit_price or 0) * item.quantity for item in cart.items), 2))


def _collection_response(collection: SavedCollection) -> CollectionResponse:
    links = [
        CollectionItemResponse(
            id=link.id,
            note=link.note,
            created_at=link.created_at,
            item=_saved_response(link.saved_item),
        )
        for link in collection.item_links
    ]
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        is_shared=collection.is_shared,
        share_token=collection.share_token if collection.is_shared else None,
        item_count=len(links),
        items=links,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


def _comparison_summary(session: SearchSession) -> ComparisonSummaryResponse:
    providers = sorted({row.provider for row in session.observations})
    return ComparisonSummaryResponse(
        id=session.id,
        query=session.query,
        category=session.category,
        provider_count=len(providers),
        result_count=len(session.observations),
        providers=providers,
        created_at=session.created_at,
    )


def _comparison_detail(session: SearchSession) -> ComparisonDetailResponse:
    summary = _comparison_summary(session)
    return ComparisonDetailResponse(
        **summary.model_dump(),
        observations=[
            ComparisonObservationResponse(
                id=row.id,
                provider=row.provider,
                product_id=row.product_id,
                product=row.product or {},
                observed_at=row.observed_at,
            )
            for row in sorted(session.observations, key=lambda value: value.observed_at, reverse=True)
        ],
    )


def _activity(db: Session, user: User, event_type: str, title: str, **details: Any) -> None:
    privacy = (user.profile.preferences or {}).get("privacy", {}) if user.profile else {}
    if privacy.get("retain_activity") is False:
        return
    db.add(UserActivity(user_id=user.id, event_type=event_type, title=title, details=details))


def _owned(db: Session, model: Any, resource_id: str, user: User):
    resource = db.scalar(select(model).where(model.id == resource_id, model.user_id == user.id))
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


@router.get("/catalog/categories", response_model=list[CategoryCatalogResponse])
def category_catalog() -> list[CategoryCatalogResponse]:
    return [CategoryCatalogResponse(**item, availability_verified=False) for item in CATEGORY_CATALOG]


@router.get("/saved-items", response_model=list[SavedItemResponse])
def list_saved_items(db: Db, user: CurrentUser) -> list[SavedItemResponse]:
    return [_saved_response(item) for item in db.scalars(select(SavedItem).where(SavedItem.user_id == user.id).order_by(SavedItem.created_at.desc())).all()]


@router.post("/saved-items", response_model=SavedItemResponse, status_code=status.HTTP_201_CREATED)
def create_saved_item(payload: SavedItemInput, db: Db, user: CurrentUser) -> SavedItemResponse:
    item = SavedItem(user_id=user.id, title=payload.title, source_url=payload.source_url, provider=payload.provider, price=payload.price, currency=payload.currency, metadata_=payload.metadata)
    db.add(item)
    _activity(db, user, "saved_item.created", f"Saved {item.title}", saved_item_id=item.id)
    db.commit()
    db.refresh(item)
    return _saved_response(item)


@router.patch("/saved-items/{item_id}", response_model=SavedItemResponse)
def update_saved_item(item_id: str, payload: SavedItemInput, db: Db, user: CurrentUser) -> SavedItemResponse:
    item: SavedItem = _owned(db, SavedItem, item_id, user)
    for field, value in payload.model_dump().items():
        setattr(item, "metadata_" if field == "metadata" else field, value)
    _activity(db, user, "saved_item.updated", f"Updated saved item {item.title}", saved_item_id=item.id)
    db.commit()
    db.refresh(item)
    return _saved_response(item)


@router.delete("/saved-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_item(item_id: str, db: Db, user: CurrentUser) -> None:
    item: SavedItem = _owned(db, SavedItem, item_id, user)
    _activity(db, user, "saved_item.deleted", f"Removed saved item {item.title}", saved_item_id=item.id)
    db.delete(item)
    db.commit()


def _collection_query():
    return select(SavedCollection).execution_options(populate_existing=True).options(
        selectinload(SavedCollection.item_links).selectinload(SavedCollectionItem.saved_item)
    )


def _owned_collection(db: Session, collection_id: str, user: User) -> SavedCollection:
    collection = db.scalar(_collection_query().where(SavedCollection.id == collection_id, SavedCollection.user_id == user.id))
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return collection


@router.get("/collections", response_model=list[CollectionResponse])
def list_collections(db: Db, user: CurrentUser) -> list[CollectionResponse]:
    rows = db.scalars(_collection_query().where(SavedCollection.user_id == user.id).order_by(SavedCollection.updated_at.desc())).all()
    return [_collection_response(row) for row in rows]


@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionInput, db: Db, user: CurrentUser) -> CollectionResponse:
    collection = SavedCollection(user_id=user.id, **payload.model_dump())
    db.add(collection)
    _activity(db, user, "collection.created", f"Created list {collection.name}", collection_id=collection.id)
    db.commit()
    return _collection_response(_owned_collection(db, collection.id, user))


@router.patch("/collections/{collection_id}", response_model=CollectionResponse)
def update_collection(collection_id: str, payload: CollectionInput, db: Db, user: CurrentUser) -> CollectionResponse:
    collection = _owned_collection(db, collection_id, user)
    collection.name = payload.name
    collection.description = payload.description
    _activity(db, user, "collection.updated", f"Updated list {collection.name}", collection_id=collection.id)
    db.commit()
    return _collection_response(_owned_collection(db, collection.id, user))


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: str, db: Db, user: CurrentUser) -> None:
    collection = _owned_collection(db, collection_id, user)
    _activity(db, user, "collection.deleted", f"Removed list {collection.name}", collection_id=collection.id)
    db.delete(collection)
    db.commit()


@router.post("/collections/{collection_id}/items", response_model=CollectionResponse)
def add_collection_item(collection_id: str, payload: CollectionItemInput, db: Db, user: CurrentUser) -> CollectionResponse:
    collection = _owned_collection(db, collection_id, user)
    saved_item: SavedItem = _owned(db, SavedItem, payload.saved_item_id, user)
    existing = db.scalar(select(SavedCollectionItem).where(SavedCollectionItem.collection_id == collection.id, SavedCollectionItem.saved_item_id == saved_item.id))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item is already in this list")
    db.add(SavedCollectionItem(collection_id=collection.id, saved_item_id=saved_item.id, note=payload.note))
    _activity(db, user, "collection.item_added", f"Added {saved_item.title} to {collection.name}", collection_id=collection.id, saved_item_id=saved_item.id)
    db.commit()
    return _collection_response(_owned_collection(db, collection.id, user))


@router.patch("/collections/{collection_id}/items/{saved_item_id}", response_model=CollectionResponse)
def update_collection_item(collection_id: str, saved_item_id: str, payload: CollectionItemInput, db: Db, user: CurrentUser) -> CollectionResponse:
    collection = _owned_collection(db, collection_id, user)
    if payload.saved_item_id != saved_item_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Saved item id does not match route")
    link = db.scalar(select(SavedCollectionItem).where(SavedCollectionItem.collection_id == collection.id, SavedCollectionItem.saved_item_id == saved_item_id))
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    link.note = payload.note
    db.commit()
    return _collection_response(_owned_collection(db, collection.id, user))


@router.delete("/collections/{collection_id}/items/{saved_item_id}", response_model=CollectionResponse)
def remove_collection_item(collection_id: str, saved_item_id: str, db: Db, user: CurrentUser) -> CollectionResponse:
    collection = _owned_collection(db, collection_id, user)
    link = db.scalar(select(SavedCollectionItem).where(SavedCollectionItem.collection_id == collection.id, SavedCollectionItem.saved_item_id == saved_item_id))
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    db.delete(link)
    _activity(db, user, "collection.item_removed", f"Removed an item from {collection.name}", collection_id=collection.id, saved_item_id=saved_item_id)
    db.commit()
    return _collection_response(_owned_collection(db, collection.id, user))


@router.post("/collections/{collection_id}/share", response_model=CollectionResponse)
def share_collection(collection_id: str, db: Db, user: CurrentUser) -> CollectionResponse:
    collection = _owned_collection(db, collection_id, user)
    collection.is_shared = True
    collection.share_token = collection.share_token or secrets.token_urlsafe(24)
    _activity(db, user, "collection.shared", f"Shared list {collection.name}", collection_id=collection.id)
    db.commit()
    return _collection_response(_owned_collection(db, collection.id, user))


@router.delete("/collections/{collection_id}/share", response_model=CollectionResponse)
def stop_sharing_collection(collection_id: str, db: Db, user: CurrentUser) -> CollectionResponse:
    collection = _owned_collection(db, collection_id, user)
    collection.is_shared = False
    collection.share_token = None
    _activity(db, user, "collection.unshared", f"Stopped sharing {collection.name}", collection_id=collection.id)
    db.commit()
    return _collection_response(_owned_collection(db, collection.id, user))


@router.get("/shared-lists/{share_token}", response_model=SharedCollectionResponse)
def get_shared_collection(share_token: str, db: Db) -> SharedCollectionResponse:
    collection = db.scalar(_collection_query().where(SavedCollection.share_token == share_token, SavedCollection.is_shared.is_(True)))
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared list not found")
    return SharedCollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        item_count=len(collection.item_links),
        items=[
            PublicCollectionItemResponse(
                id=link.id,
                note=link.note,
                created_at=link.created_at,
                item=PublicSavedItemResponse(
                    id=link.saved_item.id,
                    title=link.saved_item.title,
                    source_url=link.saved_item.source_url,
                    provider=link.saved_item.provider,
                    price=link.saved_item.price,
                    currency=link.saved_item.currency,
                    created_at=link.saved_item.created_at,
                ),
            )
            for link in collection.item_links
        ],
        updated_at=collection.updated_at,
    )


@router.get("/price-watches", response_model=list[PriceWatchResponse])
def list_price_watches(db: Db, user: CurrentUser) -> list[PriceWatchResponse]:
    return [_watch_response(watch) for watch in db.scalars(select(PriceWatch).where(PriceWatch.user_id == user.id).order_by(PriceWatch.created_at.desc())).all()]


@router.post("/price-watches", response_model=PriceWatchResponse, status_code=status.HTTP_201_CREATED)
def create_price_watch(payload: PriceWatchInput, db: Db, user: CurrentUser) -> PriceWatchResponse:
    watch = PriceWatch(user_id=user.id, **payload.model_dump())
    db.add(watch)
    _activity(db, user, "price_watch.created", f"Watching {watch.title}", price_watch_id=watch.id, target_price=watch.target_price)
    notifications = (user.profile.preferences or {}).get("notification_preferences", {}) if user.profile else {}
    if notifications.get("price_drops") is not False:
        db.add(Notification(user_id=user.id, category="price", title=f"Watching {watch.title}", body=f"We will notify you when the observed price reaches {watch.currency} {watch.target_price:g} or lower.", deep_link="Watchlist"))
    db.commit()
    db.refresh(watch)
    return _watch_response(watch)


@router.patch("/price-watches/{watch_id}", response_model=PriceWatchResponse)
def update_price_watch(watch_id: str, payload: PriceWatchInput, db: Db, user: CurrentUser) -> PriceWatchResponse:
    watch: PriceWatch = _owned(db, PriceWatch, watch_id, user)
    for field, value in payload.model_dump().items():
        setattr(watch, field, value)
    _activity(db, user, "price_watch.updated", f"Updated watch {watch.title}", price_watch_id=watch.id)
    db.commit()
    db.refresh(watch)
    return _watch_response(watch)


@router.delete("/price-watches/{watch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_price_watch(watch_id: str, db: Db, user: CurrentUser) -> None:
    watch: PriceWatch = _owned(db, PriceWatch, watch_id, user)
    _activity(db, user, "price_watch.deleted", f"Removed watch {watch.title}", price_watch_id=watch.id)
    db.delete(watch)
    db.commit()


@router.get("/price-watches/{watch_id}/observations", response_model=list[PriceObservationResponse])
def list_price_observations(watch_id: str, db: Db, user: CurrentUser) -> list[PriceObservationResponse]:
    _owned(db, PriceWatch, watch_id, user)
    rows = db.scalars(select(PriceObservation).where(PriceObservation.watch_id == watch_id).order_by(PriceObservation.observed_at.desc()).limit(100)).all()
    return [PriceObservationResponse(id=row.id, watch_id=row.watch_id, provider=row.provider, price=row.price, source_session_id=row.source_session_id, observed_at=row.observed_at) for row in rows]


@router.get("/carts", response_model=list[CartResponse])
def list_carts(db: Db, user: CurrentUser) -> list[CartResponse]:
    carts = db.scalars(select(Cart).where(Cart.user_id == user.id).options(selectinload(Cart.items)).order_by(Cart.updated_at.desc())).all()
    return [_cart_response(cart) for cart in carts]


@router.post("/carts", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def create_cart(payload: CartInput, db: Db, user: CurrentUser) -> CartResponse:
    cart = Cart(user_id=user.id, **payload.model_dump())
    db.add(cart)
    _activity(db, user, "cart.created", f"Created cart {cart.name}", cart_id=cart.id)
    db.commit()
    db.refresh(cart)
    return _cart_response(cart)


@router.delete("/carts/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart(cart_id: str, db: Db, user: CurrentUser) -> None:
    cart: Cart = _owned(db, Cart, cart_id, user)
    _activity(db, user, "cart.deleted", f"Removed cart {cart.name}", cart_id=cart.id)
    db.delete(cart)
    db.commit()


@router.post("/carts/{cart_id}/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
def add_cart_item(cart_id: str, payload: CartItemInput, db: Db, user: CurrentUser) -> CartItemResponse:
    cart: Cart = _owned(db, Cart, cart_id, user)
    item = CartItem(cart_id=cart.id, title=payload.title, quantity=payload.quantity, unit_price=payload.unit_price, provider=payload.provider, source_url=payload.source_url, metadata_=payload.metadata)
    db.add(item)
    _activity(db, user, "cart_item.created", f"Added {item.title} to {cart.name}", cart_id=cart.id, cart_item_id=item.id)
    db.commit()
    db.refresh(item)
    return _item_response(item)


@router.patch("/carts/{cart_id}/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(cart_id: str, item_id: str, payload: CartItemInput, db: Db, user: CurrentUser) -> CartItemResponse:
    _owned(db, Cart, cart_id, user)
    item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart_id))
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    for field, value in payload.model_dump().items():
        setattr(item, "metadata_" if field == "metadata" else field, value)
    _activity(db, user, "cart_item.updated", f"Updated cart item {item.title}", cart_id=cart_id, cart_item_id=item.id)
    db.commit()
    db.refresh(item)
    return _item_response(item)


@router.delete("/carts/{cart_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart_item(cart_id: str, item_id: str, db: Db, user: CurrentUser) -> None:
    cart: Cart = _owned(db, Cart, cart_id, user)
    item = db.scalar(select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id))
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    _activity(db, user, "cart_item.deleted", f"Removed {item.title} from {cart.name}", cart_id=cart.id, cart_item_id=item.id)
    db.delete(item)
    db.commit()


def _optimization_response(row: CartOptimization) -> CartOptimizationResponse:
    return CartOptimizationResponse(id=row.id, cart_id=row.cart_id, version=row.version, objective=row.objective, result=row.result or {}, created_at=row.created_at)


def _optimizer_groups(cart: Cart) -> tuple[list[list[TrueCostProduct]], list[str]]:
    groups: list[list[TrueCostProduct]] = []
    missing: list[str] = []
    for item in cart.items:
        metadata = item.metadata_ or {}
        raw_offers = metadata.get("offers") or metadata.get("prices") or []
        offers: list[ProviderPrice] = []
        for raw in raw_offers if isinstance(raw_offers, list) else []:
            if not isinstance(raw, dict) or raw.get("price") is None or not raw.get("provider"):
                continue
            offers.append(ProviderPrice(
                provider=str(raw["provider"]),
                price=float(raw["price"]),
                original_price=raw.get("originalPrice", raw.get("original_price")),
                delivery_time=str(raw.get("deliveryTime", raw.get("delivery_time", ""))),
                is_best=bool(raw.get("isBest", raw.get("is_best", False))),
                deep_link=raw.get("deepLink", raw.get("deep_link")),
            ))
        if not offers and item.provider and item.unit_price is not None:
            offers.append(ProviderPrice(provider=item.provider, price=item.unit_price, deep_link=item.source_url))
        if not offers:
            missing.append(item.title)
            continue
        product = TrueCostProduct(
            id=str(metadata.get("product_id") or item.id),
            name=item.title,
            brand=str(metadata.get("brand") or ""),
            weight_volume=str(metadata.get("weight_volume") or ""),
            image_url=str(metadata.get("image_url") or ""),
            category=str(metadata.get("category") or "Grocery"),
            prices=offers,
        )
        for _ in range(item.quantity):
            groups.append([product])
    return groups, missing


@router.post("/carts/{cart_id}/optimize", response_model=CartOptimizationResponse, status_code=status.HTTP_201_CREATED)
def optimize_cart(cart_id: str, payload: CartOptimizationInput, db: Db, user: CurrentUser) -> CartOptimizationResponse:
    cart = db.scalar(select(Cart).where(Cart.id == cart_id, Cart.user_id == user.id).options(selectinload(Cart.items)))
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    if not cart.items:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Add at least one cart item before optimizing")
    groups, missing = _optimizer_groups(cart)
    if not groups:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No observed provider offers are available for this cart")
    result = TrueCostOptimizer.optimize_basket(groups)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result["error"])
    financials = result.get("financials", {})
    single = financials.get("single_store_alternative")
    total = financials.get("grand_total")
    provider_destinations: dict[str, str] = {}
    for item in cart.items:
        for offer in (item.metadata_ or {}).get("offers", []):
            if isinstance(offer, dict):
                provider = offer.get("provider")
                destination = offer.get("deepLink") or offer.get("deep_link")
                if provider and destination:
                    provider_destinations.setdefault(str(provider), str(destination))
    result.update({
        "missing_items": missing,
        "complete": not missing,
        "savings_vs_single_store": round(max(0, single - total), 2) if not missing and single is not None and total is not None else None,
        "assumptions": [
            "Prices and links are provider observations supplied to TrueCost.",
            "Fees are deterministic estimates from the deployed optimizer and may change at provider checkout.",
            "Availability and final payable amount must be reconfirmed by the selected provider.",
        ],
        "objective_requested": payload.objective,
        "objective_applied": "cheapest",
        "provider_destinations": provider_destinations,
    })
    version = (db.scalar(select(func.max(CartOptimization.version)).where(CartOptimization.cart_id == cart.id)) or 0) + 1
    row = CartOptimization(cart_id=cart.id, version=version, objective=payload.objective, result=result)
    db.add(row)
    _activity(db, user, "cart.optimized", f"Optimized {cart.name}", cart_id=cart.id, optimization_id=row.id, version=version, objective=payload.objective)
    db.commit()
    db.refresh(row)
    return _optimization_response(row)


@router.get("/carts/{cart_id}/optimizations", response_model=list[CartOptimizationResponse])
def list_cart_optimizations(cart_id: str, db: Db, user: CurrentUser) -> list[CartOptimizationResponse]:
    _owned(db, Cart, cart_id, user)
    rows = db.scalars(select(CartOptimization).where(CartOptimization.cart_id == cart_id).order_by(CartOptimization.version.desc())).all()
    return [_optimization_response(row) for row in rows]


@router.post("/handoffs", status_code=status.HTTP_201_CREATED)
def record_handoff(payload: HandoffInput, db: Db, user: CurrentUser) -> dict[str, str]:
    _activity(db, user, "handoff.opened", f"Opened {payload.provider}", provider=payload.provider, destination_url=payload.destination_url, expected_total=payload.expected_total, currency=payload.currency, source=payload.source, reference_id=payload.reference_id)
    db.commit()
    return {"status": "recorded"}


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Db, user: CurrentUser) -> DashboardSummary:
    carts = db.scalars(select(Cart).where(Cart.user_id == user.id).options(selectinload(Cart.items))).all()
    return DashboardSummary(
        saved_item_count=db.scalar(select(func.count()).select_from(SavedItem).where(SavedItem.user_id == user.id)) or 0,
        active_price_watch_count=db.scalar(select(func.count()).select_from(PriceWatch).where(PriceWatch.user_id == user.id, PriceWatch.active.is_(True))) or 0,
        cart_count=len(carts),
        cart_item_count=sum(item.quantity for cart in carts for item in cart.items),
        estimated_cart_total=round(sum((item.unit_price or 0) * item.quantity for cart in carts for item in cart.items), 2),
        recent_activity=[ActivityResponse(id=row.id, event_type=row.event_type, title=row.title, details=row.details or {}, created_at=row.created_at) for row in db.scalars(select(UserActivity).where(UserActivity.user_id == user.id).order_by(UserActivity.created_at.desc()).limit(10)).all()],
    )


@router.get("/activity", response_model=list[ActivityResponse])
def list_activity(
    db: Db,
    user: CurrentUser,
    limit: int = Query(default=25, ge=1, le=100),
    group: str | None = Query(default=None, max_length=30),
) -> list[ActivityResponse]:
    statement = select(UserActivity).where(UserActivity.user_id == user.id)
    prefixes = {"saved": "saved_item.", "watches": "price_watch.", "carts": "cart", "lists": "collection.", "handoffs": "handoff."}
    if group in prefixes:
        statement = statement.where(UserActivity.event_type.startswith(prefixes[group]))
    rows = db.scalars(statement.order_by(UserActivity.created_at.desc()).limit(limit)).all()
    return [ActivityResponse(id=row.id, event_type=row.event_type, title=row.title, details=row.details or {}, created_at=row.created_at) for row in rows]


@router.get("/comparisons", response_model=list[ComparisonSummaryResponse])
def list_comparisons(
    db: Db,
    user: CurrentUser,
    category: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=30, ge=1, le=100),
) -> list[ComparisonSummaryResponse]:
    statement = select(SearchSession).where(SearchSession.user_id == user.id).options(selectinload(SearchSession.observations))
    if category:
        statement = statement.where(SearchSession.category == category)
    sessions = db.scalars(statement.order_by(SearchSession.created_at.desc()).limit(limit)).all()
    return [_comparison_summary(session) for session in sessions]


@router.get("/comparisons/{comparison_id}", response_model=ComparisonDetailResponse)
def get_comparison(comparison_id: str, db: Db, user: CurrentUser) -> ComparisonDetailResponse:
    session = db.scalar(
        select(SearchSession)
        .where(SearchSession.id == comparison_id, SearchSession.user_id == user.id)
        .options(selectinload(SearchSession.observations))
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return _comparison_detail(session)


@router.get("/activity/summary", response_model=ActivitySummaryResponse)
def activity_summary(db: Db, user: CurrentUser) -> ActivitySummaryResponse:
    activity_rows = db.execute(
        select(UserActivity.event_type, func.count(UserActivity.id))
        .where(UserActivity.user_id == user.id)
        .group_by(UserActivity.event_type)
    ).all()
    grouped = {"saved": 0, "watches": 0, "carts": 0, "lists": 0, "handoffs": 0, "other": 0}
    for event_type, count in activity_rows:
        if event_type.startswith("saved_item."):
            grouped["saved"] += count
        elif event_type.startswith("price_watch."):
            grouped["watches"] += count
        elif event_type.startswith("cart"):
            grouped["carts"] += count
        elif event_type.startswith("collection."):
            grouped["lists"] += count
        elif event_type.startswith("handoff."):
            grouped["handoffs"] += count
        else:
            grouped["other"] += count
    sessions = db.scalars(
        select(SearchSession)
        .where(SearchSession.user_id == user.id)
        .options(selectinload(SearchSession.observations))
        .order_by(SearchSession.created_at.desc())
        .limit(5)
    ).all()
    return ActivitySummaryResponse(
        total_events=sum(grouped.values()),
        event_groups=grouped,
        comparison_count=db.scalar(select(func.count()).select_from(SearchSession).where(SearchSession.user_id == user.id)) or 0,
        recent_comparisons=[_comparison_summary(session) for session in sessions],
    )


def _notification_response(row: Notification) -> NotificationResponse:
    return NotificationResponse(id=row.id, category=row.category, title=row.title, body=row.body, deep_link=row.deep_link, read_at=row.read_at, created_at=row.created_at)


@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(
    db: Db,
    user: CurrentUser,
    category: str | None = Query(default=None, max_length=40),
    unread_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
) -> list[NotificationResponse]:
    statement = select(Notification).where(Notification.user_id == user.id)
    if category:
        statement = statement.where(Notification.category == category)
    if unread_only:
        statement = statement.where(Notification.read_at.is_(None))
    return [_notification_response(row) for row in db.scalars(statement.order_by(Notification.created_at.desc()).limit(limit)).all()]


@router.get("/notifications/stats", response_model=NotificationStatsResponse)
def notification_stats(db: Db, user: CurrentUser) -> NotificationStatsResponse:
    rows = db.execute(
        select(Notification.category, func.count(Notification.id))
        .where(Notification.user_id == user.id)
        .group_by(Notification.category)
    ).all()
    categories = {category: count for category, count in rows}
    return NotificationStatsResponse(
        total=sum(categories.values()),
        unread=db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))) or 0,
        categories=categories,
    )


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: str, db: Db, user: CurrentUser) -> NotificationResponse:
    row = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    if row.read_at is None:
        row.read_at = datetime.now().astimezone()
        db.commit()
        db.refresh(row)
    return _notification_response(row)


@router.post("/notifications/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(db: Db, user: CurrentUser, category: str | None = Query(default=None, max_length=40)) -> None:
    statement = select(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    if category:
        statement = statement.where(Notification.category == category)
    rows = db.scalars(statement).all()
    for row in rows:
        row.read_at = datetime.now().astimezone()
    db.commit()
