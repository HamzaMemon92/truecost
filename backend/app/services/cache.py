from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Protocol

from app.config import settings


class PriceCache(Protocol):
    def get(self, query: str, provider: str, category: str, *, location: dict[str, Any] | None = None) -> list[Any] | None: ...
    def set(self, query: str, provider: str, category: str, data: list[Any], ttl: int | None = None, *, location: dict[str, Any] | None = None) -> None: ...
    def get_all_providers(self, query: str, category: str, providers: list[str], *, location: dict[str, Any] | None = None) -> dict[str, list[Any] | None]: ...
    def stats(self) -> dict: ...


def _location_digest(location: dict[str, Any] | None) -> str:
    if not location:
        return "no_location"
    pincode = location.get("pincode") or location.get("postal_code") or location.get("postalCode")
    if pincode:
        return f"pin:{str(pincode).strip().casefold()}"
    lat = location.get("latitude")
    lng = location.get("longitude")
    if lat is not None and lng is not None:
        try:
            return f"geo:{round(float(lat), 4)}:{round(float(lng), 4)}"
        except (TypeError, ValueError):
            pass
    digest = hashlib.sha256(json.dumps(location, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:12]
    return f"loc:{digest}"


def _key(query: str, provider: str, category: str, *, location: dict[str, Any] | None = None) -> str:
    # Query text is not retained in Redis keys or operational diagnostics.
    digest = hashlib.sha256(query.casefold().strip().encode()).hexdigest()[:24]
    return f"price:{category.casefold()}:{provider.casefold()}:{_location_digest(location)}:{digest}"


class MemoryPriceCache:
    def __init__(self, default_ttl_seconds: int = 900) -> None:
        self._store: dict[str, dict] = {}
        self.default_ttl = default_ttl_seconds

    def get(self, query: str, provider: str, category: str, *, location: dict[str, Any] | None = None) -> list[Any] | None:
        key = _key(query, provider, category, location=location)
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["data"]

    def set(self, query: str, provider: str, category: str, data: list[Any], ttl: int | None = None, *, location: dict[str, Any] | None = None) -> None:
        self._store[_key(query, provider, category, location=location)] = {"data": data, "expires_at": time.time() + (ttl or self.default_ttl)}

    def get_all_providers(self, query: str, category: str, providers: list[str], *, location: dict[str, Any] | None = None) -> dict[str, list[Any] | None]:
        return {provider: self.get(query, provider, category, location=location) for provider in providers}

    def stats(self) -> dict:
        now = time.time()
        return {"backend": "memory", "total_keys": len(self._store), "live_keys": sum(entry["expires_at"] > now for entry in self._store.values())}


class RedisPriceCache:
    def __init__(self, url: str, default_ttl_seconds: int = 900) -> None:
        from redis import Redis
        self._redis = Redis.from_url(url, decode_responses=True)
        self.default_ttl = default_ttl_seconds

    def get(self, query: str, provider: str, category: str, *, location: dict[str, Any] | None = None) -> list[Any] | None:
        raw = self._redis.get(_key(query, provider, category, location=location))
        return json.loads(raw) if raw else None

    def set(self, query: str, provider: str, category: str, data: list[Any], ttl: int | None = None, *, location: dict[str, Any] | None = None) -> None:
        self._redis.set(_key(query, provider, category, location=location), json.dumps(data, separators=(",", ":")), ex=ttl or self.default_ttl)

    def get_all_providers(self, query: str, category: str, providers: list[str], *, location: dict[str, Any] | None = None) -> dict[str, list[Any] | None]:
        keys = [_key(query, provider, category, location=location) for provider in providers]
        values = self._redis.mget(keys)
        return {provider: json.loads(raw) if raw else None for provider, raw in zip(providers, values)}

    def stats(self) -> dict:
        info = self._redis.info(section="keyspace")
        return {"backend": "redis", "keyspace": info}


cache: PriceCache = MemoryPriceCache() if settings.app_env.lower() in {"development", "test"} else RedisPriceCache(settings.redis_url)
