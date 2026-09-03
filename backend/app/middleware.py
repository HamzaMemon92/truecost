from __future__ import annotations

import secrets
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class RequestSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or secrets.token_hex(12)
        request.state.request_id = request_id
        if "*" not in settings.trusted_host_list and request.url.hostname not in settings.trusted_host_list:
            return JSONResponse(status_code=400, content={"error": {"code": "invalid_host", "message": "Host is not allowed", "request_id": request_id}}, headers={"X-Request-ID": request_id})
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        if settings.app_env.lower() not in {"development", "test"}:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis fixed-window limiter with a process-local test/development fallback."""

    RULES = {
        ("POST", "/api/v1/auth/request-otp"): (5, 600),
        ("POST", "/api/v1/auth/verify-otp"): (10, 600),
        ("POST", "/api/v1/auth/login"): (10, 300),
        ("POST", "/api/v1/auth/refresh"): (30, 60),
        ("POST", "/api/v1/aggregator/ingest"): (120, 60),
        ("POST", "/api/v1/aggregator/optimize"): (30, 60),
        ("POST", "/api/v1/support/reports"): (10, 3600),
    }

    def __init__(self, app):
        super().__init__(app)
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._redis = None

    async def _allowed(self, key: str, limit: int, window: int) -> bool:
        if settings.app_env.lower() not in {"development", "test"}:
            if self._redis is None:
                from redis.asyncio import from_url
                self._redis = from_url(settings.redis_url, decode_responses=True)
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, window)
            return count <= limit
        now = time.monotonic()
        bucket = self._windows[key]
        while bucket and bucket[0] <= now - window:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True

    async def dispatch(self, request: Request, call_next):
        rule = self.RULES.get((request.method, request.url.path))
        if rule is None and request.method == "POST" and request.url.path.startswith("/api/v1/provider-connections/") and request.url.path.endswith("/start"):
            rule = (10, 600)
        if rule:
            client = request.client.host if request.client else "unknown"
            key = f"rate:{request.method}:{request.url.path}:{client}"
            try:
                allowed = await self._allowed(key, *rule)
            except Exception:
                request_id = getattr(request.state, "request_id", "unknown")
                return JSONResponse(status_code=503, content={"error": {"code": "rate_limit_unavailable", "message": "Service temporarily unavailable", "request_id": request_id}})
            if not allowed:
                request_id = getattr(request.state, "request_id", "unknown")
                return JSONResponse(
                    status_code=429,
                    content={"error": {"code": "rate_limited", "message": "Too many requests", "request_id": request_id}},
                    headers={"Retry-After": str(rule[1])},
                )
        return await call_next(request)
