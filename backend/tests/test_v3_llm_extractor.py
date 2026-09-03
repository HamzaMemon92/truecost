import pytest
from unittest.mock import patch, MagicMock
from app.services.entity_resolution import entity_resolution_service, SourceRecord, ResolutionDecision
from app.schemas.product import TrueCostProduct
from app.services.llm_extractor import BoundedLLMAttributeOutput, ExtractedLLMAttribute
import asyncio

def test_llm_not_called_when_deterministic_sufficient():
    selected = {"name": "FarmXYZ Oats 1kg", "brand": "FarmXYZ"}
    tp = TrueCostProduct(id="prov_test", name="FarmXYZ Oats 1000g", brand="FarmXYZ", url="x", image_url="x", category="Grocery", weight_volume="1000g")
    record = SourceRecord(provider="zepto", product=tp, observed_metadata={})
    
    with patch("app.services.llm_extractor.extractor.extract_missing_factors") as mock_extract:
        res = entity_resolution_service.resolve(query="FarmXYZ Oats 1kg", selected_product=selected, category="Grocery", source_record=record, enable_llm_extraction=True)
        assert res.decision == ResolutionDecision.EXACT
        mock_extract.assert_not_called()

def test_llm_called_when_unresolved_critical_and_enabled():
    selected = {"name": "FarmXYZ Oats 1kg", "brand": "FarmXYZ"}
    tp = TrueCostProduct(id="prov_test", name="FarmXYZ Oats", brand="FarmXYZ", url="x", image_url="x", category="Grocery")
    record = SourceRecord(provider="zepto", product=tp, observed_metadata={})
    
    with patch("app.services.llm_extractor.extractor.extract_missing_factors") as mock_extract:
        mock_extract.return_value = BoundedLLMAttributeOutput(
            attributes=[ExtractedLLMAttribute(factor="pack_size", side="candidate", value={"dimension": "weight", "base_value": 1000, "base_unit": "g"}, confidence=0.9)],
            evidence=["LLM found size"]
        )
        res = entity_resolution_service.resolve(query="FarmXYZ Oats 1kg", selected_product=selected, category="Grocery", source_record=record, enable_llm_extraction=True)
        mock_extract.assert_called_once()

def test_llm_not_called_when_disabled():
    selected = {"name": "FarmXYZ Oats 1kg", "brand": "FarmXYZ"}
    tp = TrueCostProduct(id="prov_test", name="FarmXYZ Oats", brand="FarmXYZ", url="x", image_url="x", category="Grocery")
    record = SourceRecord(provider="zepto", product=tp, observed_metadata={})
    
    with patch("app.services.llm_extractor.extractor.extract_missing_factors") as mock_extract:
        res = entity_resolution_service.resolve(query="FarmXYZ Oats 1kg", selected_product=selected, category="Grocery", source_record=record, enable_llm_extraction=False)
        mock_extract.assert_not_called()

def test_llm_malformed_fallback():
    selected = {"name": "FarmXYZ Oats 1kg", "brand": "FarmXYZ"}
    tp = TrueCostProduct(id="prov_test", name="FarmXYZ Oats", brand="FarmXYZ", url="x", image_url="x", category="Grocery")
    record = SourceRecord(provider="zepto", product=tp, observed_metadata={})
    
    with patch("app.services.llm_extractor.extractor.extract_missing_factors") as mock_extract:
        mock_extract.side_effect = AttributeError("Malformed output")
        res = entity_resolution_service.resolve(query="FarmXYZ Oats 1kg", selected_product=selected, category="Grocery", source_record=record, enable_llm_extraction=True)
        assert res.decision != ResolutionDecision.EXACT
        assert res.llm_extraction["success"] is False
        assert "Malformed" in res.llm_extraction["reason"]

def test_llm_timeout_fallback():
    selected = {"name": "FarmXYZ Oats 1kg", "brand": "FarmXYZ"}
    tp = TrueCostProduct(id="prov_test", name="FarmXYZ Oats", brand="FarmXYZ", url="x", image_url="x", category="Grocery")
    record = SourceRecord(provider="zepto", product=tp, observed_metadata={})
    
    with patch("app.services.llm_extractor.extractor.extract_missing_factors") as mock_extract:
        mock_extract.return_value = None
        res = entity_resolution_service.resolve(query="FarmXYZ Oats 1kg", selected_product=selected, category="Grocery", source_record=record, enable_llm_extraction=True)
        assert res.decision != ResolutionDecision.EXACT
        assert res.llm_extraction["success"] is False
        assert "timeout" in res.llm_extraction["reason"].lower()

def test_structured_evidence_beats_llm():
    selected = {"name": "FarmXYZ Oats 1kg", "brand": "FarmXYZ"}
    tp = TrueCostProduct(id="prov_test", name="FarmXYZ Oats", brand="FarmXYZ", url="x", image_url="x", category="Grocery", weight_volume="500g")
    record = SourceRecord(provider="zepto", product=tp, observed_metadata={})
    
    with patch("app.services.llm_extractor.extractor.extract_missing_factors") as mock_extract:
        res = entity_resolution_service.resolve(query="FarmXYZ Oats 1kg", selected_product=selected, category="Grocery", source_record=record, enable_llm_extraction=True)
        mock_extract.assert_not_called()
        assert res.decision == ResolutionDecision.REJECTED

def test_llm_cannot_override_critical_conflict():
    selected = {"name": "TechNova Phone 64GB", "brand": "TechNova"}
    tp = TrueCostProduct(id="prov_test", name="TechNova Phone 128GB", brand="TechNova", url="x", image_url="x", category="Shopping")
    record = SourceRecord(provider="amazon", product=tp, observed_metadata={})
    
    with patch("app.services.llm_extractor.extractor.extract_missing_factors") as mock_extract:
        res = entity_resolution_service.resolve(query="TechNova Phone 64GB", selected_product=selected, category="Shopping", source_record=record, enable_llm_extraction=True)
        mock_extract.assert_not_called()
        assert res.decision == ResolutionDecision.REJECTED

def test_llm_cannot_produce_exact_authority():
    selected = {"name": "FarmXYZ Oats 1kg", "brand": "FarmXYZ"}
    tp = TrueCostProduct(id="prov_test", name="FarmXYZ Oats", brand="FarmXYZ", url="x", image_url="x", category="Grocery")
    record = SourceRecord(provider="zepto", product=tp, observed_metadata={})
    
    with patch("app.services.llm_extractor.extractor.extract_missing_factors") as mock_extract:
        mock_extract.return_value = BoundedLLMAttributeOutput(
            attributes=[ExtractedLLMAttribute(factor="pack_size", side="candidate", value={"dimension": "weight", "base_value": 1000.0, "base_unit": "g"}, confidence=0.9)],
            evidence=["LLM found size"]
        )
        res = entity_resolution_service.resolve(query="FarmXYZ Oats 1kg", selected_product=selected, category="Grocery", source_record=record, enable_llm_extraction=True)
        assert res.decision == ResolutionDecision.PROBABLE
