import pytest
from app.db import Base
from app.models import DecisionAuditTrail, EntityResolutionRecord, SearchSession, IngestedProviderResult
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

def test_audit_persistence_real_db(tmp_path):
    test_engine = create_engine(f"sqlite:///{tmp_path / 'audit_integ.db'}", connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    Base.metadata.create_all(test_engine)

    db = factory()
    session = SearchSession(category="Shopping", query="Integration Test Product")
    db.add(session)
    db.commit()
    session_id = session.id
    
    audit = EntityResolutionRecord(
        search_session_id=session_id,
        selected_entity={"entity_id": "test", "name": "Test", "brand": "Brand", "category": "Shopping", "attributes": {}},
        candidate_entity={"name": "Integration Test Product"},
        provider_offer={"provider": "amazon", "price": 100.0, "deep_link": "https://www.amazon.in/"},
        legacy_decision="exact",
        v3_decision="probable",
        disagreement=True,
        evidence=[],
        conflicts=[],
        missing_factors=[],
        unknown_attributes={},
        resolver_version="v3.0",
        confidence_inputs=0.9,
        llm_used=False
    )
    db.add(audit)
    db.commit()
    db.close()

    db2 = factory()
    records = db2.query(EntityResolutionRecord).filter(EntityResolutionRecord.search_session_id == session_id).all()
    assert len(records) == 1
    record = records[0]
    
    assert record.search_session_id == session_id
    assert record.legacy_decision == "exact"
    assert record.v3_decision == "probable"
    assert record.disagreement is True
    assert record.evidence == []
    assert record.conflicts == []
    assert record.missing_factors == []
    assert record.unknown_attributes == {}
    assert record.resolver_version == "v3.0"
    assert record.confidence_inputs == 0.9
    assert record.llm_used is False
    
    db2.close()

from fastapi.testclient import TestClient
from app.main import app
from app.db import get_db
from unittest.mock import patch, MagicMock
from app.services.entity_resolution import ResolutionDecision, ResolutionResultV3, CanonicalEntityV3, SourceRecord
from app.schemas.product import TrueCostProduct, ProviderPrice

def test_audit_persistence_aggregator_integration(tmp_path):
    test_engine = create_engine(f"sqlite:///{tmp_path / 'audit_integ2.db'}", connect_args={"check_same_thread": False})
    factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    Base.metadata.create_all(test_engine)

    test_db = factory()
    
    session = SearchSession(category="Shopping", query="Integration Test Product")
    test_db.add(session)
    test_db.commit()
    session_id = session.id
    
    from app.api.endpoints.aggregator import _persist_entity_resolution_records
    
    _persist_entity_resolution_records(test_db, search_session=session, records=[
        {
            "canonical_entity": {"entity_id": "test", "name": "Test", "brand": "Brand", "category": "Shopping", "attributes": {}},
            "raw_offer": {"name": "Integration Test Product"},
            "provider_offer": {"provider": "amazon", "price": 100.0, "deep_link": "https://www.amazon.in/"},
            "legacy_decision": "exact",
            "decision": "probable",
            "disagreement": True,
            "evidence": [],
            "conflicts": [],
            "missing_factors": [],
            "resolver_version": "v3.0",
            "confidence": 0.9
        }
    ])

    records = test_db.query(EntityResolutionRecord).filter(EntityResolutionRecord.search_session_id == session_id).all()
    assert len(records) == 1
    record = records[0]
    assert record.legacy_decision == "exact"
    assert record.v3_decision == "probable"

    test_db.close()
