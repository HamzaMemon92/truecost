import pytest
from datetime import datetime, timezone, timedelta
from app.db import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import EntityResolutionRecord, SearchSession
from app.services.entity_resolution_metrics import EntityResolutionMetricsService
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_db
import os

@pytest.fixture
def memory_db():
    engine = create_engine('sqlite://', connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    engine.dispose()

def create_synthetic_record(db, **kwargs):
    s = SearchSession(category="Shopping", query="Test")
    db.add(s)
    db.commit()
    
    defaults = {
        "search_session_id": s.id,
        "selected_entity": {"category": "Shopping", "attributes": {"brand": "Apple"}},
        "candidate_entity": {"name": "Test Product Data with words"},
        "provider_offer": {"provider": "amazon", "raw_offer": {"desc": "more text"}},
        "legacy_decision": "exact",
        "v3_decision": "exact",
        "disagreement": False,
        "evidence": [],
        "conflicts": [],
        "missing_factors": [],
        "unknown_attributes": {},
        "resolver_version": "shopping.product.v3",
        "confidence_inputs": 0.9,
        "llm_used": False,
        "created_at": datetime.now(timezone.utc)
    }
    defaults.update(kwargs)
    r = EntityResolutionRecord(**defaults)
    db.add(r)
    db.commit()
    return r

def test_empty_metrics(memory_db):
    svc = EntityResolutionMetricsService(memory_db)
    metrics = svc.get_metrics()
    assert metrics["total_resolutions"] == 0
    for k, v in metrics["decision_distribution"].items():
        assert v == 0
    for k, v in metrics["decision_percentages"].items():
        assert v == 0.0
    assert metrics["reviewed_quality"]["v3_exact_precision"] is None
    assert metrics["reviewed_quality"]["reviewed_sample_false_merge_rate"] is None

def test_decision_distribution(memory_db):
    create_synthetic_record(memory_db, v3_decision="exact")
    create_synthetic_record(memory_db, v3_decision="probable")
    create_synthetic_record(memory_db, v3_decision="related")
    create_synthetic_record(memory_db, v3_decision="rejected")
    svc = EntityResolutionMetricsService(memory_db)
    metrics = svc.get_metrics()
    assert metrics["total_resolutions"] == 4
    assert metrics["decision_distribution"]["EXACT"] == 1
    assert metrics["decision_distribution"]["PROBABLE"] == 1
    assert metrics["decision_distribution"]["RELATED"] == 1
    assert metrics["decision_distribution"]["REJECTED"] == 1
    assert metrics["decision_percentages"]["EXACT"] == 0.25

def test_disagreement_matrix(memory_db):
    create_synthetic_record(memory_db, legacy_decision="exact", v3_decision="probable", disagreement=True)
    svc = EntityResolutionMetricsService(memory_db)
    metrics = svc.get_metrics()
    assert metrics["legacy_v3_disagreement"]["disagreement_count"] == 1
    assert metrics["disagreement_matrix"]["EXACT -> PROBABLE"] == 1

def test_provider_and_category_metrics(memory_db):
    create_synthetic_record(memory_db, provider_offer={"provider": "zepto"}, selected_entity={"category": "Grocery"}, missing_factors=["storage", "color"], conflicts=[{"factor": "brand", "severity": "minor"}])
    create_synthetic_record(memory_db, provider_offer={"provider": "blinkit"}, selected_entity={"category": "Grocery"}, conflicts=[{"factor": "brand"}, {"factor": "brand"}])
    svc = EntityResolutionMetricsService(memory_db)
    metrics = svc.get_metrics()
    
    pdict = {p["provider"]: p for p in metrics["providers"]}
    assert pdict["zepto"]["records_with_missing_factors_rate"] == 1.0
    assert pdict["zepto"]["avg_missing_factors_per_resolution"] == 2.0
    assert pdict["blinkit"]["records_with_conflicts_rate"] == 1.0
    assert pdict["blinkit"]["avg_conflicts_per_resolution"] == 2.0
    
    cdict = {c["category"]: c for c in metrics["categories"]}
    assert cdict["grocery"]["avg_missing_factors_per_resolution"] == 1.0
    
    assert pdict["zepto"]["cross_breakdowns"]["missing"][0]["record_count"] == 1
    
    for prov in pdict.values():
        assert 0 <= prov["exact_rate"] <= 1
        assert 0 <= prov["records_with_missing_factors_rate"] <= 1

def test_filters(memory_db):
    now = datetime.now(timezone.utc)
    create_synthetic_record(memory_db, provider_offer={"provider": "Amazon"}, selected_entity={"category": "GroCery"}, resolver_version="shopping.product.v3", created_at=now - timedelta(days=2))
    create_synthetic_record(memory_db, provider_offer={"provider": "Zepto"}, resolver_version="shopping.product.v999", created_at=now)
    svc = EntityResolutionMetricsService(memory_db)
    
    # Case insensitive
    assert svc.get_metrics(provider="amaZon")["total_resolutions"] == 1
    assert svc.get_metrics(category="grocEry")["total_resolutions"] == 1
    
    # Unknown contract
    met = svc.get_metrics(resolver_version="shopping.product.v999")
    assert met["total_resolutions"] == 1
    assert met["unknown_contract_status"]["unknown_contract_version_count"] == 1
    assert met["unknown_contract_status"]["unknown_contract_versions"]["shopping.product.v999"] == 1
    assert met["identity_completeness"]["average_identity_completeness"] is None

def test_unknown_attributes(memory_db):
    create_synthetic_record(memory_db, unknown_attributes={"future_feature": "abc", "seller_id": "xyz"})
    create_synthetic_record(memory_db)
    svc = EntityResolutionMetricsService(memory_db)
    metrics = svc.get_metrics()
    uaa = metrics["unknown_attribute_analysis"]
    assert uaa["unknown_attribute_rate"] == 0.5
    assert len(uaa["aggregated_names"]) == 2
    for item in uaa["aggregated_names"]:
        if item["attribute"] == "future_feature":
            assert item["count"] == 1

def test_identity_completeness(memory_db):
    create_synthetic_record(memory_db, selected_entity={"category": "Shopping", "attributes": {"brand": "Apple", "storage": "256GB", "model_signature": "iPhone"}})
    svc = EntityResolutionMetricsService(memory_db)
    metrics = svc.get_metrics()
    assert metrics["identity_completeness"]["average_identity_completeness"] == 0.5

def test_llm_candidate_telemetry(memory_db):
    create_synthetic_record(memory_db, provider_offer={"provider": "amazon", "raw_offer": {"title": "something 256gb text text"}}, missing_factors=["storage"], conflicts=[])
    create_synthetic_record(memory_db, provider_offer={"provider": "amazon", "raw_offer": {"title": "something 256gb text text"}}, missing_factors=["storage"], conflicts=[{"factor": "brand", "severity": "critical"}])
    create_synthetic_record(memory_db, provider_offer={"provider": "amazon", "raw_offer": {"title": "something 256gb text text"}}, missing_factors=["title_terms"], conflicts=[])
    svc = EntityResolutionMetricsService(memory_db)
    metrics = svc.get_metrics()
    llm = metrics["llm_opportunity_report"]
    assert llm["llm_candidate_count"] == 1
    assert llm["potential_llm_calls_per_1000_resolutions"] == round((1/3) * 1000, 1)
    assert llm["top_llm_candidate_factors"][0]["factor"] == "storage"
    assert llm["provider_llm_candidate_breakdown"][0]["provider"] == "amazon"

def test_reviewed_quality(memory_db):
    create_synthetic_record(memory_db, v3_decision="exact", review_label="V3_CORRECT")
    create_synthetic_record(memory_db, v3_decision="exact", review_label="BOTH_WRONG", review_error_classification="FALSE_MERGE")
    create_synthetic_record(memory_db, v3_decision="probable", review_label="V3_CORRECT")
    create_synthetic_record(memory_db, v3_decision="rejected", review_label="LEGACY_CORRECT", review_error_classification="FALSE_REJECT")
    
    svc = EntityResolutionMetricsService(memory_db)
    metrics = svc.get_metrics()
    rq = metrics["reviewed_quality"]
    
    assert rq["reviewed_v3_exact_count"] == 2
    assert rq["v3_exact_precision"] == 0.5
    assert rq["v3_false_merge_count"] == 1
    assert rq["reviewed_sample_false_merge_rate"] == 0.5
    assert rq["reviewed_v3_probable_count"] == 1
    assert rq["probable_precision"] == 1.0
    assert rq["v3_false_reject_count"] == 1

def test_factor_record_rate_semantics(memory_db):
    create_synthetic_record(memory_db, missing_factors=["storage", "storage"])
    svc = EntityResolutionMetricsService(memory_db)
    metrics = svc.get_metrics()
    storage_metric = next(f for f in metrics["missing_factors"] if f["factor"] == "storage")
    assert storage_metric["record_count"] == 1
    assert storage_metric["occurrence_count"] == 2
    assert storage_metric["record_rate"] == 1.0

def test_pagination(memory_db):
    for _ in range(15):
        create_synthetic_record(memory_db, provider_offer={"provider": "amazon"})
    for _ in range(5):
        create_synthetic_record(memory_db, provider_offer={"provider": "zepto"})
    svc = EntityResolutionMetricsService(memory_db)
    zepto_records = svc.get_records(provider="zepto", limit=3, offset=1)
    assert len(zepto_records) == 3
    assert all(r["provider"] == "zepto" for r in zepto_records)

def test_endpoints_auth_and_review():
    test_db_url = 'sqlite:///./test_metrics.db'
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    r = create_synthetic_record(db)
    record_id = r.id
    
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    
    # Auth reject
    assert client.get("/api/v1/admin/entity-resolution/shadow/metrics").status_code in (401, 403)
    
    class MockAdmin:
        id = "admin"
        
    from app.api.endpoints.admin import require_admin
    app.dependency_overrides[require_admin] = lambda: MockAdmin()
    
    # Auth accept
    assert client.get("/api/v1/admin/entity-resolution/shadow/metrics").status_code == 200
    
    # Contradictory review validation (V3_CORRECT + FALSE_MERGE)
    payload_bad_logic = {"review_label": "V3_CORRECT", "review_error_classification": "FALSE_MERGE"}
    resp_bad_logic = client.post(f"/api/v1/admin/entity-resolution/shadow/records/{record_id}/review", json=payload_bad_logic)
    assert resp_bad_logic.status_code == 422
    assert resp_bad_logic.status_code == 422
    
    # Valid review
    payload = {"review_label": "V3_CORRECT"}
    resp = client.post(f"/api/v1/admin/entity-resolution/shadow/records/{record_id}/review", json=payload)
    assert resp.status_code == 200
    
    # Assert review provenance
    rec = db.query(EntityResolutionRecord).filter_by(id=record_id).first()
    assert rec.review_label == "V3_CORRECT"
    assert rec.reviewed_at is not None
    assert rec.reviewed_by == "admin"
    
    # Invalid review label (enum rejection)
    bad_payload = {"review_label": "NOT_A_REAL_ENUM"}
    resp_bad = client.post(f"/api/v1/admin/entity-resolution/shadow/records/{record_id}/review", json=bad_payload)
    assert resp_bad.status_code == 422
    
    # 404
    resp_404 = client.post("/api/v1/admin/entity-resolution/shadow/records/abc-123/review", json=payload)
    assert resp_404.status_code == 404

    app.dependency_overrides.clear()
    db.close()
    engine.dispose()
    if os.path.exists("./test_metrics.db"):
        os.remove("./test_metrics.db")
        
def test_cli_report():
    import subprocess
    import sys
    from sqlalchemy import create_engine
    from app.db import Base
    import os
    
    test_db = "sqlite:///./test_cli.db"
    engine = create_engine(test_db)
    Base.metadata.create_all(engine)
    engine.dispose()
    
    env = os.environ.copy()
    env["DATABASE_URL"] = test_db
    
    result = subprocess.run([sys.executable, "app/tools/entity_resolution_shadow_report.py", "--provider", "invalid_prov"], capture_output=True, text=True, cwd=".", env=env)
    
    if os.path.exists("./test_cli.db"):
        os.remove("./test_cli.db")
        
    assert result.returncode == 0
    assert "Records: 0" in result.stdout
    assert "EXACT       0.0%" in result.stdout

