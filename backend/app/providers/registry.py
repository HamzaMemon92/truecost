from __future__ import annotations

from app.providers.flipkart_provider import FlipkartProvider
from app.providers.mock_provider import MockProvider


def get_providers() -> list[object]:
    return [FlipkartProvider(), MockProvider()]
