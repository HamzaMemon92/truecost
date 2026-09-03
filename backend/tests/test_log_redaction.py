import json
import logging

from app.observability.runtime import RedactingJsonFormatter


def render(message: str) -> str:
    record = logging.LogRecord("httpx", logging.INFO, __file__, 1, message, (), None)
    return json.loads(RedactingJsonFormatter().format(record))["message"]


def test_sms_delivery_query_secrets_are_redacted() -> None:
    output = render(
        "HTTP Request: POST https://control.msg91.com/api/v5/otp?"
        "authkey=top-secret&mobile=919876543210&otp=482901"
    )

    assert "top-secret" not in output
    assert "919876543210" not in output
    assert "482901" not in output
    assert output.count("[REDACTED]") == 3


def test_twilio_account_identifier_and_personal_data_are_redacted() -> None:
    output = render(
        "POST https://api.twilio.com/2010-04-01/Accounts/AC123private/Messages.json "
        "for +919876543210 and person@example.com"
    )

    assert "AC123private" not in output
    assert "+919876543210" not in output
    assert "person@example.com" not in output
