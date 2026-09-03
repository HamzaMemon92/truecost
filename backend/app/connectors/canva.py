from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice

CANVA_PLANS = [
    {"id": "free", "name": "Free", "price": 0, "features": "250,000+ templates, 5GB storage, basic AI tools, brand kit (1)"},
    {"id": "pro", "name": "Pro", "price": 499, "features": "1M+ templates, 1TB storage, background remover, brand kit, resize tool"},
    {"id": "teams", "name": "Teams", "price": 700, "features": "All Pro + team tools, brand controls, admin roles, 1TB/person"},
]

class CanvaConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Canva"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            plans_raw = raw_payload.get("plans", raw_payload.get("tiers", []))
            plans = plans_raw if plans_raw else CANVA_PLANS

            for plan in plans:
                price = float(plan.get("price", plan.get("monthlyPrice", plan.get("amount", 0))) or 0)
                name = plan.get("name", plan.get("tier", "Plan"))
                features = plan.get("features", plan.get("description", ""))
                if isinstance(features, list):
                    features = " · ".join(str(f) for f in features[:3])

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=None,
                    delivery_time=str(features)[:120],
                    deep_link="https://www.canva.com/pricing/"
                )
                products.append(TrueCostProduct(
                    id=f"tc_canva_{name.lower().replace(' ', '_')}",
                    name=f"Canva {name}",
                    brand="Canva",
                    weight_volume="per user/month (INR/yr)",
                    image_url="",
                    category="Productivity",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[CanvaConnector] Error: {e}")
        return products
