from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import OtpChallenge, PhoneIdentity, PushDevice, RefreshToken, User, UserProfile
from app.security import create_token, decode_token, hash_password, token_fingerprint, verify_password
from app.services.sms import SmsProvider, build_sms_provider

router = APIRouter()
bearer = HTTPBearer(auto_error=False)
Db = Annotated[Session, Depends(get_db)]
sms_provider: SmsProvider = build_sms_provider()
PHONE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")
EXPO_TOKEN_PATTERN = re.compile(r"^(Expo(nent)?PushToken)\[[A-Za-z0-9_-]+\]$")


class Credentials(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=8, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("A valid email address is required")
        return value


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    token_type: str = "bearer"


class ReauthenticationResponse(BaseModel):
    reauthentication_token: str
    expires_in_seconds: int = 600


class PasswordReauthenticationInput(BaseModel):
    password: str = Field(min_length=8, max_length=256)


class UserResponse(BaseModel):
    id: str
    email: str | None
    phone_number: str | None = None


class OtpRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        value = re.sub(r"[\s()-]", "", value)
        if not PHONE_PATTERN.fullmatch(value):
            raise ValueError("Use an international phone number such as +919876543210")
        return value


class OtpRequestResponse(BaseModel):
    challenge_id: str
    expires_in_seconds: int
    resend_after_seconds: int
    delivery_channel: str


class OtpVerifyRequest(BaseModel):
    challenge_id: str = Field(min_length=36, max_length=36)
    code: str = Field(pattern=r"^\d{6}$")


class PushTokenInput(BaseModel):
    expo_push_token: str = Field(min_length=20, max_length=220)
    platform: str = Field(pattern=r"^(ios|android)$")
    device_name: str | None = Field(default=None, max_length=120)

    @field_validator("expo_push_token")
    @classmethod
    def validate_expo_token(cls, value: str) -> str:
        if not EXPO_TOKEN_PATTERN.fullmatch(value):
            raise ValueError("A valid Expo push token is required")
        return value


class PushTokenResponse(BaseModel):
    id: str
    platform: str
    active: bool
    last_seen_at: datetime


class SessionResponse(BaseModel):
    id: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


def _issue_tokens(user: User, db: Session) -> TokenResponse:
    access, _ = create_token(user.id, "access", timedelta(minutes=settings.access_token_minutes))
    refresh, token_id = create_token(user.id, "refresh", timedelta(days=settings.refresh_token_days))
    db.add(RefreshToken(id=token_id, user_id=user.id, token_hash=token_fingerprint(refresh), expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)))
    db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh, user_id=user.id)


