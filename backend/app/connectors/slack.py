from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice

SLACK_PLANS = [
    {"id": "free", "name": "Free", "price": 0, "features": "90 days message history, 10 integrations, 1:1 video calls"},
    {"id": "pro", "name": "Pro", "price": 8.75, "features": "Unlimited message history, unlimited integrations, group calls"},
    {"id": "business_plus", "name": "Business+", "price": 15, "features": "SAML SSO, 99.99% uptime SLA, data exports, compliance"},
    {"id": "enterprise", "name": "Enterprise Grid", "price": 0, "features": "Custom pricing, centralized admin, advanced security"},
]

class SlackConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Slack"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            plans_raw = raw_payload.get("plans", raw_payload.get("tiers", []))
            plans = plans_raw if plans_raw else SLACK_PLANS

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
                    deep_link="https://slack.com/intl/en-in/pricing"
                )
                products.append(TrueCostProduct(
                    id=f"tc_slack_{name.lower().replace(' ', '_').replace('+', 'plus')}",
                    name=f"Slack {name}",
                    brand="Slack",
                    weight_volume="per user/month",
                    image_url="",
                    category="Productivity",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[SlackConnector] Error: {e}")
        return products
