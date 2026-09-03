from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

import httpx


@dataclass(frozen=True)
class OAuthTokens:
    access_token: str
    refresh_token: str | None
    expires_in: int | None
    scopes: list[str]


class ProviderOAuthAdapter(Protocol):
    provider_id: str
    def authorization_url(self, *, state: str, challenge: str, redirect_uri: str) -> str: ...
    async def exchange(self, *, code: str, verifier: str, redirect_uri: str) -> OAuthTokens: ...
    async def revoke(self, token: str) -> None: ...


class ConfiguredOAuthAdapter:
    """Standards-based adapter enabled only after provider approval and config."""
    def __init__(self, provider_id: str) -> None:
        prefix = f"{provider_id.upper()}_OAUTH_"
        self.provider_id = provider_id
        self.client_id = os.getenv(prefix + "CLIENT_ID", "")
        self.client_secret = os.getenv(prefix + "CLIENT_SECRET", "")
        self.authorize_endpoint = os.getenv(prefix + "AUTHORIZE_URL", "")
        self.token_endpoint = os.getenv(prefix + "TOKEN_URL", "")
        self.revoke_endpoint = os.getenv(prefix + "REVOKE_URL", "")
        self.scopes = [scope for scope in os.getenv(prefix + "SCOPES", "").split() if scope]

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.authorize_endpoint and self.token_endpoint)

    def authorization_url(self, *, state: str, challenge: str, redirect_uri: str) -> str:
        if not self.configured:
            raise RuntimeError("Provider OAuth adapter is pending approval")
        return self.authorize_endpoint + "?" + urlencode({"response_type": "code", "client_id": self.client_id, "redirect_uri": redirect_uri, "scope": " ".join(self.scopes), "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})

    async def exchange(self, *, code: str, verifier: str, redirect_uri: str) -> OAuthTokens:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(self.token_endpoint, data={"grant_type": "authorization_code", "client_id": self.client_id, "client_secret": self.client_secret, "code": code, "code_verifier": verifier, "redirect_uri": redirect_uri})
            response.raise_for_status()
            payload = response.json()
        return OAuthTokens(payload["access_token"], payload.get("refresh_token"), payload.get("expires_in"), str(payload.get("scope", "")).split())

    async def revoke(self, token: str) -> None:
        if not self.revoke_endpoint:
            return
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(self.revoke_endpoint, data={"token": token, "client_id": self.client_id, "client_secret": self.client_secret})
            response.raise_for_status()
