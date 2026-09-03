import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.services.entity_resolution import ResolutionDecision
from app.models import SearchSession, IngestedProviderResult, User
from datetime import datetime

@pytest.fixture(autouse=True)
def disable_esci():
    with patch("app.services.search_intelligence.search_intelligence", side_effect=Exception("mocked SI to disable ESCI re-scoring")):
        yield

@pytest.fixture
def client_with_session():
    with TestClient(app) as client:
        # Create a mock session via ingest endpoint
        ingested = client.post(
            "/api/v1/aggregator/ingest",
            json={
                "provider": "Amazon",
                "category": "Shopping",
                "query": "Test Product",
                "raw_data": {"items": [
                    {"id": "prod_1", "name": "Test Product Exact", "price": 200},
                    {"id": "prod_2", "name": "Test Product Probable", "price": 100},
                ]},
            },
        )
        session_id = ingested.headers["X-Search-Session-Id"]
        yield client, session_id

def test_endpoint_mode_shadow(client_with_session):
    client, session_id = client_with_session
    
    with patch("app.api.endpoints.aggregator.settings") as mock_settings:
        mock_settings.entity_resolution_mode = "shadow"
        mock_settings.entity_resolution_rollback_to_legacy = False
        mock_settings.entity_resolution_llm_extraction_enabled = False
        
        with patch("app.api.endpoints.aggregator.entity_resolution_service") as mock_v3, \
             patch("app.api.endpoints.aggregator.identity_engine") as mock_legacy:
            
            mock_v3.supports.return_value = True
            mock_v3.selected_entity.return_value = {"mode": "shadow"}
            mock_legacy.selected_identity.return_value = {"mode": "legacy"}
            
            # Legacy decides prod_1 is EXACT, prod_2 is REJECTED
            def mock_compare(*args, **kwargs):
                prod = kwargs.get("provider_product")
                m = MagicMock()
                if "Exact" in prod.name: m.match_tier = "exact"; m.match_score = 1.0; m.rejection_reason = None
                else: m.match_tier = "rejected"; m.match_score = 0.1; m.rejection_reason = "mismatch"
                m.model_dump.return_value = {"match_tier": m.match_tier, "match_score": m.match_score}
                return m
            mock_legacy.compare.side_effect = mock_compare
            
            # V3 decides prod_2 is EXACT (contrary to legacy), prod_1 is REJECTED
            def mock_resolve(*args, **kwargs):
                rec = kwargs.get("source_record")
                m = MagicMock()
                if "Probable" in rec.product.name:
                    m.decision = ResolutionDecision.EXACT
                else:
                    m.decision = ResolutionDecision.REJECTED
                m.confidence = 0.9
                m.canonical_entity.entity_id = "v3_mock_id"
                m.canonical_entity.model_dump.return_value = {"id": "v3_mock_id"}
                m.provider_offer.model_dump.return_value = {"price": rec.product.prices[0].price}
                m.model_dump.return_value = {"decision": m.decision.value}
                return m
            mock_v3.resolve.side_effect = mock_resolve
            
            res = client.get(f"/api/v1/aggregator/search?q=Test Product&category=Shopping&session_id={session_id}&exact_match=true")
            data = res.json()
            
            # In SHADOW mode, legacy is authoritative. Legacy says Exact is Exact. So best_observed should be Exact (price 200).
            assert data["discovery_report"]["best_observed"]["product"]["name"] == "Test Product Exact"
            assert data["discovery_report"]["best_observed"]["offer"]["price"] == 200

