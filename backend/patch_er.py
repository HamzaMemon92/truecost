import re

with open('app/services/entity_resolution.py', 'r') as f:
    content = f.read()

new_contracts = '''
FOOD_CONTRACT = IdentityContract(
    resolver_version="food.delivery.v1",
    entity_type=EntityType.PRODUCT,
    critical=("restaurant_name", "dish_name"),
    variant=("cuisine", "price", "eta"),
)

PHARMACY_CONTRACT = IdentityContract(
    resolver_version="pharmacy.medicine.v1",
    entity_type=EntityType.PRODUCT,
    critical=("medicine_name", "dosage"),
    variant=("brand", "pack_size", "price"),
)

MOBILITY_CONTRACT = IdentityContract(
    resolver_version="mobility.ride.v1",
    entity_type=EntityType.PRODUCT,
    critical=("ride_class",),
    variant=("price", "eta", "capacity"),
)

TRAVEL_CONTRACT = IdentityContract(
    resolver_version="travel.flight.v1",
    entity_type=EntityType.PRODUCT,
    critical=("origin", "destination", "date"),
    variant=("airline", "price", "duration", "stops"),
)

FINANCE_CONTRACT = IdentityContract(
    resolver_version="finance.product.v1",
    entity_type=EntityType.PRODUCT,
    critical=("product_type",),
    variant=("interest_rate", "tenure", "benefits"),
)

PRODUCTIVITY_CONTRACT = IdentityContract(
    resolver_version="productivity.saas.v1",
    entity_type=EntityType.PRODUCT,
    critical=("tool_name",),
    variant=("tier", "price", "features"),
)
'''

content = re.sub(
    r'GENERIC_CONTRACT\s*=\s*IdentityContract\(.*?\)\n', 
    new_contracts, 
    content, 
    flags=re.DOTALL
)

content = content.replace(
    'GENERIC_CONTRACT.resolver_version: GENERIC_CONTRACT,',
    '''FOOD_CONTRACT.resolver_version: FOOD_CONTRACT,
    PHARMACY_CONTRACT.resolver_version: PHARMACY_CONTRACT,
    MOBILITY_CONTRACT.resolver_version: MOBILITY_CONTRACT,
    TRAVEL_CONTRACT.resolver_version: TRAVEL_CONTRACT,
    FINANCE_CONTRACT.resolver_version: FINANCE_CONTRACT,
    PRODUCTIVITY_CONTRACT.resolver_version: PRODUCTIVITY_CONTRACT,'''
)

contract_method = '''
    def _contract(self, category: str) -> IdentityContract | None:
        key = str(category or "").casefold().strip()
        if key == "grocery": return GROCERY_CONTRACT
        if key == "shopping": return SHOPPING_CONTRACT
        if key in ("food", "food delivery"): return FOOD_CONTRACT
        if key == "pharmacy": return PHARMACY_CONTRACT
        if key in ("mobility", "rides"): return MOBILITY_CONTRACT
        if key in ("travel", "flights"): return TRAVEL_CONTRACT
        if key in ("finance", "financial products"): return FINANCE_CONTRACT
        if key in ("productivity", "saas", "services"): return PRODUCTIVITY_CONTRACT
        return None
'''

content = re.sub(
    r'    def _contract\(self, category: str\) -> IdentityContract \| None:.*?(?=    def _extract_attributes)',
    contract_method.lstrip('\n') + '\n',
    content,
    flags=re.DOTALL
)

with open('app/services/entity_resolution.py', 'w') as f:
    f.write(content)
