from __future__ import annotations

import re


def normalize_unit(unit: str | None) -> str:
    """Normalize common units to a standard set."""
    if not unit:
        return ""
    
    u = unit.strip().lower()
    
    # Liquid Volume
    if u in ("l", "litre", "liter", "liters", "litres"):
        return "L"
    if u in ("ml", "milliliter", "milliliters", "millilitre", "millilitres"):
        return "ml"
        
    # Weight
    if u in ("kg", "kilogram", "kilograms", "kilo", "kilos"):
        return "kg"
    if u in ("g", "gram", "grams", "gm", "gms"):
        return "g"
        
    # Count/Pieces
    if u in ("pc", "pcs", "piece", "pieces", "count", "pack", "packs"):
        return "pcs"
        
    return u


def normalize_quantity(value: float, unit: str) -> tuple[float, str]:
    """Convert quantities into standardized units (e.g. 500 ml -> 0.5 L)."""
    normalized_u = normalize_unit(unit)
    
    # Standardize everything to L or kg where it makes sense
    if normalized_u == "ml":
        return value / 1000.0, "L"
    if normalized_u == "g":
        return value / 1000.0, "kg"
        
    return value, normalized_u


def normalize_brand(brand: str | None) -> str:
    if not brand:
        return ""
    
    # E.g. "Amul", "amul", " AMUL " -> "amul"
    return brand.strip().lower()


def normalize_category(category: str | None) -> str:
    if not category:
        return ""
    
    # Normalize synonyms
    c = category.strip().lower()
    if c in ("milk", "dairy"):
        return "dairy"
    if c in ("egg", "eggs"):
        return "eggs"
    if c in ("bread", "bakery"):
        return "bakery"
        
    return c
