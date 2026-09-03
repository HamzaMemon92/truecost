from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice

FIGMA_PLANS = [
    {"id": "starter", "name": "Starter", "price": 0, "features": "3 Figma files, unlimited personal files, basic components"},
    {"id": "professional", "name": "Professional", "price": 15, "features": "Unlimited files, shared libraries, version history, advanced prototyping"},
    {"id": "organization", "name": "Organization", "price": 45, "features": "Org-wide libraries, centralized admin, SSO, private plugins"},
    {"id": "enterprise", "name": "Enterprise", "price": 75, "features": "Advanced admin, dedicated workspace, 24/7 enterprise support"},
]

class FigmaConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Figma"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            plans_raw = raw_payload.get("plans", raw_payload.get("tiers", []))
            plans = plans_raw if plans_raw else FIGMA_PLANS

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
                    deep_link="https://www.figma.com/pricing/"
                )
                products.append(TrueCostProduct(
                    id=f"tc_figma_{name.lower().replace(' ', '_')}",
                    name=f"Figma {name}",
                    brand="Figma",
                    weight_volume="per editor/month",
                    image_url="",
                    category="Productivity",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[FigmaConnector] Error: {e}")
        return products
