from app.schemas.product import TrueCostProduct
from app.services.entity_resolution import (
    EntityOfferResolutionService,
    ResolutionDecision,
    SourceRecord,
    get_contract_by_version,
)


def _shopping_record(name: str, *, brand: str = "Noise", provider: str = "flipkart", **extra):
    return SourceRecord(
        provider=provider,
        product=TrueCostProduct(
            id=extra.pop("id", "provider-local-sku"),
            name=name,
            brand=brand,
            url="https://provider.example/item",
            image_url="https://provider.example/item.jpg",
            category="Shopping",
            **extra,
        ),
        observed_metadata={"observed_at": "2026-08-28T00:00:00Z"},
    )


def test_shopping_contract_is_data_driven_and_contains_no_product_name_patches():
    contract = get_contract_by_version("shopping.product.v3")

    assert contract is not None
    assert contract.category_aliases == ("shopping",)
    assert contract.rollout_state == "authoritative_v3_candidate"

    runtime_terms = set(contract.generic_terms)
    product_name_patches = {"noise", "sony", "iphone", "maggi", "amul", "airwave", "taaza"}
    assert runtime_terms.isdisjoint(product_name_patches)


def test_entity_and_offer_are_separate_artifacts():
    resolver = EntityOfferResolutionService()

    result = resolver.resolve(
        query="Noise Airwave Max 6 Bluetooth",
        selected_product={"name": "Noise Airwave Max 6 Bluetooth", "brand": "Noise"},
        category="Shopping",
        source_record=_shopping_record("Noise Airwave Max 6 Bluetooth", price=328),
    )

    payload = result.model_dump()

    assert result.decision == ResolutionDecision.EXACT
    assert payload["selected_entity"]["entity_id"].startswith("tc_entity_")
    assert payload["candidate_entity"]["entity_id"].startswith("tc_entity_")
    assert payload["provider_offer"]["offer_id"].startswith("tc_offer_")
    assert payload["provider_offer"]["entity_id"] == payload["canonical_entity"]["entity_id"]
    assert "price" not in payload["canonical_entity"]["attributes"]
    assert payload["provider_offer"]["provider"] == "flipkart"


def test_provider_sku_is_provider_scoped_not_a_cross_provider_identifier():
    resolver = EntityOfferResolutionService()

    result = resolver.resolve(
        query="Noise Airwave Max 6 Bluetooth",
        selected_product={
            "name": "Noise Airwave Max 6 Bluetooth",
            "brand": "Noise",
            "provider_sku": "same-provider-local-id",
        },
        category="Shopping",
        source_record=_shopping_record(
            "Noise Airwave Max 2 Bluetooth",
            id="same-provider-local-id",
            provider_sku="same-provider-local-id",
        ),
    )

    assert result.decision == ResolutionDecision.REJECTED
    assert any(conflict["factor"] in {"identity_numbers", "model_signature"} for conflict in result.conflicts)
    assert not any(item.get("source") == "identifier_hierarchy" for item in result.evidence)


def test_llm_extraction_cannot_override_explicit_candidate_attributes(monkeypatch):
    resolver = EntityOfferResolutionService()

    class FakeAttr:
        factor = "pack_size"
        side = "candidate"
        value = {"dimension": "weight", "base_value": 1000.0, "base_unit": "g", "raw": "1kg"}
        confidence = 0.99

    class FakeOutput:
        attributes = [FakeAttr()]
        evidence = [{"source": "candidate_title", "text": "provider explicitly said 500g"}]

    async def fake_extract(*_args, **_kwargs):
        return FakeOutput()

    monkeypatch.setattr("app.services.entity_resolution.extractor.extract_missing_factors", fake_extract)

    result = resolver.resolve(
        query="FarmXYZ Oats 1kg",
        selected_product={"name": "FarmXYZ Oats 1kg", "brand": "FarmXYZ"},
        category="Grocery",
        source_record=SourceRecord(
            provider="zepto",
            product=TrueCostProduct(
                id="oats-500",
                name="FarmXYZ Oats 500g",
                brand="FarmXYZ",
                weight_volume="500g",
                url="https://provider.example/oats",
                image_url="https://provider.example/oats.jpg",
                category="Grocery",
            ),
            observed_metadata={},
        ),
        enable_llm_extraction=True,
    )

    assert result.decision == ResolutionDecision.REJECTED
    assert result.llm_extraction is None or result.llm_extraction.get("attributes_extracted", 0) == 0
