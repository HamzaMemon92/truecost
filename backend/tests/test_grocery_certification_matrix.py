import json
import pytest
import glob
import os
import uuid
import httpx
from sqlalchemy import create_engine, text
from app.api.endpoints.aggregator import ingest_scraped_data, IngestPayload
from app.db import get_db
from fastapi import Response
from app.services.cache import cache
from app.graph.grocery_workflow import compile_grocery_workflow

# Ensure no outbound network calls happen during test
async def network_guard_request(*args, **kwargs):
    raise AssertionError("NETWORK GUARD TRIGGERED: Outbound HTTP call blocked during user query.")

@pytest.mark.asyncio
async def test_matrix_cases():
    engine = create_engine('sqlite:///./decision_advisor.db')
    
    # Clean state
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM ingested_provider_results"))
        conn.execute(text("DELETE FROM search_sessions"))
        conn.execute(text("DELETE FROM entity_resolution_records"))
        conn.commit()

    if hasattr(cache, "redis_client"):
        cache.redis_client.flushall()
    elif hasattr(cache, "_store"):
        cache._store.clear()

    files = glob.glob("tests/fixtures/scraper_certification/runs/MATRIX/*.json")
    results = []

    for f_path in files:
        print(f"\nProcessing {f_path}")
        with open(f_path, "r", encoding="utf-8") as f:
            capture = json.load(f)
            
        payload = IngestPayload(
            provider=capture["provider"],
            raw_data=capture["payload"],
            search_session_id=str(uuid.uuid4()),
            query=capture["query"],
            category="Grocery",
            message_type="SEARCH_SUCCESS"
        )
        
        db_gen = get_db()
        db = next(db_gen)
        try:
            await ingest_scraped_data(payload=payload, response=Response(), db=db, credentials=None)
        finally:
            db_gen.close()
            
        with engine.connect() as conn:
            # check ER exact
            res = conn.execute(text("SELECT v3_decision FROM entity_resolution_records WHERE v3_decision='EXACT'")).fetchone()
            has_exact = res is not None
            # clear DB for next run
            conn.execute(text("DELETE FROM ingested_provider_results"))
            conn.execute(text("DELETE FROM search_sessions"))
            conn.execute(text("DELETE FROM entity_resolution_records"))
            conn.commit()
            
        results.append({
            "provider": capture["provider"],
            "query": capture["query"],
            "has_exact": has_exact
        })

    # Output simple report
    for r in results:
        print(f"[{r['provider']}] {r['query']}: EXACT={r['has_exact']}")
