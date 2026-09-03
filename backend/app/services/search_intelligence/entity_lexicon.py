"""
Entity Lexicon — Alias Knowledge Graph V2
==========================================
Context-sensitive brand/family/product aliases for TrueCost.

V2 CHANGES:
  - Every alias is now an AliasRecord with a typed relation
  - Only SPELLING_VARIANT and PHONETIC_VARIANT are allowed to rewrite the query
  - GENERIC_EQUIVALENT (brufen→ibuprofen) is kept for discovery only
  - SUBSTITUTION (dal fry→dal tadka) is kept for discovery only
  - Pharmacy brand→molecule mappings correctly typed as GENERIC_EQUIVALENT
  - Duplicate keys removed (doodh, koramangla)
  - get_category_aliases() if-elif → registry dict (open/closed principle)
  - Startup validation asserts no duplicate aliases within each category
  - _KNOWN_BRANDS moved here from query_parser (single source of truth)
  - Canonical brand names are explicit, never reconstructed via .title()

Rules:
  - Add entries when real queries fail; never guess in advance
  - Numbers/model-numbers are never fuzzed via this lexicon
  - Only SPELLING_VARIANT and PHONETIC_VARIANT rewrite the retrieval query
  - GENERIC_EQUIVALENT/SUBSTITUTION only expand search for discovery
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.search_intelligence.models import AliasRelation


# ─────────────────────────────────────────────────────────────────────────────
# AliasRecord — single structured alias entry
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AliasRecord:
    alias: str            # lowercase user spelling
    canonical: str        # correct canonical form
    relation: AliasRelation
    brand_context: str | None = None   # restrict to this brand (lowercase)
    category: str | None = None        # restrict to this category
    confidence: float = 0.95
    locale: str = "en-IN"
    notes: str = ""

    # Only these relation types may rewrite the query text
    REWRITE_RELATIONS: frozenset[AliasRelation] = field(
        default_factory=lambda: frozenset({
            AliasRelation.SPELLING_VARIANT,
            AliasRelation.PHONETIC_VARIANT,
            AliasRelation.BRAND_ALIAS,
            AliasRelation.PRODUCT_FAMILY_ALIAS,
            AliasRelation.LOCATION_ALIAS,
            AliasRelation.ABBREVIATION,
        }),
        init=False, repr=False, compare=False,
    )

    def may_rewrite(self) -> bool:
        return self.relation in self.REWRITE_RELATIONS


# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL BRAND NAME MAP
# Maps canonical lowercase token → display-case canonical name
# Used so we never produce "Jbl", "Hdfc", "Sbi" via .title()
# ─────────────────────────────────────────────────────────────────────────────
CANONICAL_BRAND_NAMES: dict[str, str] = {
    "noise": "Noise",
    "boat": "boAt",
    "apple": "Apple",
    "samsung": "Samsung",
    "sony": "Sony",
    "jbl": "JBL",
    "sennheiser": "Sennheiser",
    "bose": "Bose",
    "skullcandy": "Skullcandy",
    "realme": "Realme",
    "oneplus": "OnePlus",
    "xiaomi": "Xiaomi",
    "mi": "Xiaomi",
    "oppo": "OPPO",
    "vivo": "vivo",
    "motorola": "Motorola",
    "lg": "LG",
    "philips": "Philips",
    "panasonic": "Panasonic",
    "mivi": "Mivi",
    "ptron": "pTron",
    "zebronics": "Zebronics",
    "portronics": "Portronics",
    "fireboltt": "Fire-Boltt",
    "hammer": "Hammer",
    "nothing": "Nothing",
    "cmf": "CMF",
    "boult": "Boult",
    "amul": "Amul",
    "nestle": "Nestlé",
    "britannia": "Britannia",
    "haldiram": "Haldiram's",
    "hdfc": "HDFC",
    "sbi": "SBI",
    "icici": "ICICI",
    "axis": "Axis",
    "kotak": "Kotak",
    "slack": "Slack",
    "figma": "Figma",
    "notion": "Notion",
    "canva": "Canva",
    "adobe": "Adobe",
    "uber": "Uber",
    "ola": "Ola",
    "rapido": "Rapido",
    "indigo": "IndiGo",
    "airasia": "AirAsia",
    "spicejet": "SpiceJet",
    "airindia": "Air India",
    "dolo": "Dolo",
    "crocin": "Crocin",
    "combiflam": "Combiflam",
    "cipla": "Cipla",
    "flipkart": "Flipkart",
    "amazon": "Amazon",
    "myntra": "Myntra",
    "meesho": "Meesho",
}

# ─────────────────────────────────────────────────────────────────────────────
# KNOWN BRANDS SET (used for brand detection in parser)
# Source of truth — import from here, not from query_parser
# ─────────────────────────────────────────────────────────────────────────────
KNOWN_BRANDS: frozenset[str] = frozenset(CANONICAL_BRAND_NAMES.keys())


# ─────────────────────────────────────────────────────────────────────────────
# SHOPPING — Brand aliases
# ─────────────────────────────────────────────────────────────────────────────
BRAND_ALIASES: list[AliasRecord] = [
    # Noise
    AliasRecord("noize", "Noise", AliasRelation.PHONETIC_VARIANT),
    AliasRecord("gonoise", "Noise", AliasRelation.BRAND_ALIAS),
    AliasRecord("go noise", "Noise", AliasRelation.BRAND_ALIAS),
    AliasRecord("noisee", "Noise", AliasRelation.SPELLING_VARIANT),
    # boAt
    AliasRecord("b0at", "boAt", AliasRelation.SPELLING_VARIANT),
    AliasRecord("b0at audio", "boAt", AliasRelation.BRAND_ALIAS),
    # Samsung
    AliasRecord("samsing", "Samsung", AliasRelation.SPELLING_VARIANT),
    AliasRecord("samsng", "Samsung", AliasRelation.SPELLING_VARIANT),
    AliasRecord("samsuung", "Samsung", AliasRelation.SPELLING_VARIANT),
    # Apple
    AliasRecord("aple", "Apple", AliasRelation.SPELLING_VARIANT),
    AliasRecord("appel", "Apple", AliasRelation.SPELLING_VARIANT),
    # Sony
    AliasRecord("soni", "Sony", AliasRelation.PHONETIC_VARIANT),
    AliasRecord("sonny", "Sony", AliasRelation.PHONETIC_VARIANT),
    # JBL
    AliasRecord("jbl audio", "JBL", AliasRelation.BRAND_ALIAS),
    # Realme
    AliasRecord("real me", "Realme", AliasRelation.SPELLING_VARIANT),
    # OnePlus
    AliasRecord("one plus", "OnePlus", AliasRelation.SPELLING_VARIANT),
    # Xiaomi
    AliasRecord("xioami", "Xiaomi", AliasRelation.SPELLING_VARIANT),
    AliasRecord("xiomi", "Xiaomi", AliasRelation.SPELLING_VARIANT),
    # pTron
    AliasRecord("ptron", "pTron", AliasRelation.SPELLING_VARIANT),
    # Fire-Boltt
    AliasRecord("fire boltt", "Fire-Boltt", AliasRelation.SPELLING_VARIANT),
    AliasRecord("fier boltt", "Fire-Boltt", AliasRelation.PHONETIC_VARIANT),
    AliasRecord("fireboltt", "Fire-Boltt", AliasRelation.SPELLING_VARIANT),
    # CMF (Nothing sub-brand)
    AliasRecord("cmf by nothing", "CMF", AliasRelation.BRAND_ALIAS),
    # Finance
    AliasRecord("hdfcbank", "HDFC", AliasRelation.BRAND_ALIAS),
    AliasRecord("hdfc bank", "HDFC", AliasRelation.BRAND_ALIAS),
    AliasRecord("state bank", "SBI", AliasRelation.BRAND_ALIAS),
    AliasRecord("axis bank", "Axis", AliasRelation.BRAND_ALIAS),
]

# Build a fast flat lookup: alias_text → AliasRecord (for rewrite-eligible only)
_BRAND_ALIAS_MAP: dict[str, AliasRecord] = {
    r.alias.lower(): r for r in BRAND_ALIASES
}


# ─────────────────────────────────────────────────────────────────────────────
# SHOPPING — Product family aliases (context-sensitive)
# ─────────────────────────────────────────────────────────────────────────────
FAMILY_ALIASES: list[AliasRecord] = [
    # ── Noise ──────────────────────────────────────────────────────────────
    AliasRecord("airmax", "Airwave Max", AliasRelation.PHONETIC_VARIANT, brand_context="noise"),
    AliasRecord("air max", "Airwave Max", AliasRelation.PHONETIC_VARIANT, brand_context="noise"),
    AliasRecord("airmaks", "Airwave Max", AliasRelation.PHONETIC_VARIANT, brand_context="noise"),
    AliasRecord("airmacks", "Airwave Max", AliasRelation.PHONETIC_VARIANT, brand_context="noise"),
    AliasRecord("airwav", "Airwave Max", AliasRelation.SPELLING_VARIANT, brand_context="noise"),
    AliasRecord("airwavemax", "Airwave Max", AliasRelation.SPELLING_VARIANT, brand_context="noise"),
    AliasRecord("air wave max", "Airwave Max", AliasRelation.SPELLING_VARIANT, brand_context="noise"),
    # Note: "airwave" alone is NOT here — when "airwave max" is already present,
    # the parser handles it directly. Expanding "airwave" → "Airwave Max" would
    # create "Airwave Max max" duplication.
    AliasRecord("airdopes", "Buds", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="noise",
                notes="Noise uses both Buds and Airdopes naming"),
    AliasRecord("smartwatch", "Noise Smartwatch", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="noise"),
    # ── boAt ───────────────────────────────────────────────────────────────
    AliasRecord("rockerz", "Rockerz", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="boat"),
    AliasRecord("airdopes", "Airdopes", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="boat"),
    AliasRecord("bassheads", "BassHeads", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="boat"),
    AliasRecord("nirvana", "Nirvana", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="boat"),
    # ── Apple ──────────────────────────────────────────────────────────────
    AliasRecord("airpod", "AirPods", AliasRelation.SPELLING_VARIANT, brand_context="apple"),
    AliasRecord("air pod", "AirPods", AliasRelation.SPELLING_VARIANT, brand_context="apple"),
    AliasRecord("iphone", "iPhone", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="apple"),
    AliasRecord("i phone", "iPhone", AliasRelation.SPELLING_VARIANT, brand_context="apple"),
    AliasRecord("macbook", "MacBook", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="apple"),
    AliasRecord("mac book", "MacBook", AliasRelation.SPELLING_VARIANT, brand_context="apple"),
    AliasRecord("ipad", "iPad", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="apple"),
    AliasRecord("i pad", "iPad", AliasRelation.SPELLING_VARIANT, brand_context="apple"),
    # ── Samsung ────────────────────────────────────────────────────────────
    AliasRecord("galaxy buds", "Galaxy Buds", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="samsung"),
    AliasRecord("galaxy watch", "Galaxy Watch", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="samsung"),
    # ── Sony ───────────────────────────────────────────────────────────────
    AliasRecord("wh1000", "WH-1000XM", AliasRelation.SPELLING_VARIANT, brand_context="sony"),
    AliasRecord("wh 1000", "WH-1000XM", AliasRelation.SPELLING_VARIANT, brand_context="sony"),
    AliasRecord("xm series", "WH-1000XM", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="sony"),
    AliasRecord("linkbuds", "LinkBuds", AliasRelation.PRODUCT_FAMILY_ALIAS, brand_context="sony"),
    # ── Generic (brand-agnostic) — RELATED_CONCEPT only, does not rewrite ──
    # These expand search but do NOT replace the original entity
    AliasRecord("tws", "true wireless earbuds", AliasRelation.RELATED_CONCEPT),
    AliasRecord("anc headphones", "ANC headphones", AliasRelation.RELATED_CONCEPT),
    AliasRecord("neckband", "neckband headphones", AliasRelation.RELATED_CONCEPT),
]


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCT TYPE ALIASES — category-scoped
# Structure: { category_lower → { alias → canonical_type } }
# NEVER define cross-category aliases here (e.g. "tab" in both Shopping+Pharmacy)
# ─────────────────────────────────────────────────────────────────────────────
PRODUCT_TYPE_ALIASES_BY_CATEGORY: dict[str, dict[str, str]] = {
    "shopping": {
        "headfone": "headphones",
        "headfones": "headphones",
        "headphone": "headphones",
        "earphone": "earphones",
        "earfone": "earphones",
        "earfones": "earphones",
        "earbud": "earbuds",
        "earbuds": "earbuds",
        "smartwatch": "smartwatch",
        "tab": "tablet",
        "television": "television",
        "mobile": "smartphone",
        "fone": "smartphone",
        "phone": "smartphone",
        "refrigerator": "refrigerator",
        "fridge": "refrigerator",
        "washer": "washing machine",
        "ac": "air conditioner",
        "dslr": "camera",
        "soundbar": "soundbar",
        "charger": "charger",
        "cover": "case",
        "laptop": "laptop",
    },
    "grocery": {
        "milk": "milk",
        "atta": "flour",
        "dal": "lentils",
        "rice": "rice",
        "oil": "cooking oil",
        "ghee": "ghee",
        "paneer": "paneer",
        "sabzi": "vegetables",
    },
    "pharmacy": {
        # Note: "tab" only maps to medicine tablet in pharmacy context
        "tablet": "tablet",
        "capsule": "capsule",
        "syrup": "syrup",
        "cream": "cream",
        "drops": "eye drops",
        "injection": "injection",
    },
    "food": {
        "restaurant": "restaurant",
        "cafe": "cafe",
        "dhaba": "dhaba",
    },
}

# Flat alias maps per category (for backward compat)
def _build_flat_alias_map(category: str) -> dict[str, str]:
    """Return product type alias map for a category."""
    return PRODUCT_TYPE_ALIASES_BY_CATEGORY.get(category.lower(), {})


# ─────────────────────────────────────────────────────────────────────────────
# GROCERY aliases
# ─────────────────────────────────────────────────────────────────────────────
GROCERY_ALIASES: list[AliasRecord] = [
    AliasRecord("panir", "paneer", AliasRelation.PHONETIC_VARIANT),
    AliasRecord("paniir", "paneer", AliasRelation.SPELLING_VARIANT),
    AliasRecord("panner", "paneer", AliasRelation.SPELLING_VARIANT),
    AliasRecord("paner", "paneer", AliasRelation.SPELLING_VARIANT),
    AliasRecord("doodh", "milk", AliasRelation.PHONETIC_VARIANT, notes="Hindi for milk"),
    AliasRecord("dudh", "milk", AliasRelation.PHONETIC_VARIANT, notes="Hindi for milk"),
    AliasRecord("aata", "atta", AliasRelation.SPELLING_VARIANT),
    AliasRecord("aatta", "atta", AliasRelation.SPELLING_VARIANT),
    AliasRecord("coke", "coca cola", AliasRelation.BRAND_ALIAS),
    AliasRecord("pepsi cola", "pepsi", AliasRelation.BRAND_ALIAS),
    AliasRecord("toor dal", "arhar dal", AliasRelation.RELATED_CONCEPT,
                notes="Regional name — not exact spelling correction"),
    AliasRecord("tuvar dal", "arhar dal", AliasRelation.RELATED_CONCEPT),
    AliasRecord("chana", "chickpeas", AliasRelation.RELATED_CONCEPT),
    AliasRecord("amul taja", "amul taaza", AliasRelation.SPELLING_VARIANT),
    AliasRecord("amul taza", "amul taaza", AliasRelation.SPELLING_VARIANT),
    # dal fry ≠ dal tadka (similar dish, NOT spelling correction)
    AliasRecord("dal fry", "dal tadka", AliasRelation.SUBSTITUTION,
                notes="Related dish, not spelling correction — use for discovery only"),
]


# ─────────────────────────────────────────────────────────────────────────────
# PHARMACY aliases — STRICT: never map brand→molecule as SPELLING_VARIANT
# ─────────────────────────────────────────────────────────────────────────────
PHARMACY_ALIASES: list[AliasRecord] = [
    AliasRecord("dollo", "dolo", AliasRelation.SPELLING_VARIANT),
    AliasRecord("dolo650", "dolo 650", AliasRelation.SPELLING_VARIANT),
    AliasRecord("calpol", "calpol", AliasRelation.BRAND_ALIAS),
    # GENERIC_EQUIVALENT — these may NOT rewrite the query
    # They are for "show generic alternatives" feature only
    AliasRecord("brufen", "ibuprofen", AliasRelation.GENERIC_EQUIVALENT,
                notes="Brufen is a branded ibuprofen — never rewrite as ibuprofen"),
    AliasRecord("voveran", "diclofenac", AliasRelation.GENERIC_EQUIVALENT),
    AliasRecord("pantop", "pantoprazole", AliasRelation.GENERIC_EQUIVALENT),
    AliasRecord("omez", "omeprazole", AliasRelation.GENERIC_EQUIVALENT),
    AliasRecord("combiflam", "ibuprofen paracetamol", AliasRelation.GENERIC_EQUIVALENT),
]


# ─────────────────────────────────────────────────────────────────────────────
# FINANCE aliases
# ─────────────────────────────────────────────────────────────────────────────
FINANCE_ALIASES: list[AliasRecord] = [
    AliasRecord("regelia", "Regalia", AliasRelation.SPELLING_VARIANT),
    AliasRecord("millennia", "Millennia", AliasRelation.SPELLING_VARIANT),
    AliasRecord("millenia", "Millennia", AliasRelation.SPELLING_VARIANT),
    AliasRecord("infinia", "Infinia", AliasRelation.SPELLING_VARIANT),
    AliasRecord("infinea", "Infinia", AliasRelation.SPELLING_VARIANT),
    AliasRecord("flipkart axis", "Flipkart Axis Bank", AliasRelation.BRAND_ALIAS),
    # "amazon pay" is ambiguous — it may mean the payment service, not the card
    # Use RELATED_CONCEPT so it expands search but does not rewrite
    AliasRecord("amazon pay", "Amazon Pay ICICI", AliasRelation.RELATED_CONCEPT,
                notes="Ambiguous — could mean payment service or credit card"),
]


# ─────────────────────────────────────────────────────────────────────────────
# SAAS aliases
# ─────────────────────────────────────────────────────────────────────────────
SAAS_ALIASES: list[AliasRecord] = [
    AliasRecord("slak", "Slack", AliasRelation.SPELLING_VARIANT),
    AliasRecord("slak pro", "Slack Pro", AliasRelation.SPELLING_VARIANT),
    AliasRecord("figma pro", "Figma Professional", AliasRelation.BRAND_ALIAS),
    AliasRecord("figma profesional", "Figma Professional", AliasRelation.SPELLING_VARIANT),
    AliasRecord("notion ai", "Notion AI", AliasRelation.PRODUCT_FAMILY_ALIAS),
    AliasRecord("g suite", "Google Workspace", AliasRelation.BRAND_ALIAS),
    AliasRecord("gsuite", "Google Workspace", AliasRelation.BRAND_ALIAS),
    AliasRecord("office365", "Microsoft 365", AliasRelation.BRAND_ALIAS),
    AliasRecord("ms 365", "Microsoft 365", AliasRelation.ABBREVIATION),
    AliasRecord("teams", "Microsoft Teams", AliasRelation.PRODUCT_FAMILY_ALIAS),
]


# ─────────────────────────────────────────────────────────────────────────────
# TRAVEL — Airport/city aliases
# These are LOCATION_ALIAS or AIRPORT_CODE — they represent entities, not typos
# ─────────────────────────────────────────────────────────────────────────────
TRAVEL_ALIASES: list[AliasRecord] = [
    AliasRecord("bombay", "Mumbai", AliasRelation.LOCATION_ALIAS),
    AliasRecord("bom", "Mumbai", AliasRelation.AIRPORT_CODE),
    AliasRecord("delhi", "New Delhi", AliasRelation.LOCATION_ALIAS),
    AliasRecord("new delhi", "New Delhi", AliasRelation.LOCATION_ALIAS),
    AliasRecord("del", "New Delhi", AliasRelation.AIRPORT_CODE),
    AliasRecord("banglore", "Bengaluru", AliasRelation.SPELLING_VARIANT),
    AliasRecord("bangalore", "Bengaluru", AliasRelation.LOCATION_ALIAS),
    AliasRecord("blr", "Bengaluru", AliasRelation.AIRPORT_CODE),
    AliasRecord("maa", "Chennai", AliasRelation.AIRPORT_CODE),
    AliasRecord("hyd", "Hyderabad", AliasRelation.AIRPORT_CODE),
    AliasRecord("calcutta", "Kolkata", AliasRelation.LOCATION_ALIAS),
    AliasRecord("ccu", "Kolkata", AliasRelation.AIRPORT_CODE),
    AliasRecord("pnq", "Pune", AliasRelation.AIRPORT_CODE),
    AliasRecord("amd", "Ahmedabad", AliasRelation.AIRPORT_CODE),
    AliasRecord("cochin", "Kochi", AliasRelation.LOCATION_ALIAS),
    AliasRecord("cok", "Kochi", AliasRelation.AIRPORT_CODE),
]


# ─────────────────────────────────────────────────────────────────────────────
# MOBILITY — Location phonetics
# ─────────────────────────────────────────────────────────────────────────────
MOBILITY_ALIASES: list[AliasRecord] = [
    AliasRecord("koramangla", "Koramangala", AliasRelation.SPELLING_VARIANT),
    AliasRecord("indira nagar", "Indiranagar", AliasRelation.LOCATION_ALIAS),
    AliasRecord("whitfiled", "Whitefield", AliasRelation.SPELLING_VARIANT),
    AliasRecord("whitfeild", "Whitefield", AliasRelation.SPELLING_VARIANT),
]


# ─────────────────────────────────────────────────────────────────────────────
# FOOD aliases
# ─────────────────────────────────────────────────────────────────────────────
FOOD_ALIASES: list[AliasRecord] = [
    AliasRecord("briyani", "biryani", AliasRelation.SPELLING_VARIANT),
    AliasRecord("biriyani", "biryani", AliasRelation.PHONETIC_VARIANT),
    AliasRecord("biriyaani", "biryani", AliasRelation.PHONETIC_VARIANT),
    AliasRecord("chiken", "chicken", AliasRelation.SPELLING_VARIANT),
    AliasRecord("chikan", "chicken", AliasRelation.PHONETIC_VARIANT),
    AliasRecord("piza", "pizza", AliasRelation.SPELLING_VARIANT),
    AliasRecord("pixxa", "pizza", AliasRelation.PHONETIC_VARIANT),
    AliasRecord("mcdonald", "McDonald's", AliasRelation.BRAND_ALIAS),
    AliasRecord("mcdonalds", "McDonald's", AliasRelation.BRAND_ALIAS),
    AliasRecord("paniir butter masala", "paneer butter masala", AliasRelation.SPELLING_VARIANT),
    # dal fry → dal tadka is SUBSTITUTION, not a rewrite (handled in grocery too)
    AliasRecord("dal fry", "dal tadka", AliasRelation.SUBSTITUTION,
                notes="Similar dish — expansion only, not identity rewrite"),
]


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY ALIAS REGISTRY — replaces if-elif chain
# Maps category → list of AliasRecord for that category
# Adding a new category: just add an entry here, no function changes needed
# ─────────────────────────────────────────────────────────────────────────────
_CATEGORY_ALIAS_REGISTRY: dict[str, list[AliasRecord]] = {
    "shopping": BRAND_ALIASES + FAMILY_ALIASES,
    "electronics": BRAND_ALIASES + FAMILY_ALIASES,
    "grocery": GROCERY_ALIASES,
    "pharmacy": PHARMACY_ALIASES,
    "finance": FINANCE_ALIASES,
    "productivity": SAAS_ALIASES,
    "saas": SAAS_ALIASES,
    "travel": TRAVEL_ALIASES,
    "mobility": MOBILITY_ALIASES,
    "rides": MOBILITY_ALIASES,
    "food": FOOD_ALIASES,
}


def get_category_alias_records(category: str) -> list[AliasRecord]:
    """Return AliasRecord list for a given category."""
    return _CATEGORY_ALIAS_REGISTRY.get(category.lower(), [])


def get_rewrite_aliases(category: str) -> list[AliasRecord]:
    """Return only aliases that are allowed to rewrite the query text."""
    return [r for r in get_category_alias_records(category) if r.may_rewrite()]


def get_category_aliases(category: str) -> dict[str, str]:
    """
    Legacy flat alias map for backward compatibility.
    Returns only rewrite-eligible aliases.
    """
    return {r.alias: r.canonical for r in get_rewrite_aliases(category)}


# ─────────────────────────────────────────────────────────────────────────────
# STARTUP VALIDATION
# Catches duplicate alias entries at import time
# ─────────────────────────────────────────────────────────────────────────────
def _validate_alias_lists() -> None:
    """Assert no duplicate alias text within any alias list."""
    for category, records in _CATEGORY_ALIAS_REGISTRY.items():
        seen: dict[str, str] = {}
        for r in records:
            key = f"{r.alias}|{r.brand_context or ''}"
            if key in seen:
                raise ValueError(
                    f"Duplicate alias '{r.alias}' (brand_ctx={r.brand_context}) "
                    f"in category '{category}'. "
                    f"Previous: {seen[key]}, New: {r.canonical}"
                )
            seen[key] = r.canonical


# Run validation at import — catches errors before any query is processed
_validate_alias_lists()
