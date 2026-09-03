from __future__ import annotations

from app.schemas.shopping import CanonicalProduct


def compute_payment_benefits(query: str, recommendation: CanonicalProduct | None) -> list[str]:
    if recommendation is None:
        return []
    normalized = query.lower()
    if "card" not in normalized and "emi" not in normalized:
        return []
    return [
        f"Estimated card cashback for {recommendation.brand}: 2% (verification pending provider confirmation)",
        "No-cost EMI availability should be confirmed on final checkout page.",
    ]
