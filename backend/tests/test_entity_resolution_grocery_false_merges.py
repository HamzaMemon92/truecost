from __future__ import annotations

import pytest

from app.schemas.product import ProviderPrice, TrueCostProduct
from app.services.entity_resolution import ResolutionDecision, SourceRecord, entity_resolution_service


def _resolve(query: str, candidate: str, *, brand: str, weight: str = ""):
    product = TrueCostProduct(
        id=f"fixture-{abs(hash((query, candidate))) % 100000}",
        name=candidate,
        brand=brand,
        category="Grocery",
        weight_volume=weight,
        prices=[ProviderPrice(provider="Blinkit", price=100)],
    )
    return entity_resolution_service.resolve(
        query=query,
        selected_product={"name": query, "brand": brand},
        category="Grocery",
        source_record=SourceRecord(provider="blinkit", product=product, observed_metadata={}),
    )


@pytest.mark.parametrize(
    "query,candidate,brand,weight",
    [
        ("Amul Gold Milk 1L", "Amul Taaza Toned Milk 1 L", "Amul", "1 L"),
        ("True Elements Muesli Fruit and Nuts 750g", "True Elements Muesli Chocolate 750g", "True Elements", "750g"),
        ("Kelloggs Muesli 400g", "Kelloggs Muesli 750g", "Kelloggs", "750g"),
    ],
)
def test_grocery_false_merge_pairs_are_not_exact(query: str, candidate: str, brand: str, weight: str) -> None:
    resolution = _resolve(query, candidate, brand=brand, weight=weight)
    assert resolution.decision != ResolutionDecision.EXACT


def test_grocery_same_brand_same_size_same_variant_can_be_exact() -> None:
    resolution = _resolve("Kelloggs Muesli 400g", "Kelloggs Muesli 400g", brand="Kelloggs", weight="400g")
    assert resolution.decision == ResolutionDecision.EXACT


def test_selected_product_hint_contract_should_include_structured_identity() -> None:
    selected_identity = entity_resolution_service.selected_entity(
        query="Saffola Muesli Choco Crunch",
        selected_product={"name": "Saffola Muesli Choco Crunch with Flavour Pops", "brand": "Saffola", "weightVolume": "700 g"},
        category="Grocery",
    )

    attrs = selected_identity["attributes"]
    assert attrs.get("brand")
    assert attrs.get("pack_size")
