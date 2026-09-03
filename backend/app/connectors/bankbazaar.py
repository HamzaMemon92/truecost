from typing import List, Dict, Any
from app.connectors.base import BaseProviderConnector
from app.schemas.product import TrueCostProduct, ProviderPrice

# Finance connectors use TrueCostProduct in rate-comparison mode:
# - name = product name (Home Loan, Car Loan, Term Plan, etc.)
# - weightVolume = key spec (e.g. "10 yr tenure", "₹50L cover")
# - price = interest rate (% p.a.) or premium (₹/yr)
# - deliveryTime = key highlight ("Processing fee: 0.5%")

def _find_products(obj, keys, depth=0):
    if depth > 8:
        return []
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        if any(k in obj[0] for k in keys):
            return obj
    if isinstance(obj, dict):
        for key in ["products", "loans", "cards", "policies", "results", "data", "items"]:
            if key in obj and isinstance(obj[key], list) and obj[key]:
                found = _find_products(obj[key], keys, depth + 1)
                if found:
                    return found
        for v in obj.values():
            if isinstance(v, (dict, list)):
                found = _find_products(v, keys, depth + 1)
                if found:
                    return found
    if isinstance(obj, list):
        for item in obj:
            found = _find_products(item, keys, depth + 1)
            if found:
                return found
    return []


class BankBazaarConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "BankBazaar"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            keys = ["interestRate", "roi", "rate", "annualFee", "joiningFee", "loanName", "cardName", "productName", "name", "bankName"]
            items = _find_products(raw_payload, keys)
            for item in items[:10]:
                rate = item.get("interestRate", item.get("roi", item.get("rate", item.get("annualFee", item.get("joiningFee", 0)))))
                try:
                    rate = float(rate or 0)
                except (TypeError, ValueError):
                    rate = 0.0
                name = item.get("cardName", item.get("loanName", item.get("productName", item.get("name", "Finance Product"))))
                bank = item.get("bankName", item.get("issuer", item.get("bank", "Bank")))
                tenure = item.get("maxTenure", item.get("tenure", ""))
                fee = item.get("processingFee", "")
                if not fee and ("annualFee" in item or "joiningFee" in item):
                    fee = f"Annual fee: {item.get('annualFee', item.get('joiningFee', 0))}"

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=rate,
                    original_price=None,
                    delivery_time=f"Fee: {fee}" if fee else f"Tenure: {tenure}",
                    deep_link=item.get("applyUrl", "https://www.bankbazaar.com/")
                )
                products.append(TrueCostProduct(
                    id=f"tc_bb_{hash(name + bank) % 999999}",
                    name=name,
                    brand=bank,
                    weight_volume=f"{tenure} tenure" if tenure else "% p.a.",
                    image_url="",
                    category="Finance",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[BankBazaarConnector] Error: {e}")
        return products


class PolicyBazaarConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "PolicyBazaar"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            keys = ["premium", "annualPremium", "policyName", "insurerName", "coverAmount", "name"]
            items = _find_products(raw_payload, keys)
            for item in items[:10]:
                premium = item.get("premium", item.get("annualPremium", item.get("price", 0)))
                try:
                    premium = float(premium or 0)
                except (TypeError, ValueError):
                    premium = 0.0
                name = item.get("policyName", item.get("planName", item.get("name", "Policy")))
                insurer = item.get("insurerName", item.get("company", item.get("brand", "Insurer")))
                cover = item.get("coverAmount", item.get("sumAssured", ""))
                tenure = item.get("policyTerm", item.get("tenure", ""))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=premium,
                    original_price=None,
                    delivery_time=f"Cover: ₹{cover}" if cover else "",
                    deep_link=item.get("buyUrl", "https://www.policybazaar.com/")
                )
                products.append(TrueCostProduct(
                    id=f"tc_pb_{hash(name + insurer) % 999999}",
                    name=name,
                    brand=insurer,
                    weight_volume=f"{tenure} yr term" if tenure else "Annual premium",
                    image_url="",
                    category="Finance",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[PolicyBazaarConnector] Error: {e}")
        return products


class PaisaBazaarConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "PaisaBazaar"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            keys = ["interestRate", "roi", "rate", "productName", "lenderName", "name", "bankName"]
            items = _find_products(raw_payload, keys)
            for item in items[:10]:
                rate = item.get("interestRate", item.get("roi", item.get("rate", 0)))
                try:
                    rate = float(rate or 0)
                except (TypeError, ValueError):
                    rate = 0.0
                name = item.get("productName", item.get("loanName", item.get("name", "Product")))
                lender = item.get("lenderName", item.get("bankName", item.get("bank", "Lender")))
                tenure = item.get("tenure", item.get("maxTenure", ""))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=rate,
                    original_price=None,
                    delivery_time=f"Tenure: {tenure}" if tenure else "% p.a.",
                    deep_link=item.get("applyUrl", "https://www.paisabazaar.com/")
                )
                products.append(TrueCostProduct(
                    id=f"tc_pab_{hash(name + lender) % 999999}",
                    name=name,
                    brand=lender,
                    weight_volume="% p.a.",
                    image_url="",
                    category="Finance",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[PaisaBazaarConnector] Error: {e}")
        return products


class CreditMantriConnector(BaseProviderConnector):
    @property
    def provider_name(self) -> str:
        return "CreditMantri"

    def parse_search_results(self, raw_payload: Dict[str, Any]) -> List[TrueCostProduct]:
        products = []
        try:
            keys = ["interestRate", "roi", "apr", "productName", "bankName", "name"]
            items = _find_products(raw_payload, keys)
            for item in items[:10]:
                rate = item.get("interestRate", item.get("roi", item.get("apr", 0)))
                try:
                    rate = float(rate or 0)
                except (TypeError, ValueError):
                    rate = 0.0
                name = item.get("productName", item.get("cardName", item.get("name", "Product")))
                bank = item.get("bankName", item.get("issuer", item.get("bank", "Bank")))

                provider_price = ProviderPrice(
                    provider=self.provider_name,
                    price=rate,
                    original_price=None,
                    delivery_time=item.get("eligibility", item.get("highlight", "")),
                    deep_link=item.get("applyUrl", "https://www.creditmantri.com/")
                )
                products.append(TrueCostProduct(
                    id=f"tc_cm_{hash(name + bank) % 999999}",
                    name=name,
                    brand=bank,
                    weight_volume="% p.a.",
                    image_url="",
                    category="Finance",
                    prices=[provider_price]
                ))
        except Exception as e:
            print(f"[CreditMantriConnector] Error: {e}")
        return products
