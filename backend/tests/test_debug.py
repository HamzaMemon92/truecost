import pytest
from app.services.entity_resolution import entity_resolution_service, SourceRecord, ResolutionDecision, EvidenceResult
from app.schemas.product import TrueCostProduct

def test_debug():
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
    
    print("EVIDENCE:", resolution.evidence)
    print("CONFLICTS:", resolution.conflicts)
    print("DECISION:", resolution.decision)
