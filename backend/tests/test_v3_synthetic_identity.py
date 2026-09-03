import pytest
from app.services.entity_resolution import entity_resolution_service, SourceRecord, ResolutionDecision, EvidenceResult
from app.schemas.product import TrueCostProduct

def test_synthetic_shopping_exact_match():
    query = "BrandZXQ SeriesNova Model731 512GB"
    selected = {"name": query, "brand": "BrandZXQ"}
    
    tp = TrueCostProduct(
        id="prov_123",
        name="BrandZXQ SeriesNova Model731 - 512GB (Midnight Black)",
        brand="BrandZXQ",
        url="http://x",
        image_url="http://x.jpg",
        category="Shopping",
        color="Midnight Black"
    )
    
    record = SourceRecord(provider="amazon", product=tp, observed_metadata={})
    resolution = entity_resolution_service.resolve(
        query=query,
        selected_product=selected,
        category="Shopping",
        source_record=record,
    )
    
    assert resolution.decision == ResolutionDecision.EXACT
    assert "model731" in resolution.canonical_entity.attributes["identity_numbers"]
    assert resolution.canonical_entity.attributes["storage"] == "512gb"
    assert resolution.canonical_entity.attributes["brand"] == "brandzxq"

def test_synthetic_shopping_conflict():
    query = "BrandZXQ SeriesNova Model731 512GB"
    selected = {"name": query, "brand": "BrandZXQ"}
    
    tp = TrueCostProduct(
        id="prov_456",
        name="BrandZXQ SeriesNova Model732 - 512GB (Midnight Black)",
        brand="BrandZXQ",
        url="http://x",
        image_url="http://x.jpg",
        category="Shopping",
        color="Midnight Black"
    )
    
    record = SourceRecord(provider="amazon", product=tp, observed_metadata={})
    resolution = entity_resolution_service.resolve(
        query=query,
        selected_product=selected,
        category="Shopping",
        source_record=record,
    )
    
    assert resolution.decision == ResolutionDecision.REJECTED
    conflicts = [c["factor"] for c in resolution.conflicts]
    assert "identity_numbers" in conflicts or "model_signature" in conflicts

def test_synthetic_grocery_exact_match():
    query = "FarmXYZ Organic QuantumFlakes 500g"
    selected = {"name": query, "brand": "FarmXYZ"}
    
    tp = TrueCostProduct(
        id="prov_789",
        name="FarmXYZ Organic QuantumFlakes Cereal 500g Pack",
        brand="FarmXYZ",
        url="http://x",
        image_url="http://x.jpg",
        category="Grocery"
    )
    
    record = SourceRecord(provider="zepto", product=tp, observed_metadata={})
    resolution = entity_resolution_service.resolve(
        query=query,
        selected_product=selected,
        category="Grocery",
        source_record=record,
    )
    
    assert resolution.decision == ResolutionDecision.EXACT
    assert resolution.canonical_entity.attributes["pack_size"]["base_value"] == 500.0
    assert resolution.canonical_entity.attributes["brand"] == "farmxyz"

def test_size_normalization():
    query = "TestBrand Liquid 1L"
    selected = {"name": query, "brand": "TestBrand"}
    
    tp = TrueCostProduct(
        id="prov_999",
        name="TestBrand Liquid 1000ml",
        brand="TestBrand",
        url="http://x",
        image_url="http://x.jpg",
        category="Grocery",
        weight_volume="1000ml"
    )
    
    record = SourceRecord(provider="zepto", product=tp, observed_metadata={})
    resolution = entity_resolution_service.resolve(
        query=query,
        selected_product=selected,
        category="Grocery",
        source_record=record,
    )
    
    assert resolution.decision == ResolutionDecision.EXACT
    assert resolution.canonical_entity.attributes["pack_size"]["base_value"] == 1000.0
    assert resolution.canonical_entity.attributes["pack_size"]["base_unit"] == "ml"

