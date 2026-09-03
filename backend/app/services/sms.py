from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.config import Settings, settings

logger = logging.getLogger("truecost.sms")


def mask_phone(phone_number: str) -> str:
    return f"{phone_number[:3]}***{phone_number[-3:]}"


class SmsDeliveryError(RuntimeError):
    """A redacted delivery failure safe to surface inside the backend only."""

    def __init__(self, provider_name: str, *, retry_safe: bool) -> None:
        super().__init__(f"{provider_name} could not confirm OTP delivery")
        self.provider_name = provider_name
        self.retry_safe = retry_safe


class SmsProvider(ABC):
    provider_name = "unknown"

    @abstractmethod
    def send_otp(self, phone_number: str, code: str, expires_minutes: int) -> None:
        """Deliver a one-time code. Implementations must never persist plaintext codes."""


class ConsoleSmsProvider(SmsProvider):
    provider_name = "console"

    def send_otp(self, phone_number: str, code: str, expires_minutes: int) -> None:
        logger.warning(
            "Development OTP for %s: %s (expires in %s minutes)",
            mask_phone(phone_number),
            code,
            expires_minutes,
        )


class HttpSmsProvider(SmsProvider):
    timeout_seconds: float

    def _post(self, url: str, **kwargs: Any) -> httpx.Response:
        try:
            return httpx.post(url, timeout=self.timeout_seconds, **kwargs)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout) as exc:
            # The request did not reach a point where delivery could have been accepted.
            raise SmsDeliveryError(self.provider_name, retry_safe=True) from exc
        except httpx.RequestError as exc:
            # Read/write failures are ambiguous: a second provider could deliver a duplicate OTP.
            raise SmsDeliveryError(self.provider_name, retry_safe=False) from exc

    def _require_success_status(self, response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # A concrete non-2xx response confirms that this provider rejected the send.
            raise SmsDeliveryError(self.provider_name, retry_safe=True) from exc

    def _response_json(self, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            # A 2xx response with an unknown body may already have delivered the message.
            raise SmsDeliveryError(self.provider_name, retry_safe=False) from exc
        if not isinstance(payload, dict):
            raise SmsDeliveryError(self.provider_name, retry_safe=False)
        return payload


class Msg91SmsProvider(HttpSmsProvider):
    provider_name = "msg91"

    def __init__(self, config: Settings) -> None:
        self.auth_key = config.msg91_auth_key or ""
        self.template_id = config.msg91_template_id or ""
        self.timeout_seconds = config.sms_request_timeout_seconds

    def send_otp(self, phone_number: str, code: str, expires_minutes: int) -> None:
        response = self._post(
            "https://control.msg91.com/api/v5/otp",
            headers={"Content-Type": "application/json"},
            params={
                "authkey": self.auth_key,
                "template_id": self.template_id,
                "mobile": phone_number.removeprefix("+"),
                "otp": code,
                "otp_expiry": expires_minutes,
                "otp_length": len(code),
            },
            json={},
        )
        self._require_success_status(response)
        payload = self._response_json(response)
        if str(payload.get("type", "")).lower() != "success":
            raise SmsDeliveryError(self.provider_name, retry_safe=True)


class TwoFactorSmsProvider(HttpSmsProvider):
    provider_name = "twofactor"

    def __init__(self, config: Settings) -> None:
        self.api_key = config.twofactor_api_key or ""
        self.template_name = config.twofactor_template_name or ""
        self.timeout_seconds = config.sms_request_timeout_seconds

    def send_otp(self, phone_number: str, code: str, expires_minutes: int) -> None:
        del expires_minutes  # Expiry remains authoritative in TrueCost's hashed challenge.
        response = self._post(
            "https://2factor.in/API/V1/OTP/SEND",
            headers={"Content-Type": "application/json", "X-API-Key": self.api_key},
            json={
                "to": phone_number,
                "template_name": self.template_name,
                "var1": code,
            },
        )
        self._require_success_status(response)
        payload = self._response_json(response)
        delivery_status = str(payload.get("status", payload.get("Status", ""))).lower()
        if delivery_status not in {"sent", "success"}:
            raise SmsDeliveryError(self.provider_name, retry_safe=True)


class TwilioSmsProvider(HttpSmsProvider):
    provider_name = "twilio"

    def __init__(self, config: Settings) -> None:
        self.account_sid = config.twilio_account_sid or ""
        self.auth_token = config.twilio_auth_token or ""
        self.from_number = config.twilio_from_number or ""
        self.timeout_seconds = config.sms_request_timeout_seconds

    def send_otp(self, phone_number: str, code: str, expires_minutes: int) -> None:
        response = self._post(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
            auth=(self.account_sid, self.auth_token),
            data={
                "To": phone_number,
                "From": self.from_number,
                "Body": f"Your TrueCost verification code is {code}. It expires in {expires_minutes} minutes.",
            },
        )
        self._require_success_status(response)


class FailoverSmsProvider(SmsProvider):
    provider_name = "failover"

    def __init__(self, primary: SmsProvider, fallback: SmsProvider) -> None:
        self.primary = primary
        self.fallback = fallback

    def send_otp(self, phone_number: str, code: str, expires_minutes: int) -> None:
        try:
            self.primary.send_otp(phone_number, code, expires_minutes)
        except SmsDeliveryError as exc:
            if not exc.retry_safe:
                raise
            logger.warning(
                "OTP provider %s rejected delivery; attempting configured fallback %s",
                self.primary.provider_name,
                self.fallback.provider_name,
            )
            self.fallback.send_otp(phone_number, code, expires_minutes)


def _provider_from_name(provider_name: str, config: Settings) -> SmsProvider:
    if provider_name == "console":
        return ConsoleSmsProvider()
    if provider_name == "msg91":
        return Msg91SmsProvider(config)
    if provider_name == "twofactor":
        return TwoFactorSmsProvider(config)
    if provider_name == "twilio":
        return TwilioSmsProvider(config)
    raise ValueError(f"Unsupported SMS provider: {provider_name}")


def build_sms_provider(config: Settings = settings) -> SmsProvider:
    primary = _provider_from_name(config.sms_provider, config)
    if config.sms_fallback_provider == "none":
        return primary
    return FailoverSmsProvider(primary, _provider_from_name(config.sms_fallback_provider, config))
