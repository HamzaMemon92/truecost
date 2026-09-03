from __future__ import annotations

from app.schemas.shopping import CanonicalProduct


def build_verification_notes(query: str, recommendation: CanonicalProduct | None, providers_count: int) -> list[str]:
    notes = [f"Query verified: {query}", f"Providers scanned: {providers_count}"]
    if recommendation:
        notes.append(f"Recommendation confidence: {recommendation.confidence:.2f}")
        notes.append(f"Source type: {recommendation.source_type}")
    else:
        notes.append("No recommendation available")
    return notes