def test_strong_identifier_match():
    query = "Generic Item"
    selected = {"name": query, "upc": "123456789012"}
    
    tp = TrueCostProduct(
        id="prov_id",
        name="Generic Item But Different Name",
        upc="123456789012",
        brand="GenericBrand",
        url="http://x",
        image_url="http://x.jpg",
        category="Shopping"
    )
    
    record = SourceRecord(provider="amazon", product=tp, observed_metadata={})
    resolution = entity_resolution_service.resolve(
        query=query,
        selected_product=selected,
        category="Shopping",
        source_record=record,
    )
    
    assert resolution.decision == ResolutionDecision.EXACT
    assert any(e["factor"] == "strong_identifier" and e["result"] == EvidenceResult.MATCH.value for e in resolution.evidence)

def test_strong_identifier_conflict():
    query = "Generic Item"
    selected = {"name": query, "upc": "123456789012"}
    
    tp = TrueCostProduct(
        id="prov_id",
        name="Generic Item",
        upc="999999999999",
        brand="GenericBrand",
        url="http://x",
        image_url="http://x.jpg",
        category="Shopping"
    )
    
    record = SourceRecord(provider="amazon", product=tp, observed_metadata={})
    resolution = entity_resolution_service.resolve(
        query=query,
        selected_product=selected,
        category="Shopping",
        source_record=record,
    )
    
    assert resolution.decision == ResolutionDecision.REJECTED
    assert any(c["factor"] == "upc" and c["result"] == EvidenceResult.CONFLICT.value for c in resolution.conflicts)
@pytest.mark.parametrize("query,candidate_name,candidate_attrs,expected_decision", [
    # Extra descriptive words (capitalization/punctuation)
    ("TechNova Phone 64GB", "TechNova Phone - 64GB (Refurbished) Excellent Condition!", {"color": "Blue"}, ResolutionDecision.REJECTED),
    # Conflicting model
    ("TechNova Phone 64GB", "TechNova Phone Max 64GB", {}, ResolutionDecision.REJECTED),
    # Conflicting storage
    ("TechNova Phone 64GB", "TechNova Phone 128GB", {}, ResolutionDecision.REJECTED),
    # Variant change
    ("TechNova Phone 64GB", "TechNova Phone 64GB Pro", {}, ResolutionDecision.REJECTED),
    # Missing attributes - fallback to probable or rejected depending on strictness
    ("TechNova Phone 64GB", "TechNova Device", {}, ResolutionDecision.REJECTED),
])
def test_parameterized_product_matching(query, candidate_name, candidate_attrs, expected_decision):
    selected = {"name": query, "brand": "TechNova"}
    tp = TrueCostProduct(
        id="prov_test",
        name=candidate_name,
        brand="TechNova",
        url="http://x",
        image_url="http://x.jpg",
        category="Shopping",
        **candidate_attrs
    )
    record = SourceRecord(provider="amazon", product=tp, observed_metadata={})
    resolution = entity_resolution_service.resolve(
        query=query,
        selected_product=selected,
        category="Shopping",
        source_record=record,
    )
    assert resolution.decision == expected_decision

@pytest.mark.parametrize("query,candidate_name,candidate_pack_size,expected_decision", [
    # Pack-size change
    ("FarmXYZ Oats 1kg", "FarmXYZ Oats 1000g", "1000g", ResolutionDecision.EXACT),
    ("FarmXYZ Oats 1kg", "FarmXYZ Oats 500g", "500g", ResolutionDecision.REJECTED),
    # Unit formatting
    ("FarmXYZ Oats 1 KG", "FarmXYZ Oats 1kg", "1kg", ResolutionDecision.EXACT),
    # Provider metadata mistaken for brand
    ("FarmXYZ Oats 1kg", "Zepto FarmXYZ Oats 1kg", "1kg", ResolutionDecision.EXACT),
])
def test_parameterized_grocery_matching(query, candidate_name, candidate_pack_size, expected_decision):
    selected = {"name": query, "brand": "FarmXYZ"}
    tp = TrueCostProduct(
        id="prov_test",
        name=candidate_name,
        brand="FarmXYZ",
        url="http://x",
        image_url="http://x.jpg",
        category="Grocery",
        weight_volume=candidate_pack_size
    )
    record = SourceRecord(provider="zepto", product=tp, observed_metadata={})
    resolution = entity_resolution_service.resolve(
        query=query,
        selected_product=selected,
        category="Grocery",
        source_record=record,
    )
    assert resolution.decision == expected_decision

