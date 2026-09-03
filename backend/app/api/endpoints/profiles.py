from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.endpoints.auth import current_user, require_user_ownership
from app.db import get_db
from app.models import BrokerRevocationOutbox, PaymentPreference, SavedAddress, User, UserActivity, UserProfile
from app.security import decode_token, verify_password
from app.category_catalog import SUPPORTED_CATEGORY_NAMES

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(current_user)]

SUPPORTED_CATEGORIES = SUPPORTED_CATEGORY_NAMES
SUPPORTED_DIETARY = {"vegetarian", "vegan", "eggetarian", "halal", "kosher", "gluten_free", "lactose_free", "nut_free", "low_sugar"}


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    preferences: dict | None = None


class AccountDeleteInput(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=256)
    reauthentication_token: str | None = Field(default=None, min_length=20)


class ProfileResponse(BaseModel):
    user_id: str
    email: str | None
    phone_number: str | None = None
    display_name: str | None
    preferences: dict


class NotificationPreferencePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    price_drops: bool | None = None
    travel_alerts: bool | None = None
    savings_updates: bool | None = None
    deals: bool | None = None
    account_updates: bool | None = None


class AccessibilityPreferencePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reduced_motion: bool | None = None
    larger_text: bool | None = None
    high_contrast: bool | None = None
    screen_reader_hints: bool | None = None


class PrivacyPreferencePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    personalized_recommendations: bool | None = None
    retain_activity: bool | None = None
    save_location_history: bool | None = None
    product_analytics: bool | None = None


class ProfilePreferencePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    objective: Literal["cheapest", "balanced", "fastest"] | None = None
    delivery_preference: Literal["cheapest", "balanced", "fastest"] | None = None
    preferred_categories: list[str] | None = Field(default=None, max_length=16)
    preferred_providers: list[str] | None = Field(default=None, max_length=32)
    dietary: list[str] | None = Field(default=None, max_length=16)
    notification_preferences: NotificationPreferencePatch | None = None
    accessibility: AccessibilityPreferencePatch | None = None
    privacy: PrivacyPreferencePatch | None = None
    language: str | None = Field(default=None, min_length=2, max_length=12)
    region: str | None = Field(default=None, min_length=2, max_length=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    monthly_budget: float | None = Field(default=None, ge=0)

    @field_validator("preferred_categories")
    @classmethod
    def validate_categories(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        normalized = list(dict.fromkeys(item.strip() for item in value if item.strip()))
        unknown = sorted(set(normalized) - SUPPORTED_CATEGORIES)
        if unknown:
            raise ValueError(f"Unsupported categories: {', '.join(unknown)}")
        return normalized

    @field_validator("dietary")
    @classmethod
    def validate_dietary(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        normalized = list(dict.fromkeys(item.strip().lower() for item in value if item.strip()))
        unknown = sorted(set(normalized) - SUPPORTED_DIETARY)
        if unknown:
            raise ValueError(f"Unsupported dietary preferences: {', '.join(unknown)}")
        return normalized

    @field_validator("preferred_providers")
    @classmethod
    def validate_providers(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        normalized = list(dict.fromkeys(item.strip() for item in value if item.strip()))
        if any(len(item) > 100 for item in normalized):
            raise ValueError("Provider names must be 100 characters or fewer")
        return normalized

    @field_validator("region", "currency")
    @classmethod
    def uppercase_codes(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class AddressInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1, max_length=80)
    address_line: str = Field(min_length=2, max_length=300)
    locality: str | None = Field(default=None, max_length=120)
    city: str = Field(min_length=1, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    postal_code: str = Field(min_length=3, max_length=24)
    country_code: str = Field(default="IN", min_length=2, max_length=2)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    is_default: bool = False

    @field_validator("country_code")
    @classmethod
    def uppercase_country(cls, value: str) -> str:
        return value.upper()


class AddressResponse(AddressInput):
    id: str
    created_at: datetime
    updated_at: datetime


PaymentType = Literal["card", "upi", "wallet", "net_banking"]


class PaymentPreferenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    method_type: PaymentType
    label: str = Field(min_length=1, max_length=100)
    issuer: str | None = Field(default=None, max_length=100)
    network: str | None = Field(default=None, max_length=40)
    last4: str | None = Field(default=None, max_length=4)
    masked_identifier: str | None = Field(default=None, max_length=120)
    benefit_tags: list[str] = Field(default_factory=list, max_length=12)
    is_preferred: bool = False

    @model_validator(mode="after")
    def validate_safe_metadata(self) -> "PaymentPreferenceInput":
        if self.last4 and (len(self.last4) != 4 or not self.last4.isdigit()):
            raise ValueError("last4 must contain exactly four digits")
        if self.masked_identifier and (len("".join(char for char in self.masked_identifier if char.isdigit())) > 4 or (self.method_type in {"upi", "wallet"} and "*" not in self.masked_identifier)):
            raise ValueError("Only masked payment identifiers with at most four visible digits may be stored")
        if self.method_type == "card" and not self.last4:
            raise ValueError("A card requires only its final four digits")
        if self.method_type == "upi" and (not self.masked_identifier or "@" not in self.masked_identifier or "*" not in self.masked_identifier):
            raise ValueError("UPI identifiers must be masked, for example a***@bank")
        if self.method_type == "net_banking" and not self.issuer:
            raise ValueError("A bank name is required; account numbers are not accepted")
        self.benefit_tags = list(dict.fromkeys(tag.strip() for tag in self.benefit_tags if tag.strip()))
        if any(len(tag) > 80 for tag in self.benefit_tags):
            raise ValueError("Benefit labels must be 80 characters or fewer")
        return self


class PaymentPreferenceResponse(PaymentPreferenceInput):
    id: str
    created_at: datetime
    updated_at: datetime


class ServiceabilityResponse(BaseModel):
    address_id: str
    category: str | None
    status: Literal["verification_required"] = "verification_required"
    can_request_comparison: bool
    checked_providers: list[str] = Field(default_factory=list)
    message: str


def _response(user: User) -> ProfileResponse:
    profile = user.profile or UserProfile(user_id=user.id)
    public_email = None if user.email.endswith("@phone.truecost.invalid") else user.email
    phone = user.phone_identities[0].phone_number if user.phone_identities else None
    return ProfileResponse(user_id=user.id, email=public_email, phone_number=phone, display_name=profile.display_name, preferences=profile.preferences or {})


def _activity(db: Session, user: User, event_type: str, title: str, **details: Any) -> None:
    privacy = (user.profile.preferences or {}).get("privacy", {}) if user.profile else {}
    if privacy.get("retain_activity") is False:
        return
    db.add(UserActivity(user_id=user.id, event_type=event_type, title=title, details=details))


def _deep_merge(current: dict, patch: dict) -> dict:
    result = dict(current)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _address_response(row: SavedAddress) -> AddressResponse:
    return AddressResponse(id=row.id, label=row.label, address_line=row.address_line, locality=row.locality, city=row.city, state=row.state, postal_code=row.postal_code, country_code=row.country_code, latitude=row.latitude, longitude=row.longitude, is_default=row.is_default, created_at=row.created_at, updated_at=row.updated_at)


def _payment_response(row: PaymentPreference) -> PaymentPreferenceResponse:
    return PaymentPreferenceResponse(id=row.id, method_type=row.method_type, label=row.label, issuer=row.issuer, network=row.network, last4=row.last4, masked_identifier=row.masked_identifier, benefit_tags=(row.metadata_ or {}).get("benefit_tags", []), is_preferred=row.is_preferred, created_at=row.created_at, updated_at=row.updated_at)


def _owned_address(db: Session, address_id: str, user: User) -> SavedAddress:
    row = db.scalar(select(SavedAddress).where(SavedAddress.id == address_id, SavedAddress.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return row


def _owned_payment(db: Session, payment_id: str, user: User) -> PaymentPreference:
    row = db.scalar(select(PaymentPreference).where(PaymentPreference.id == payment_id, PaymentPreference.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return row


def _clear_default_addresses(db: Session, user: User, except_id: str | None = None) -> None:
    rows = db.scalars(select(SavedAddress).where(SavedAddress.user_id == user.id, SavedAddress.is_default.is_(True))).all()
    for row in rows:
        if row.id != except_id:
            row.is_default = False


def _clear_preferred_payments(db: Session, user: User, except_id: str | None = None) -> None:
    rows = db.scalars(select(PaymentPreference).where(PaymentPreference.user_id == user.id, PaymentPreference.is_preferred.is_(True))).all()
    for row in rows:
        if row.id != except_id:
            row.is_preferred = False


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(user: CurrentUser) -> ProfileResponse:
    return _response(user)


@router.put("/me", response_model=ProfileResponse)
def update_my_profile(payload: ProfileUpdate, db: Db, user: CurrentUser) -> ProfileResponse:
    return _update_profile(payload, db, user)


@router.patch("/me/preferences", response_model=ProfileResponse)
def patch_my_preferences(payload: ProfilePreferencePatch, db: Db, user: CurrentUser) -> ProfileResponse:
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    patch = payload.model_dump(exclude_unset=True)
    profile.preferences = _deep_merge(profile.preferences or {}, patch)
    _activity(db, user, "profile.preferences_updated", "Updated decision preferences", fields=sorted(patch))
    db.commit()
    db.refresh(user)
    return _response(user)


@router.get("/me/export")
def export_my_account(user: CurrentUser) -> dict:
    profile = user.profile
    return {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "account": {
            "id": user.id,
            "email": None if user.email.endswith("@phone.truecost.invalid") else user.email,
            "phone_number": user.phone_identities[0].phone_number if user.phone_identities else None,
            "created_at": user.created_at.isoformat(),
        },
        "profile": {"display_name": profile.display_name if profile else None, "preferences": (profile.preferences or {}) if profile else {}},
        "saved_addresses": [{"id": row.id, "label": row.label, "address_line": row.address_line, "locality": row.locality, "city": row.city, "state": row.state, "postal_code": row.postal_code, "country_code": row.country_code, "latitude": row.latitude, "longitude": row.longitude, "is_default": row.is_default} for row in user.saved_addresses],
        "payment_preferences": [{"id": row.id, "method_type": row.method_type, "label": row.label, "issuer": row.issuer, "network": row.network, "last4": row.last4, "masked_identifier": row.masked_identifier, "metadata": row.metadata_, "is_preferred": row.is_preferred} for row in user.payment_preferences],
        "provider_connections": [{"provider_id": row.provider_id, "status": row.status, "account_label": row.account_label, "connected_at": row.connected_at.isoformat(), "expires_at": row.expires_at.isoformat() if row.expires_at else None} for row in user.provider_connections],
        "saved_items": [{"id": row.id, "title": row.title, "provider": row.provider, "price": row.price, "currency": row.currency, "source_url": row.source_url, "metadata": row.metadata_} for row in user.saved_items],
        "price_watches": [{"id": row.id, "title": row.title, "target_price": row.target_price, "current_price": row.current_price, "currency": row.currency, "provider": row.provider, "active": row.active} for row in user.price_watches],
        "carts": [{"id": row.id, "name": row.name, "currency": row.currency, "items": [{"id": item.id, "title": item.title, "quantity": item.quantity, "unit_price": item.unit_price, "provider": item.provider, "metadata": item.metadata_} for item in row.items]} for row in user.carts],
        "recent_activity": [{"event_type": row.event_type, "title": row.title, "details": row.details, "created_at": row.created_at.isoformat()} for row in user.activities],
    }


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(payload: AccountDeleteInput, db: Db, user: CurrentUser) -> None:
    password_valid = bool(payload.password and verify_password(payload.password, user.password_hash))
    reauth_valid = False
    if payload.reauthentication_token:
        claims = decode_token(payload.reauthentication_token, "reauth")
        reauth_valid = claims["sub"] == user.id
    if not password_valid and not reauth_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Recent account verification is required")
    for connection in user.provider_connections:
        if connection.broker_subject_ref:
            db.add(BrokerRevocationOutbox(connection_id=connection.id, user_id=user.id, provider_id=connection.provider_id, subject_ref=connection.broker_subject_ref))
    db.delete(user)
    db.commit()


def _update_profile(payload: ProfileUpdate, db: Session, user: User) -> ProfileResponse:
    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    if "display_name" in payload.model_fields_set:
        profile.display_name = payload.display_name.strip() if payload.display_name else None
    if "preferences" in payload.model_fields_set:
        profile.preferences = payload.preferences or {}
    _activity(db, user, "profile.updated", "Updated profile")
    db.commit()
    db.refresh(user)
    return _response(user)


@router.get("/me/addresses", response_model=list[AddressResponse])
def list_addresses(db: Db, user: CurrentUser) -> list[AddressResponse]:
    rows = db.scalars(select(SavedAddress).where(SavedAddress.user_id == user.id).order_by(SavedAddress.is_default.desc(), SavedAddress.updated_at.desc())).all()
    return [_address_response(row) for row in rows]


@router.post("/me/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressInput, db: Db, user: CurrentUser) -> AddressResponse:
    count = len(db.scalars(select(SavedAddress.id).where(SavedAddress.user_id == user.id)).all())
    values = payload.model_dump()
    values["is_default"] = payload.is_default or count == 0
    if values["is_default"]:
        _clear_default_addresses(db, user)
    row = SavedAddress(user_id=user.id, **values)
    db.add(row)
    _activity(db, user, "address.created", f"Saved {row.label}", address_id=row.id)
    db.commit(); db.refresh(row)
    return _address_response(row)


@router.put("/me/addresses/{address_id}", response_model=AddressResponse)
def update_address(address_id: str, payload: AddressInput, db: Db, user: CurrentUser) -> AddressResponse:
    row = _owned_address(db, address_id, user)
    if payload.is_default:
        _clear_default_addresses(db, user, row.id)
    for field, value in payload.model_dump().items():
        setattr(row, field, value)
    _activity(db, user, "address.updated", f"Updated {row.label}", address_id=row.id)
    db.commit(); db.refresh(row)
    return _address_response(row)


@router.post("/me/addresses/{address_id}/activate", response_model=AddressResponse)
def activate_address(address_id: str, db: Db, user: CurrentUser) -> AddressResponse:
    row = _owned_address(db, address_id, user)
    _clear_default_addresses(db, user, row.id)
    row.is_default = True
    _activity(db, user, "address.activated", f"Using {row.label}", address_id=row.id)
    db.commit(); db.refresh(row)
    return _address_response(row)


@router.delete("/me/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: str, db: Db, user: CurrentUser) -> None:
    row = _owned_address(db, address_id, user)
    was_default = row.is_default
    _activity(db, user, "address.deleted", f"Removed {row.label}", address_id=row.id)
    db.delete(row); db.flush()
    if was_default:
        replacement = db.scalar(select(SavedAddress).where(SavedAddress.user_id == user.id).order_by(SavedAddress.updated_at.desc()))
        if replacement:
            replacement.is_default = True
    db.commit()


@router.get("/me/serviceability", response_model=ServiceabilityResponse)
def address_serviceability(address_id: str, db: Db, user: CurrentUser, category: str | None = Query(default=None, max_length=100)) -> ServiceabilityResponse:
    row = _owned_address(db, address_id, user)
    return ServiceabilityResponse(address_id=row.id, category=category, can_request_comparison=True, message="This location has valid coordinates. Provider availability is verified only when you start a comparison.")


@router.get("/me/payment-preferences", response_model=list[PaymentPreferenceResponse])
def list_payment_preferences(db: Db, user: CurrentUser) -> list[PaymentPreferenceResponse]:
    rows = db.scalars(select(PaymentPreference).where(PaymentPreference.user_id == user.id).order_by(PaymentPreference.is_preferred.desc(), PaymentPreference.updated_at.desc())).all()
    return [_payment_response(row) for row in rows]


@router.post("/me/payment-preferences", response_model=PaymentPreferenceResponse, status_code=status.HTTP_201_CREATED)
def create_payment_preference(payload: PaymentPreferenceInput, db: Db, user: CurrentUser) -> PaymentPreferenceResponse:
    count = len(db.scalars(select(PaymentPreference.id).where(PaymentPreference.user_id == user.id)).all())
    values = payload.model_dump(exclude={"benefit_tags"})
    values["is_preferred"] = payload.is_preferred or count == 0
    if values["is_preferred"]:
        _clear_preferred_payments(db, user)
    if payload.method_type == "card":
        values["masked_identifier"] = f"•••• {payload.last4}"
    row = PaymentPreference(user_id=user.id, metadata_={"benefit_tags": payload.benefit_tags}, **values)
    db.add(row)
    _activity(db, user, "payment_preference.created", f"Added {row.label}", payment_preference_id=row.id, method_type=row.method_type)
    db.commit(); db.refresh(row)
    return _payment_response(row)


@router.put("/me/payment-preferences/{payment_id}", response_model=PaymentPreferenceResponse)
def update_payment_preference(payment_id: str, payload: PaymentPreferenceInput, db: Db, user: CurrentUser) -> PaymentPreferenceResponse:
    row = _owned_payment(db, payment_id, user)
    if payload.is_preferred:
        _clear_preferred_payments(db, user, row.id)
    values = payload.model_dump(exclude={"benefit_tags"})
    if payload.method_type == "card":
        values["masked_identifier"] = f"•••• {payload.last4}"
    for field, value in values.items():
        setattr(row, field, value)
    row.metadata_ = {"benefit_tags": payload.benefit_tags}
    _activity(db, user, "payment_preference.updated", f"Updated {row.label}", payment_preference_id=row.id)
    db.commit(); db.refresh(row)
    return _payment_response(row)


@router.post("/me/payment-preferences/{payment_id}/prefer", response_model=PaymentPreferenceResponse)
def prefer_payment(payment_id: str, db: Db, user: CurrentUser) -> PaymentPreferenceResponse:
    row = _owned_payment(db, payment_id, user)
    _clear_preferred_payments(db, user, row.id)
    row.is_preferred = True
    _activity(db, user, "payment_preference.preferred", f"Preferred {row.label}", payment_preference_id=row.id)
    db.commit(); db.refresh(row)
    return _payment_response(row)


@router.delete("/me/payment-preferences/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_preference(payment_id: str, db: Db, user: CurrentUser) -> None:
    row = _owned_payment(db, payment_id, user)
    was_preferred = row.is_preferred
    _activity(db, user, "payment_preference.deleted", f"Removed {row.label}", payment_preference_id=row.id)
    db.delete(row); db.flush()
    if was_preferred:
        replacement = db.scalar(select(PaymentPreference).where(PaymentPreference.user_id == user.id).order_by(PaymentPreference.updated_at.desc()))
        if replacement:
            replacement.is_preferred = True
    db.commit()


@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile(user_id: str, owned_user: Annotated[User, Depends(require_user_ownership)]) -> ProfileResponse:
    return _response(owned_user)


@router.put("/{user_id}", response_model=ProfileResponse)
def update_profile(user_id: str, payload: ProfileUpdate, db: Db, owned_user: Annotated[User, Depends(require_user_ownership)]) -> ProfileResponse:
    return _update_profile(payload, db, owned_user)
