import re

with open("backend/app/api/endpoints/aggregator.py", "r", encoding="utf-8") as f:
    content = f.read()

imports = """
from app.connectors.namma_yatri import NammaYatriConnector
from app.connectors.meesho import MeeshoConnector
from app.connectors.myntra import MyntraConnector
from app.connectors.magicpin import MagicPinConnector
from app.connectors.eatsure import EatSureConnector
from app.connectors.apollo247 import Apollo247Connector
from app.connectors.netmeds import NetmedsConnector
from app.connectors.ixigo import IxigoConnector
from app.connectors.cleartrip import CleartripConnector
from app.connectors.policybazaar import PolicyBazaarConnector
from app.connectors.paisabazaar import PaisaBazaarConnector
from app.connectors.creditmantri import CreditMantriConnector
from app.connectors.slack import SlackConnector
from app.connectors.canva import CanvaConnector
"""

# add imports after app.connectors.figma import FigmaConnector
content = content.replace("from app.connectors.figma import FigmaConnector", "from app.connectors.figma import FigmaConnector" + imports)

known_providers = """KNOWN_PROVIDERS = [
    "zepto", "blinkit", "swiggy", "bigbasket",
    "uber", "ola", "rapido", "namma_yatri",
    "amazon", "flipkart", "meesho", "myntra",
    "swiggy_food", "zomato", "magicpin", "eatsure",
    "tata1mg", "pharmeasy", "apollo247", "netmeds",
    "makemytrip", "goibibo", "ixigo", "cleartrip",
    "bankbazaar", "policybazaar", "paisabazaar", "creditmantri",
    "notion", "figma", "slack", "canva",
]"""

content = re.sub(r'KNOWN_PROVIDERS = \[.*?\]', known_providers, content, flags=re.DOTALL)

alias_map = """PROVIDER_ALIAS_MAP: dict = {
    # Grocery
    "zepto": "zepto",
    "blinkit": "blinkit",
    "swiggy": "swiggy",
    "swiggy instamart": "swiggy",
    "bigbasket": "bigbasket",
    "big basket": "bigbasket",
    # Mobility
    "uber": "uber",
    "ola": "ola",
    "rapido": "rapido",
    "namma yatri": "namma_yatri",
    "nammayatri": "namma_yatri",
    # Shopping
    "amazon": "amazon",
    "flipkart": "flipkart",
    "meesho": "meesho",
    "myntra": "myntra",
    # Food
    "swiggy food": "swiggy_food",
    "swiggy_food": "swiggy_food",
    "zomato": "zomato",
    "magicpin": "magicpin",
    "eatsure": "eatsure",
    # Pharmacy
    "tata 1mg": "tata1mg",
    "tata1mg": "tata1mg",
    "1mg": "tata1mg",
    "pharmeasy": "pharmeasy",
    "pharm easy": "pharmeasy",
    "apollo 247": "apollo247",
    "apollo247": "apollo247",
    "netmeds": "netmeds",
    # Travel
    "makemytrip": "makemytrip",
    "make my trip": "makemytrip",
    "goibibo": "goibibo",
    "ixigo": "ixigo",
    "cleartrip": "cleartrip",
    # Finance
    "bankbazaar": "bankbazaar",
    "bank bazaar": "bankbazaar",
    "policybazaar": "policybazaar",
    "paisabazaar": "paisabazaar",
    "creditmantri": "creditmantri",
    # Productivity
    "notion": "notion",
    "figma": "figma",
    "slack": "slack",
    "canva": "canva",
}"""

content = re.sub(r'PROVIDER_ALIAS_MAP: dict = \{.*?\}', alias_map, content, flags=re.DOTALL)

connectors_str = """connectors = {
    "zepto": ZeptoConnector(),
    "blinkit": BlinkitConnector(),
    "swiggy": SwiggyInstamartConnector(),
    "bigbasket": BigBasketConnector(),
    "uber": UberConnector(),
    "ola": OlaConnector(),
    "rapido": RapidoConnector(),
    "namma_yatri": NammaYatriConnector(),
    "amazon": AmazonConnector() if "AmazonConnector" in dir() else None,
    "flipkart": FlipkartConnector(),
    "meesho": MeeshoConnector(),
    "myntra": MyntraConnector(),
    "swiggy_food": SwiggyFoodConnector(),
    "zomato": ZomatoConnector(),
    "magicpin": MagicPinConnector(),
    "eatsure": EatSureConnector(),
    "tata1mg": Tata1mgConnector(),
    "pharmeasy": PharmEasyConnector(),
    "apollo247": Apollo247Connector(),
    "netmeds": NetmedsConnector(),
    "makemytrip": MakeMyTripConnector(),
    "goibibo": GoibiboConnector(),
    "ixigo": IxigoConnector(),
    "cleartrip": CleartripConnector(),
    "bankbazaar": BankBazaarConnector(),
    "policybazaar": PolicyBazaarConnector(),
    "paisabazaar": PaisaBazaarConnector(),
    "creditmantri": CreditMantriConnector(),
    "notion": NotionConnector(),
    "figma": FigmaConnector(),
    "slack": SlackConnector(),
    "canva": CanvaConnector(),
}"""

content = re.sub(r'connectors = \{\n.*?\}\n# Remove any', connectors_str + '\n# Remove any', content, flags=re.DOTALL)

with open("backend/app/api/endpoints/aggregator.py", "w", encoding="utf-8") as f:
    f.write(content)
