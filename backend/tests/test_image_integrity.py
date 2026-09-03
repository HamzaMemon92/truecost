import pytest
from app.providers.canonical_catalog import get_canonical_catalog
from app.schemas.grocery import CanonicalProduct, ImageConfidence

def test_product_images_are_isolated_by_variant():
    """
    Ensure that different variants of the same product do not accidentally
    share the same image URL unless explicitly verified.
    Specifically checks 'Amul Taaza Toned Milk 1L' vs '500ml'.
    """
    catalog = get_canonical_catalog()
    
    amul_500ml = next((p for p in catalog if p.canonical_product_id == "amul-taaza-toned-milk-500ml"), None)
    amul_1l = next((p for p in catalog if p.canonical_product_id == "amul-taaza-toned-milk-1l"), None)
    
    assert amul_500ml is not None
    assert amul_1l is not None
    
    # In our current setup, we use FALLBACK (None) for both to avoid wrong images
    if amul_500ml.image_url is None:
        assert amul_500ml.image_confidence == "FALLBACK"
    
    if amul_1l.image_url is None:
        assert amul_1l.image_confidence == "FALLBACK"
        
    # If they DO have an image URL eventually, they MUST be distinct if the variants have distinct packaging.
    # Since we cannot visually test, we enforce they don't share the same string if they are TRUSTED.
    if amul_500ml.image_url and amul_1l.image_url and amul_500ml.image_confidence == "TRUSTED":
        assert amul_500ml.image_url != amul_1l.image_url, "Variant images must be distinct if trusted"

def test_image_confidence_enums():
    """
    Ensure catalog items strictly follow the image confidence enums.
    """
    catalog = get_canonical_catalog()
    valid_confidences = {"TRUSTED", "KNOWN_SOURCE", "FALLBACK", "UNVERIFIED"}
    
    for product in catalog:
        assert product.image_confidence in valid_confidences, f"Invalid confidence {product.image_confidence} on {product.canonical_product_id}"
