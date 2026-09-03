from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.schemas.shopping import CanonicalProduct


class MockProvider:
    name = "Mock"
    status = "mock"

    async def search(self, query: str) -> list[CanonicalProduct]:
        normalized = query.lower()
        if "laptop" in normalized or "macbook" in normalized:
            title = "MacBook Air M3"
            brand = "Apple"
            category = "Laptop"
            price = 98999
        elif "iphone" in normalized:
            title = "Apple iPhone 17"
            brand = "Apple"
            category = "Mobile"
            price = 79999
        else:
            title = "Sony WH-1000XM5"
            brand = "Sony"
            category = "Audio"
            price = 24490

        now = datetime.now(timezone.utc)
        return [
            CanonicalProduct(
                canonical_product_id=f"mock-{title.lower().replace(' ', '-')}",
                provider=self.name,
                provider_product_id=f"mock-{abs(hash(query)) % 100000}",
                title=title,
                brand=brand,
                category=category,
                variant="standard",
                price=price,
                availability="In stock",
                seller="Mock Seller",
                rating=4.7,
                review_count=1800,
                delivery="2 days",
                offers=["Mock cashback", "No-cost EMI"],
                return_policy="7-day return",
                warranty="1 year",
                source_url="https://mock.example/product",
                affiliate_url="https://mock.example/affiliate",
                source_type="mock",
                retrieved_at=now,
                expires_at=now + timedelta(minutes=30),
                confidence=0.91,
            )
        ]
