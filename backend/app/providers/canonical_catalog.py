from __future__ import annotations

from app.schemas.grocery import CanonicalProduct

MOCK_CATALOG = [
    # MILK
    CanonicalProduct(
        canonical_product_id="amul-taaza-toned-milk-500ml",
        title="Amul Taaza Toned Milk",
        brand="Amul",
        category="dairy",
        variant="milk",
        normalized_quantity=0.5,
        normalized_unit="L",
        base_price_estimate=27.0,
        image_url="https://cdn.grofers.com/cdn-cgi/image/f=auto,fit=scale-down,q=70,metadata=none,w=270/app/images/products/sliding_image/159a.jpg",
        image_confidence="TRUSTED",
        tags=["toned", "taaza", "fresh"]
    ),
    CanonicalProduct(
        canonical_product_id="amul-taaza-toned-milk-1l",
        title="Amul Taaza Toned Milk",
        brand="Amul",
        category="dairy",
        variant="milk",
        normalized_quantity=1.0,
        normalized_unit="L",
        base_price_estimate=54.0,
        image_url="https://cdn.grofers.com/cdn-cgi/image/f=auto,fit=scale-down,q=70,metadata=none,w=270/app/images/products/sliding_image/160a.jpg",
        image_confidence="TRUSTED",
        tags=["toned", "taaza", "fresh"]
    ),
    CanonicalProduct(
        canonical_product_id="amul-gold-full-cream-milk-500ml",
        title="Amul Gold Full Cream Milk",
        brand="Amul",
        category="dairy",
        variant="milk",
        normalized_quantity=0.5,
        normalized_unit="L",
        base_price_estimate=33.0,
        image_url="https://cdn.grofers.com/cdn-cgi/image/f=auto,fit=scale-down,q=70,metadata=none,w=270/app/images/products/sliding_image/105655a.jpg",
        image_confidence="TRUSTED",
        tags=["gold", "full cream"]
    ),
    CanonicalProduct(
        canonical_product_id="amul-gold-full-cream-milk-1l",
        title="Amul Gold Full Cream Milk",
        brand="Amul",
        category="dairy",
        variant="milk",
        normalized_quantity=1.0,
        normalized_unit="L",
        base_price_estimate=66.0,
        image_url="https://cdn.grofers.com/cdn-cgi/image/f=auto,fit=scale-down,q=70,metadata=none,w=270/app/images/products/sliding_image/161a.jpg",
        image_confidence="TRUSTED",
        tags=["gold", "full cream"]
    ),
    CanonicalProduct(
        canonical_product_id="mother-dairy-toned-milk-500ml",
        title="Mother Dairy Toned Milk",
        brand="Mother Dairy",
        category="dairy",
        variant="milk",
        normalized_quantity=0.5,
        normalized_unit="L",
        base_price_estimate=27.0,
        image_url=None,
        image_confidence="FALLBACK",
        tags=["toned"]
    ),
    CanonicalProduct(
        canonical_product_id="mother-dairy-toned-milk-1l",
        title="Mother Dairy Toned Milk",
        brand="Mother Dairy",
        category="dairy",
        variant="milk",
        normalized_quantity=1.0,
        normalized_unit="L",
        base_price_estimate=54.0,
        image_url=None,
        image_confidence="FALLBACK",
        tags=["toned"]
    ),
    CanonicalProduct(
        canonical_product_id="nandini-toned-milk-1l",
        title="Nandini Toned Milk",
        brand="Nandini",
        category="dairy",
        variant="milk",
        normalized_quantity=1.0,
        normalized_unit="L",
        base_price_estimate=44.0,
        image_url=None,
        image_confidence="FALLBACK",
        tags=["toned"]
    ),
    
    # EGGS
    CanonicalProduct(
        canonical_product_id="farm-eggs-6pcs",
        title="Farm Fresh White Eggs",
        brand="Unknown",
        category="eggs",
        variant="eggs",
        normalized_quantity=6.0,
        normalized_unit="pcs",
        pack_count=6,
        base_price_estimate=40.0,
        image_url="https://cdn.grofers.com/cdn-cgi/image/f=auto,fit=scale-down,q=70,metadata=none,w=270/app/images/products/sliding_image/168434a.jpg",
        image_confidence="TRUSTED",
        tags=["white", "farm"]
    ),
    CanonicalProduct(
        canonical_product_id="farm-eggs-12pcs",
        title="Farm Fresh White Eggs",
        brand="Unknown",
        category="eggs",
        variant="eggs",
        normalized_quantity=12.0,
        normalized_unit="pcs",
        pack_count=12,
        base_price_estimate=80.0,
        image_url="https://cdn.grofers.com/cdn-cgi/image/f=auto,fit=scale-down,q=70,metadata=none,w=270/app/images/products/sliding_image/168434a.jpg",
        image_confidence="TRUSTED",
        tags=["white", "farm"]
    ),
    
    # BREAD
    CanonicalProduct(
        canonical_product_id="britannia-white-bread-400g",
        title="Britannia Daily Fresh White Bread",
        brand="Britannia",
        category="bakery",
        variant="bread",
        normalized_quantity=0.4,
        normalized_unit="kg",
        base_price_estimate=30.0,
        image_url="https://cdn.grofers.com/cdn-cgi/image/f=auto,fit=scale-down,q=70,metadata=none,w=270/app/images/products/sliding_image/13251a.jpg",
        image_confidence="TRUSTED",
        tags=["white", "daily fresh"]
    ),
    
    # COFFEE
    CanonicalProduct(
        canonical_product_id="nescafe-classic-instant-coffee-50g",
        title="Nescafe Classic Instant Coffee",
        brand="Nescafe",
        category="beverages",
        variant="coffee",
        normalized_quantity=50.0,
        normalized_unit="g",
        base_price_estimate=150.0,
        image_url="https://cdn.grofers.com/da/cms-assets/cms/product/9a4c1d73-d959-4fac-994a-bd95414155d4.jpg",
        image_confidence="TRUSTED",
        tags=["coffee", "classic", "instant"]
    ),
    
    # DECOYS (to prove search filtering works)
    CanonicalProduct(
        canonical_product_id="steel-milk-pan-1l",
        title="Stainless Steel Milk Pan",
        brand="Unknown",
        category="cookware",
        variant="pan",
        normalized_quantity=1.0,
        normalized_unit="L",
        base_price_estimate=350.0,
        image_url=None,
        image_confidence="FALLBACK",
        tags=["steel", "milk pan"]
    ),
    CanonicalProduct(
        canonical_product_id="pedigree-dog-food-milk-1kg",
        title="Pedigree Puppy Dog Food with Milk & Chicken",
        brand="Pedigree",
        category="pets",
        variant="dog food",
        normalized_quantity=1.0,
        normalized_unit="kg",
        base_price_estimate=250.0,
        image_url=None,
        image_confidence="FALLBACK",
        tags=["puppy", "milk"]
    )
]

def get_canonical_catalog() -> list[CanonicalProduct]:
    return MOCK_CATALOG
