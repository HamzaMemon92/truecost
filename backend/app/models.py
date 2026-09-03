from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferences_json: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    saved_items: Mapped[list["SavedItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    price_watches: Mapped[list["PriceWatch"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    carts: Mapped[list["Cart"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    activities: Mapped[list["UserActivity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    search_sessions: Mapped[list["SearchSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    saved_collections: Mapped[list["SavedCollection"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    saved_addresses: Mapped[list["SavedAddress"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payment_preferences: Mapped[list["PaymentPreference"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    support_reports: Mapped[list["SupportReport"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    phone_identities: Mapped[list["PhoneIdentity"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    push_devices: Mapped[list["PushDevice"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    provider_connections: Mapped[list["ProviderConnection"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    decision_audits: Mapped[list["DecisionAuditTrail"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="profile")


class SavedAddress(Base):
    __tablename__ = "saved_addresses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    address_line: Mapped[str] = mapped_column(String(300), nullable=False)
    locality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(24), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), default="IN", nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="saved_addresses")


class PaymentPreference(Base):
    __tablename__ = "payment_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    method_type: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    network: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    masked_identifier: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="payment_preferences")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class PhoneIdentity(Base):
    __tablename__ = "phone_identities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="phone_identities")


class OtpChallenge(Base):
    __tablename__ = "otp_challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    phone_number: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    request_ip_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)


class PushDevice(Base):
    __tablename__ = "push_devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    expo_push_token: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    device_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="push_devices")


class ProviderConnection(Base):
    __tablename__ = "provider_connections"
    __table_args__ = (UniqueConstraint("user_id", "provider_id", name="uq_user_provider_connection"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    provider_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="connected", nullable=False)
    account_label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    broker_subject_ref: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="provider_connections")


class ProviderConnectionAttempt(Base):
    __tablename__ = "provider_connection_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    provider_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    state_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ProviderOperationalState(Base):
    __tablename__ = "provider_operational_states"

    provider_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    rollout_state: Mapped[str] = mapped_column(String(24), default="catalogued", nullable=False)
    connection_state: Mapped[str] = mapped_column(String(24), default="pending_approval", nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(240), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class ProviderVerificationEvent(Base):
    __tablename__ = "provider_verification_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    verification_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    checks: Mapped[dict] = mapped_column(JSON, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    recorded_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class SavedItem(Base):
    __tablename__ = "saved_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(12), default="INR", nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="saved_items")
    collection_links: Mapped[list["SavedCollectionItem"]] = relationship(back_populates="saved_item", cascade="all, delete-orphan")


class SavedCollection(Base):
    __tablename__ = "saved_collections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="saved_collections")
    item_links: Mapped[list["SavedCollectionItem"]] = relationship(back_populates="collection", cascade="all, delete-orphan", order_by="SavedCollectionItem.created_at")


class SavedCollectionItem(Base):
    __tablename__ = "saved_collection_items"
    __table_args__ = (UniqueConstraint("collection_id", "saved_item_id", name="uq_saved_collection_item"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    collection_id: Mapped[str] = mapped_column(ForeignKey("saved_collections.id", ondelete="CASCADE"), index=True, nullable=False)
    saved_item_id: Mapped[str] = mapped_column(ForeignKey("saved_items.id", ondelete="CASCADE"), index=True, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    collection: Mapped[SavedCollection] = relationship(back_populates="item_links")
    saved_item: Mapped[SavedItem] = relationship(back_populates="collection_links")


class PriceWatch(Base):
    __tablename__ = "price_watches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(12), default="INR", nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="price_watches")
    observations: Mapped[list["PriceObservation"]] = relationship(back_populates="watch", cascade="all, delete-orphan", order_by="PriceObservation.observed_at")
    triggers: Mapped[list["PriceWatchTrigger"]] = relationship(back_populates="watch", cascade="all, delete-orphan")


class PriceObservation(Base):
    __tablename__ = "price_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    watch_id: Mapped[str] = mapped_column(ForeignKey("price_watches.id", ondelete="CASCADE"), index=True, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    source_session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    watch: Mapped[PriceWatch] = relationship(back_populates="observations")


class PriceWatchTrigger(Base):
    __tablename__ = "price_watch_triggers"
    __table_args__ = (UniqueConstraint("watch_id", "observation_key", name="uq_price_watch_observation_trigger"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    watch_id: Mapped[str] = mapped_column(ForeignKey("price_watches.id", ondelete="CASCADE"), index=True, nullable=False)
    observation_key: Mapped[str] = mapped_column(String(160), nullable=False)
    observed_price: Mapped[float] = mapped_column(Float, nullable=False)
    notification_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    watch: Mapped[PriceWatch] = relationship(back_populates="triggers")


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), default="My cart", nullable=False)
    currency: Mapped[str] = mapped_column(String(12), default="INR", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="carts")
    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan", order_by="CartItem.created_at")
    optimizations: Mapped[list["CartOptimization"]] = relationship(back_populates="cart", cascade="all, delete-orphan", order_by="CartOptimization.created_at")


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    cart_id: Mapped[str] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    cart: Mapped[Cart] = relationship(back_populates="items")


class CartOptimization(Base):
    __tablename__ = "cart_optimizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    cart_id: Mapped[str] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    objective: Mapped[str] = mapped_column(String(30), default="balanced", nullable=False)
    result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    cart: Mapped[Cart] = relationship(back_populates="optimizations")

    __table_args__ = (UniqueConstraint("cart_id", "version", name="uq_cart_optimization_version"),)


class UserActivity(Base):
    __tablename__ = "user_activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="activities")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(40), default="updates", nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    deep_link: Mapped[str | None] = mapped_column(String(400), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    user: Mapped[User] = relationship(back_populates="notifications")


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"
    __table_args__ = (UniqueConstraint("notification_id", name="uq_notification_outbox_notification"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    notification_id: Mapped[str] = mapped_column(ForeignKey("notifications.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ticket_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    delivery_targets: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    last_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class ProviderAccountBenefit(Base):
    __tablename__ = "provider_account_benefits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    provider_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    benefit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False)
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BrokerRevocationOutbox(Base):
    __tablename__ = "broker_revocation_outbox"
    __table_args__ = (UniqueConstraint("connection_id", name="uq_broker_revocation_connection"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    connection_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    provider_id: Mapped[str] = mapped_column(String(80), nullable=False)
    subject_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class SupportReport(Base):
    __tablename__ = "support_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    subject: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    user: Mapped[User | None] = relationship(back_populates="support_reports")


class SearchSession(Base):
    __tablename__ = "search_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    user: Mapped[User | None] = relationship(back_populates="search_sessions")
    observations: Mapped[list["IngestedProviderResult"]] = relationship(back_populates="search_session", cascade="all, delete-orphan")
    decision_audits: Mapped[list["DecisionAuditTrail"]] = relationship(back_populates="search_session", cascade="all, delete-orphan")
    entity_resolution_records: Mapped[list["EntityResolutionRecord"]] = relationship(back_populates="search_session", cascade="all, delete-orphan")


class IngestedProviderResult(Base):
    __tablename__ = "ingested_provider_results"
    __table_args__ = (UniqueConstraint("search_session_id", "provider", "product_id", "ingestion_key", name="uq_ingested_result_request_product"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    search_session_id: Mapped[str] = mapped_column(ForeignKey("search_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    product_id: Mapped[str] = mapped_column(String(300), nullable=False)
    product: Mapped[dict] = mapped_column(JSON, nullable=False)
    ingestion_key: Mapped[str] = mapped_column(String(64), default=lambda: str(uuid4()), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    search_session: Mapped[SearchSession] = relationship(back_populates="observations")


class DecisionAuditTrail(Base):
    __tablename__ = "decision_audit_trail"
    __table_args__ = (UniqueConstraint("search_session_id", "artifact_type", "artifact_hash", name="uq_decision_audit_artifact"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    search_session_id: Mapped[str] = mapped_column(ForeignKey("search_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    artifact_type: Mapped[str] = mapped_column(String(60), default="exact_discovery", nullable=False)
    artifact_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    selected_identity: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    provider_attempts: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    exact_results: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    related_results: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    rejected_results: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    final_decision: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    freshness: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    search_session: Mapped[SearchSession] = relationship(back_populates="decision_audits")
    user: Mapped[User | None] = relationship(back_populates="decision_audits")


class EntityResolutionRecord(Base):
    __tablename__ = "entity_resolution_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    search_session_id: Mapped[str | None] = mapped_column(ForeignKey("search_sessions.id", ondelete="CASCADE"), index=True, nullable=True)
    selected_entity: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    candidate_entity: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    provider_offer: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    legacy_decision: Mapped[str] = mapped_column(String(20), nullable=False)
    v3_decision: Mapped[str] = mapped_column(String(20), nullable=False)
    disagreement: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evidence: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    conflicts: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    missing_factors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    unknown_attributes: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    resolver_version: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence_inputs: Mapped[float] = mapped_column(Float, nullable=False)
    extraction_provenance: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Human-reviewed labels for shadow evaluation
    review_label: Mapped[str | None] = mapped_column(String(40), nullable=True) # V3_CORRECT, LEGACY_CORRECT, BOTH_CORRECT, BOTH_WRONG, AMBIGUOUS, INSUFFICIENT_EVIDENCE
    review_error_classification: Mapped[str | None] = mapped_column(String(40), nullable=True) # FALSE_MERGE, FALSE_REJECT, etc.
    review_notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    search_session: Mapped[SearchSession | None] = relationship(back_populates="entity_resolution_records")

