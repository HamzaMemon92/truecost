from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from app.config import settings


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, settings.password_pbkdf2_iterations)
    return "pbkdf2_sha256${}${}${}".format(settings.password_pbkdf2_iterations, base64.urlsafe_b64encode(salt).decode(), base64.urlsafe_b64encode(digest).decode())


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.urlsafe_b64decode(salt), int(iterations))
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(expected))
    except (ValueError, TypeError):
        return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_token(subject: str, token_type: str, expires_in: timedelta, token_id: str | None = None) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    jti = token_id or str(uuid4())
    payload = {"sub": subject, "typ": token_type, "jti": jti, "iat": int(now.timestamp()), "exp": int((now + expires_in).timestamp())}
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{_b64(json.dumps(header, separators=(',', ':')).encode())}.{_b64(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = _b64(hmac.new(settings.auth_secret_key.encode(), signing_input.encode(), hashlib.sha256).digest())
    return f"{signing_input}.{signature}", jti


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        encoded_header, encoded_payload, signature = token.split(".")
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected = _b64(hmac.new(settings.auth_secret_key.encode(), signing_input.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("signature")
        payload = json.loads(_unb64(encoded_payload))
        if payload.get("typ") != expected_type or not payload.get("sub") or not payload.get("jti"):
            raise ValueError("claims")
        if int(payload["exp"]) <= int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("expired")
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})


def token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
