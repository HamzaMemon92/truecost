from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from app.config import Settings
from app.services.sms import (
    FailoverSmsProvider,
    Msg91SmsProvider,
    SmsDeliveryError,
    SmsProvider,
    TwoFactorSmsProvider,
    build_sms_provider,
)


def response(status_code: int, payload: dict[str, str]) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("POST", "https://provider.invalid/otp"),
    )








class StubProvider(SmsProvider):
    def __init__(
        self,
        provider_name: str,
        action: Callable[[], None] | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.action = action
        self.calls = 0

    def send_otp(self, phone_number: str, code: str, expires_minutes: int) -> None:
        self.calls += 1
        if self.action:
            self.action()


def raises_delivery_error(provider: str, *, retry_safe: bool) -> Callable[[], None]:
    def raise_error() -> None:
        raise SmsDeliveryError(provider, retry_safe=retry_safe)

    return raise_error


def test_failover_runs_only_after_confirmed_primary_rejection() -> None:
    primary = StubProvider("msg91", raises_delivery_error("msg91", retry_safe=True))
    fallback = StubProvider("twofactor")

    FailoverSmsProvider(primary, fallback).send_otp("+919876543210", "482901", 5)

    assert primary.calls == 1
    assert fallback.calls == 1


def test_failover_does_not_risk_duplicate_after_ambiguous_failure() -> None:
    primary = StubProvider("msg91", raises_delivery_error("msg91", retry_safe=False))
    fallback = StubProvider("twofactor")

    with pytest.raises(SmsDeliveryError):
        FailoverSmsProvider(primary, fallback).send_otp("+919876543210", "482901", 5)

    assert primary.calls == 1
    assert fallback.calls == 0

