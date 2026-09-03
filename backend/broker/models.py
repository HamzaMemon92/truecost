from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, LargeBinary, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from broker.config import settings


class BrokerBase(DeclarativeBase):
    pass


class VaultCredential(BrokerBase):
    __tablename__ = "broker_vault_credentials"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    subject_ref: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    provider_id: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    access_token_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    refresh_token_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    key_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)
    scopes: Mapped[str] = mapped_column(String(1000), default="", nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


engine = create_engine(settings.database_url, pool_pre_ping=True)
BrokerSession = sessionmaker(bind=engine, expire_on_commit=False)
