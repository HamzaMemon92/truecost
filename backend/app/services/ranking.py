from __future__ import annotations

from app.schemas.shopping import CanonicalProduct


def select_recommendation(products: list[CanonicalProduct]) -> CanonicalProduct | None:
    if not products:
        return None
    return sorted(products, key=lambda p: (p.price, -p.confidence))[0]