def _as_utc(value: datetime) -> datetime:
    """Normalise SQLite's timezone-naive timestamps before comparison."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _otp_hash(challenge_id: str, code: str) -> str:
    return hmac.new(settings.auth_secret_key.encode(), f"otp:{challenge_id}:{code}".encode(), hashlib.sha256).hexdigest()


def _request_ip_hash(request: Request) -> str | None:
    if request.client is None:
        return None
    return hmac.new(settings.auth_secret_key.encode(), request.client.host.encode(), hashlib.sha256).hexdigest()


def current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)], db: Db) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(credentials.credentials, "access")
    user = db.get(User, payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user


def require_user_ownership(user_id: str, user: Annotated[User, Depends(current_user)]) -> User:
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Resource belongs to another user")
    return user


def require_admin(user: Annotated[User, Depends(current_user)]) -> User:
    configured = {email.strip().lower() for email in settings.admin_emails.split(",") if email.strip()}
    if not user.is_admin and user.email.lower() not in configured:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access is required")
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: Credentials, db: Db) -> TokenResponse:
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    user.profile = UserProfile()
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    return _issue_tokens(user, db)


@router.post("/login", response_model=TokenResponse)
def login(payload: Credentials, db: Db) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return _issue_tokens(user, db)


@router.post("/request-otp", response_model=OtpRequestResponse, status_code=status.HTTP_202_ACCEPTED)
def request_otp(payload: OtpRequest, request: Request, db: Db) -> OtpRequestResponse:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=10)
    phone_count = len(db.scalars(select(OtpChallenge.id).where(OtpChallenge.phone_number == payload.phone_number, OtpChallenge.created_at >= window_start)).all())
    ip_hash = _request_ip_hash(request)
    ip_count = len(db.scalars(select(OtpChallenge.id).where(OtpChallenge.request_ip_hash == ip_hash, OtpChallenge.created_at >= window_start)).all()) if ip_hash else 0
    if max(phone_count, ip_count) >= settings.otp_max_requests_per_10_minutes:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many verification requests. Try again later.", headers={"Retry-After": "600"})

    challenge_id = str(uuid4())
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = OtpChallenge(
        id=challenge_id,
        phone_number=payload.phone_number,
        code_hash=_otp_hash(challenge_id, code),
        request_ip_hash=ip_hash,
        max_attempts=settings.otp_max_attempts,
        expires_at=now + timedelta(minutes=settings.otp_ttl_minutes),
    )
    db.add(challenge)
    db.commit()
    try:
        sms_provider.send_otp(payload.phone_number, code, settings.otp_ttl_minutes)
    except Exception:
        challenge.consumed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Verification message could not be delivered")
    return OtpRequestResponse(
        challenge_id=challenge.id,
        expires_in_seconds=settings.otp_ttl_minutes * 60,
        resend_after_seconds=settings.otp_resend_seconds,
        delivery_channel="development_console" if settings.sms_provider == "console" else "sms",
    )


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: OtpVerifyRequest, db: Db) -> TokenResponse:
    challenge = db.get(OtpChallenge, payload.challenge_id)
    now = datetime.now(timezone.utc)
    invalid = challenge is None or challenge.consumed_at is not None or _as_utc(challenge.expires_at) <= now
    if invalid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verification code is invalid or expired")
    if challenge.attempts >= challenge.max_attempts:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many verification attempts")
    if not hmac.compare_digest(challenge.code_hash, _otp_hash(challenge.id, payload.code)):
        challenge.attempts += 1
        db.commit()
        remaining = max(challenge.max_attempts - challenge.attempts, 0)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Incorrect verification code. {remaining} attempts remaining.")

    challenge.consumed_at = now
    identity = db.scalar(select(PhoneIdentity).where(PhoneIdentity.phone_number == challenge.phone_number))
    if identity is None:
        phone_digest = hashlib.sha256(challenge.phone_number.encode()).hexdigest()[:32]
        user = User(email=f"phone-{phone_digest}@phone.truecost.invalid", password_hash=hash_password(secrets.token_urlsafe(32)))
        user.profile = UserProfile(preferences={"auth_method": "phone"})
        db.add(user)
        db.flush()
        identity = PhoneIdentity(user_id=user.id, phone_number=challenge.phone_number)
        db.add(identity)
        db.flush()
    else:
        user = identity.user
        identity.verified_at = now
    return _issue_tokens(user, db)


@router.post("/reauth/password", response_model=ReauthenticationResponse)
def reauthenticate_password(payload: PasswordReauthenticationInput, user: Annotated[User, Depends(current_user)]) -> ReauthenticationResponse:
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password is incorrect")
    token, _ = create_token(user.id, "reauth", timedelta(minutes=10))
    return ReauthenticationResponse(reauthentication_token=token)


@router.post("/reauth/verify-otp", response_model=ReauthenticationResponse)
def reauthenticate_phone(payload: OtpVerifyRequest, db: Db, user: Annotated[User, Depends(current_user)]) -> ReauthenticationResponse:
    challenge = db.get(OtpChallenge, payload.challenge_id)
    now = datetime.now(timezone.utc)
    phone_numbers = {identity.phone_number for identity in user.phone_identities}
    if challenge is None or challenge.phone_number not in phone_numbers or challenge.consumed_at is not None or _as_utc(challenge.expires_at) <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verification code is invalid or expired")
    if challenge.attempts >= challenge.max_attempts:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many verification attempts")
    if not hmac.compare_digest(challenge.code_hash, _otp_hash(challenge.id, payload.code)):
        challenge.attempts += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect verification code")
    challenge.consumed_at = now
    db.commit()
    token, _ = create_token(user.id, "reauth", timedelta(minutes=10))
    return ReauthenticationResponse(reauthentication_token=token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Db) -> TokenResponse:
    claims = decode_token(payload.refresh_token, "refresh")
    stored = db.get(RefreshToken, claims["jti"])
    if stored is None or stored.revoked_at is not None or stored.token_hash != token_fingerprint(payload.refresh_token) or _as_utc(stored.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid or revoked")
    user = db.get(User, claims["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    stored.revoked_at = datetime.now(timezone.utc)
    return _issue_tokens(user, db)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Db) -> None:
    claims = decode_token(payload.refresh_token, "refresh")
    stored = db.get(RefreshToken, claims["jti"])
    if stored is not None and stored.token_hash == token_fingerprint(payload.refresh_token):
        stored.revoked_at = datetime.now(timezone.utc)
        db.commit()


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(current_user)]) -> UserResponse:
    phone = user.phone_identities[0].phone_number if user.phone_identities else None
    public_email = None if user.email.endswith("@phone.truecost.invalid") else user.email
    return UserResponse(id=user.id, email=public_email, phone_number=phone)


@router.post("/push-tokens", response_model=PushTokenResponse)
def register_push_token(payload: PushTokenInput, db: Db, user: Annotated[User, Depends(current_user)]) -> PushTokenResponse:
    now = datetime.now(timezone.utc)
    device = db.scalar(select(PushDevice).where(PushDevice.expo_push_token == payload.expo_push_token))
    if device is None:
        device = PushDevice(user_id=user.id, **payload.model_dump(), last_seen_at=now)
        db.add(device)
    else:
        device.user_id = user.id
        device.platform = payload.platform
        device.device_name = payload.device_name
        device.active = True
        device.last_seen_at = now
    db.commit()
    db.refresh(device)
    return PushTokenResponse(id=device.id, platform=device.platform, active=device.active, last_seen_at=device.last_seen_at)


@router.delete("/push-tokens/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_push_token(device_id: str, db: Db, user: Annotated[User, Depends(current_user)]) -> None:
    device = db.scalar(select(PushDevice).where(PushDevice.id == device_id, PushDevice.user_id == user.id))
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Push device not found")
    device.active = False
    db.commit()


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(db: Db, user: Annotated[User, Depends(current_user)]) -> list[SessionResponse]:
    rows = db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id).order_by(RefreshToken.created_at.desc())).all()
    return [SessionResponse(id=row.id, created_at=row.created_at, expires_at=row.expires_at, revoked_at=row.revoked_at) for row in rows]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(session_id: str, db: Db, user: Annotated[User, Depends(current_user)]) -> None:
    row = db.scalar(select(RefreshToken).where(RefreshToken.id == session_id, RefreshToken.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)
        db.commit()


@router.post("/sessions/revoke-all", status_code=status.HTTP_204_NO_CONTENT)
def revoke_all_sessions(db: Db, user: Annotated[User, Depends(current_user)]) -> None:
    now = datetime.now(timezone.utc)
    for row in db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))).all():
        row.revoked_at = now
    db.commit()