def test_endpoint_mode_v3(client_with_session):
    client, session_id = client_with_session
    
    with patch("app.api.endpoints.aggregator.settings") as mock_settings:
        mock_settings.entity_resolution_mode = "v3"
        mock_settings.entity_resolution_rollback_to_legacy = False
        mock_settings.entity_resolution_llm_extraction_enabled = False
        
        with patch("app.api.endpoints.aggregator.entity_resolution_service") as mock_v3:
            
            mock_v3.supports.return_value = True
            mock_v3.selected_entity.return_value = {"mode": "v3"}
            
            # V3 decides prod_1 is PROBABLE, prod_2 is EXACT
            def mock_resolve(*args, **kwargs):
                rec = kwargs.get("source_record")
                m = MagicMock()
                if "Probable" in rec.product.name:
                    m.decision = ResolutionDecision.PROBABLE
                else:
                    m.decision = ResolutionDecision.EXACT
                m.confidence = 0.9
                m.canonical_entity.entity_id = "v3_mock_id"
                m.canonical_entity.model_dump.return_value = {"id": "v3_mock_id"}
                m.provider_offer.model_dump.return_value = {"price": rec.product.prices[0].price}
                m.model_dump.return_value = {"decision": m.decision.value}
                return m
            mock_v3.resolve.side_effect = mock_resolve
            
            res = client.get(f"/api/v1/aggregator/search?q=Test Product&category=Shopping&session_id={session_id}&exact_match=true")
            data = res.json()
            
            # In V3 mode, v3 is authoritative. Exact is prod_1 (price 200). Probable is prod_2 (price 100).
            # EXACT must determine best_observed, even if PROBABLE is cheaper!
            assert data["discovery_report"]["best_observed"]["product"]["name"] == "Test Product Exact"
            assert data["discovery_report"]["best_observed"]["offer"]["price"] == 200
            assert data["probable_results"][0]["name"] == "Test Product Probable"
            assert data["discovery_report"]["probable_results"][0]["name"] == "Test Product Probable"
            assert data["discovery_report"]["probable_results"][0]["name"] not in [
                item["name"] for item in data["discovery_report"]["exact_results"]
            ]

def test_endpoint_mode_rollback(client_with_session):
    client, session_id = client_with_session
    
    with patch("app.api.endpoints.aggregator.settings") as mock_settings:
        mock_settings.entity_resolution_mode = "v3"
        mock_settings.entity_resolution_rollback_to_legacy = True
        mock_settings.entity_resolution_llm_extraction_enabled = False
        
        with patch("app.api.endpoints.aggregator.entity_resolution_service") as mock_v3, \
             patch("app.api.endpoints.aggregator.identity_engine") as mock_legacy:
            
            mock_v3.supports.return_value = True
            mock_v3.selected_entity.return_value = {"mode": "rollback"}
            mock_legacy.selected_identity.return_value = {"mode": "legacy"}
            
            # Legacy decides prod_1 is EXACT
            def mock_compare(*args, **kwargs):
                prod = kwargs.get("provider_product")
                m = MagicMock()
                if "Exact" in prod.name: m.match_tier = "exact"; m.match_score = 1.0; m.rejection_reason = None
                else: m.match_tier = "rejected"; m.match_score = 0.1; m.rejection_reason = "mismatch"
                m.model_dump.return_value = {"match_tier": m.match_tier, "match_score": m.match_score}
                return m
            mock_legacy.compare.side_effect = mock_compare
            
            # Rollback means v3 isn't even called (or its result is ignored)
            res = client.get(f"/api/v1/aggregator/search?q=Test Product&category=Shopping&session_id={session_id}&exact_match=true")
            data = res.json()
            
            assert data["discovery_report"]["best_observed"]["product"]["name"] == "Test Product Exact"

def test_endpoint_mode_v3_zero_exact(client_with_session):
    client, session_id = client_with_session
    
    with patch("app.api.endpoints.aggregator.settings") as mock_settings:
        mock_settings.entity_resolution_mode = "v3"
        mock_settings.entity_resolution_rollback_to_legacy = False
        mock_settings.entity_resolution_llm_extraction_enabled = False
        
        with patch("app.api.endpoints.aggregator.entity_resolution_service") as mock_v3:
            
            mock_v3.supports.return_value = True
            mock_v3.selected_entity.return_value = {"mode": "v3"}
            
            # V3 decides BOTH are PROBABLE
            def mock_resolve(*args, **kwargs):
                rec = kwargs.get("source_record")
                m = MagicMock()
                m.decision = ResolutionDecision.PROBABLE
                m.confidence = 0.5
                m.canonical_entity.entity_id = "v3_mock_id"
                m.canonical_entity.model_dump.return_value = {"id": "v3_mock_id"}
                m.provider_offer.model_dump.return_value = {"price": rec.product.prices[0].price}
                m.model_dump.return_value = {"decision": m.decision.value}
                return m
            mock_v3.resolve.side_effect = mock_resolve
            
            res = client.get(f"/api/v1/aggregator/search?q=Test Product&category=Shopping&session_id={session_id}&exact_match=true")
            data = res.json()
            
            # Zero exact offers -> best_observed must be null
            assert data["discovery_report"].get("best_observed") is None
            assert len(data["probable_results"]) == 2
            assert len(data["discovery_report"]["probable_results"]) == 2
