from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice

# Productivity SaaS connectors use the TrueCostProduct schema in a plan-comparison mode:
# - name = plan name (Free, Pro, Business, Enterprise)
# - weightVolume = billing cycle context ("per user/month")
# - prices[0].price = monthly per-seat cost
# - prices[0].deliveryTime = key features summary

NOTION_PLANS = [
    {"id": "free", "name": "Free", "price": 0, "features": "Unlimited pages, basic blocks"},
    {"id": "plus", "name": "Plus", "price": 10, "features": "Unlimited blocks, unlimited file uploads"},
    {"id": "business", "name": "Business", "price": 18, "features": "SAML SSO, private team spaces, bulk PDF export"},
    {"id": "enterprise", "name": "Enterprise", "price": 0, "features": "Custom pricing, advanced security, audit log"},
]

class NotionConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "Notion"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            # Try to parse live plan data if scraper sends it
            plans_raw = raw_payload.get("plans", raw_payload.get("tiers", []))
            plans = plans_raw if plans_raw else NOTION_PLANS

            for plan in plans:
                price = float(plan.get("price", plan.get("monthlyPrice", plan.get("amount", 0))) or 0)
                name = plan.get("name", plan.get("tier", plan.get("planName", "Plan")))
                features = plan.get("features", plan.get("description", ""))
                if isinstance(features, list):
                    features = " · ".join(str(f) for f in features[:3])

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=price,
                    original_price=None,
                    delivery_time=str(features)[:100],
                    deep_link="https://www.notion.so/pricing"
                )
                products.append(TrueCostProduct(
                    id=f"tc_notion_{name.lower().replace(' ', '_')}",
                    name=f"Notion {name}",
                    brand="Notion",
                    weight_volume="per user/month",
                    image_url="",
                    category="Productivity",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[NotionConnector] Error: {e}")
        return products


FIGMA_PLANS = [
    {"id": "starter", "name": "Starter", "price": 0, "features": "3 Figma files, unlimited personal files"},
    {"id": "professional", "name": "Professional", "price": 15, "features": "Unlimited files, shared libraries, version history"},
    {"id": "organization", "name": "Organization", "price": 45, "features": "Org-wide libraries, centralized admin, SSO"},
    {"id": "enterprise", "name": "Enterprise", "price": 75, "features": "Advanced admin, dedicated workspace, 24/7 support"},
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
                    delivery_time=str(features)[:100],
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


SLACK_PLANS = [
    {"id": "free", "name": "Free", "price": 0, "features": "90 days message history, 10 integrations"},
    {"id": "pro", "name": "Pro", "price": 8.75, "features": "Unlimited message history, unlimited integrations, group calls"},
    {"id": "business+", "name": "Business+", "price": 15, "features": "SAML-based SSO, 99.99% uptime SLA, data exports"},
    {"id": "enterprise", "name": "Enterprise Grid", "price": 0, "features": "Custom pricing, enterprise security, centralized admin"},
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
                    delivery_time=str(features)[:100],
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


CANVA_PLANS = [
    {"id": "free", "name": "Free", "price": 0, "features": "250,000+ templates, 5GB storage, basic AI tools"},
    {"id": "pro", "name": "Pro", "price": 499, "features": "1M+ templates, 1TB storage, background remover, brand kit"},
    {"id": "teams", "name": "Teams", "price": 700, "features": "All Pro + team tools, brand controls, admin roles"},
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
                    weight_volume="per user/month (₹/yr)",
                    image_url="",
                    category="Productivity",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[CanvaConnector] Error: {e}")
        return products
