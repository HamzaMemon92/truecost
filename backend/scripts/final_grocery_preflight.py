from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.api.endpoints.aggregator import connectors, normalize_provider_key
from app.config import settings
from app.db import Base, SessionLocal, get_db
from app.main import app
from app.models import DecisionAuditTrail, EntityResolutionRecord, IngestedProviderResult, SearchSession

GROCERY_PROVIDERS = ["blinkit", "zepto", "bigbasket", "swiggy"]
FIXTURE_DIR = BACKEND / "tests" / "fixtures" / "scraper_certification" / "runs" / "MATRIX"
ARTIFACT = ROOT / "artifacts" / "final_grocery_preflight_report.json"
DB_SESSION_FACTORY = SessionLocal

TEST_CASES = [
    ("Amul Gold Milk 500ml", "variant"),
    ("Coca-Cola Original Taste 750 ml", "beverage"),
    ("Maggi 2-Minute Instant Noodles 70g", "snack"),
    ("Surf Excel Easy Wash Detergent Powder 1 kg", "home"),
    ("Amul Taaza Toned Fresh Milk", "dairy"),
    ("Tata Salt 1 kg", "quantity"),
    ("Aashirvaad Superior MP Sharbati Atta 5 kg", "staple"),
    ("Dairy Milk", "common_dairymilk"),
    ("Oreo", "common_oreo"),
    ("Thums Up", "common_thumsup"),
]


def provider_fixture(provider: str, case_id: str) -> Path | None:
    direct = FIXTURE_DIR / f"{provider}_{case_id}.json"
    if direct.exists():
        return direct
    candidates = sorted(FIXTURE_DIR.glob(f"{provider}_{case_id}*.json"))
    return candidates[0] if candidates else None


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def looks_product_like(value: dict[str, Any]) -> bool:
    keys = {str(key).lower() for key in value.keys()}
    if "productresponse" in keys:
        return True
    if "product" in keys and ("productvariant" in keys or "sellingprice" in keys or "mrp" in keys):
        return True
    has_name = bool(keys & {"name", "title", "desc", "product_name", "productname", "display_name", "displayname"})
    has_price = bool(keys & {"price", "sp", "mrp", "pricing", "sellingprice", "selling_price", "offer_price", "offerprice", "discountedsellingprice"})
    return has_name and has_price


def count_product_like(value: Any, *, limit: int = 100_000) -> int:
    seen = 0
    total = 0
    stack = [value]
    while stack and seen < limit:
        seen += 1
        node = stack.pop()
        if isinstance(node, dict):
            if looks_product_like(node):
                total += 1
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return total


def top_level_shape(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        keys = list(value.keys())
        return {
            "payload_type": "dict",
            "top_level_keys": keys[:40],
            "top_level_key_count": len(keys),
        }
    if isinstance(value, list):
        return {"payload_type": "list", "top_level_keys": [], "top_level_key_count": len(value)}
    return {"payload_type": type(value).__name__, "top_level_keys": [], "top_level_key_count": 0}


def classify_parser_empty(payload: Any, parse_error: str | None) -> tuple[str, str | None, dict[str, Any]]:
    shape = top_level_shape(payload)
    product_like_count = count_product_like(payload)
    payload_text = json.dumps(payload, ensure_ascii=False, default=str)[:120_000].casefold() if payload is not None else ""
    diagnostics = {
        **shape,
        "payload_size_chars": len(payload_text),
        "product_like_key_count": product_like_count,
        "contains_search_recall_meta": "recall_type" in payload_text or "total_results" in payload_text,
        "contains_config_markers": "config" in payload_text or "experiments" in payload_text,
        "contains_block_markers": any(marker in payload_text for marker in ("captcha", "access denied", "forbidden", "too many requests")),
    }
    if parse_error:
        return "PARSER_ERROR", parse_error, diagnostics
    if not payload_text.strip():
        return "CAPTURE_EMPTY", "CAPTURE_EMPTY", diagnostics
    if diagnostics["contains_block_markers"]:
        return "PROVIDER_ACCESS_BLOCKED", "PROVIDER_ACCESS_BLOCKED", diagnostics
    if product_like_count == 0:
        return "WRONG_RESPONSE_CAPTURED", "No product-like records found in captured payload", diagnostics
    return "PARSER_EMPTY_SCHEMA_CHANGED", "Product-like records exist but connector produced zero products", diagnostics


def normalize_products(provider: str, payload: Any) -> tuple[list[dict[str, Any]], str | None]:
    try:
        connector = connectors[normalize_provider_key(provider)]
        products = connector.parse_search_results(payload if isinstance(payload, dict) else {"items": payload})
        return [item.model_dump(by_alias=True) for item in products], None
    except Exception as exc:
        return [], f"{exc.__class__.__name__}: {exc}"


def offer_rows_from_api(api_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in (api_payload.get("discovery_report") or {}).get("canonical_offer_groups") or []:
        for offer in group.get("offers") or []:
            product = offer.get("product") or {}
            rows.append(
                {
                    "sku": group.get("title"),
                    "provider": offer.get("provider"),
                    "price": offer.get("price"),
                    "size": product.get("weightVolume") or product.get("weight_volume"),
                    "in_stock": offer.get("in_stock"),
                    "serviceable": offer.get("serviceable"),
                    "image_match_status": offer.get("image_match_status"),
                    "has_image": bool(offer.get("image_url")),
                    "has_url": bool(offer.get("product_url") or offer.get("deep_link")),
                }
            )
    return rows


def provider_positions(api_payload: dict[str, Any]) -> dict[str, dict[str, str]]:
    matrix: dict[str, dict[str, str]] = {}
    for group in (api_payload.get("discovery_report") or {}).get("canonical_offer_groups") or []:
        sku = str(group.get("title") or group.get("group_id"))
        row = matrix.setdefault(sku, {provider: "MISSING" for provider in GROCERY_PROVIDERS})
        for provider, state in (group.get("provider_status") or {}).items():
            key = normalize_provider_key(provider)
            if key in row:
                status = state.get("match_status") or state.get("state") or "unknown"
                row[key] = str(status)
        for offer in group.get("offers") or []:
            key = normalize_provider_key(str(offer.get("provider") or ""))
            if key in row:
                if offer.get("in_stock") is False:
                    row[key] = "SOLD_OUT"
                elif offer.get("serviceable") is False:
                    row[key] = "NOT_SERVICEABLE"
                else:
                    row[key] = f"PRICE={offer.get('price')}"
    return matrix


def db_counts(search_id: str) -> dict[str, Any]:
    with DB_SESSION_FACTORY() as db:
        return {
            "search_sessions": db.query(SearchSession).filter(SearchSession.id == search_id).count(),
            "ingested_provider_results": db.query(IngestedProviderResult).filter(IngestedProviderResult.search_session_id == search_id).count(),
            "decision_audits": db.query(DecisionAuditTrail).filter(DecisionAuditTrail.search_session_id == search_id).count(),
            "entity_resolution_records": db.query(EntityResolutionRecord).filter(EntityResolutionRecord.search_session_id == search_id).count(),
        }


def install_preflight_database() -> Any:
    global DB_SESSION_FACTORY

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    DB_SESSION_FACTORY = sessionmaker(bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = DB_SESSION_FACTORY()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return test_engine


def run_fixture_case(client: TestClient, query: str, case_id: str) -> dict[str, Any]:
    search_id = str(uuid.uuid4())
    provider_results: dict[str, Any] = {}
    live_available = False

    for provider in GROCERY_PROVIDERS:
        fixture_path = provider_fixture(provider, case_id)
        started = time.perf_counter()
        result = {
            "request_attempted": False,
            "execution_status": "NO_REPLAY_CAPTURE",
            "attempt_count": 0,
            "location": "fixture",
            "raw_result_count": 0,
            "parsed_result_count": 0,
            "relevant_result_count": 0,
            "exact_result_count": 0,
            "sold_out_result_count": 0,
            "duration_ms": 0,
            "error_stage": "capture",
            "error_code": "CAPTURE_MISSING",
            "sample": [],
        }

        if fixture_path:
            capture = load_json(fixture_path)
            payload = capture.get("payload")
            execution_mode = capture.get("execution_mode")
            live_available = live_available or execution_mode == "REAL_LIVE_SCRAPE"
            parsed, parse_error = normalize_products(provider, payload)
            empty_status, empty_error, empty_diagnostics = classify_parser_empty(payload, parse_error) if not parsed else (None, None, {})
            result.update(
                {
                    "request_attempted": execution_mode == "REAL_LIVE_SCRAPE",
                    "execution_status": "REPLAY_CAPTURE_PARSED" if parsed else empty_status,
                    "attempt_count": 1,
                    "location": capture.get("observed_location_evidence") or capture.get("requested_location_profile") or "fixture",
                    "raw_result_count": count_product_like(payload),
                    "parsed_result_count": len(parsed),
                    "sold_out_result_count": sum(1 for item in parsed if (item.get("prices") or [{}])[0].get("inStock") is False),
                    "error_stage": None if parsed else "parser",
                    "error_code": None if parsed else empty_error,
                    "diagnostics": empty_diagnostics,
                    "sample": [
                        {
                            "provider_product_id": item.get("id"),
                            "variant_id": item.get("providerSku") or item.get("id"),
                            "title": item.get("name"),
                            "size": item.get("weightVolume"),
                            "price": (item.get("prices") or [{}])[0].get("price"),
                            "mrp": (item.get("prices") or [{}])[0].get("originalPrice"),
                            "stock": (item.get("prices") or [{}])[0].get("inStock"),
                            "has_image": bool(item.get("imageUrl")),
                            "has_url": bool((item.get("prices") or [{}])[0].get("productUrl") or (item.get("prices") or [{}])[0].get("deepLink")),
                        }
                        for item in parsed[:8]
                    ],
                }
            )
            response = client.post(
                "/api/v1/aggregator/ingest",
                json={
                    "provider": provider,
                    "raw_data": payload,
                    "query": query,
                    "category": "Grocery",
                    "search_session_id": search_id,
                },
            )
            if response.status_code != 200:
                result["execution_status"] = "INGEST_FAILED"
                result["error_stage"] = "ingest"
                result["error_code"] = f"HTTP_{response.status_code}: {response.text[:300]}"

        result["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
        provider_results[provider] = result

    api_started = time.perf_counter()
    api_response = client.get(
        "/api/v1/aggregator/search",
        params={"q": query, "category": "Grocery", "session_id": search_id, "exact_match": "true"},
    )
    api_duration = round((time.perf_counter() - api_started) * 1000, 2)
    api_payload = api_response.json() if api_response.status_code == 200 else {"error": api_response.text[:500]}
    api_rows = offer_rows_from_api(api_payload)

    providers_in_rows = {normalize_provider_key(str(row.get("provider") or "")) for row in api_rows}
    for provider, stats in provider_results.items():
        stats["relevant_result_count"] = sum(1 for row in api_rows if normalize_provider_key(str(row.get("provider") or "")) == provider)
        stats["exact_result_count"] = stats["relevant_result_count"]
        if stats["parsed_result_count"] and provider not in providers_in_rows:
            stats["lost_after_parser"] = True

    return {
        "search_id": search_id,
        "query": query,
        "case_id": case_id,
        "location": "captured fixture location; not current live device location",
        "live_capture_available": live_available,
        "providers": provider_results,
        "api": {
            "status_code": api_response.status_code,
            "duration_ms": api_duration,
            "canonical_group_count": len((api_payload.get("discovery_report") or {}).get("canonical_offer_groups") or []),
            "offer_rows": api_rows[:40],
            "provider_positions": provider_positions(api_payload),
        },
        "database": db_counts(search_id),
    }


async def run_quickcommerce_smoke(query: str) -> dict[str, Any]:
    from app.providers.quickcommerce_provider import QuickCommerceProvider
    from app.schemas.grocery import Location

    provider = QuickCommerceProvider()
    result: dict[str, Any] = {
        "enabled": provider.is_enabled(),
        "query": query,
        "status": "NOT_CONFIGURED",
        "duration_ms": 0,
        "platform_counts": {},
        "error": None,
    }
    if not provider.is_enabled():
        result["error"] = "QUICKCOMMERCE_API_KEY is not configured"
        return result
    started = time.perf_counter()
    try:
        items = await provider.search(query, location=Location(latitude=settings.quickcommerce_lat, longitude=settings.quickcommerce_lon))
        result["status"] = "SUCCESS" if items else "ZERO_RESULTS"
        for item in items:
            result["platform_counts"][item.provider] = result["platform_counts"].get(item.provider, 0) + 1
    except Exception as exc:
        result["status"] = "ERROR"
        result["error"] = f"{exc.__class__.__name__}: {exc}"
    finally:
        result["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return result


def release_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    tooling = report["environment"].get("android_tooling") or {}
    if not tooling.get("adb_path"):
        blockers.append("Android platform-tools/adb not found locally: cannot automate Expo/mobile WebView scraper capture from this terminal.")
    elif not tooling.get("adb_devices"):
        blockers.append("ADB is installed, but no Android device/emulator is connected or authorized for automated Expo/mobile WebView capture.")
    if not tooling.get("maestro_path"):
        blockers.append("Maestro not found locally: existing mobile scraper certification runner cannot execute.")
    for case in report["fixture_replay_cases"]:
        swiggy = case["providers"].get("swiggy") or {}
        if swiggy.get("execution_status") == "NO_REPLAY_CAPTURE":
            blockers.append(f"Missing Swiggy Instamart real capture for case {case['case_id']} ({case['query']}).")
        blinkit = case["providers"].get("blinkit") or {}
        if case["case_id"] == "variant" and blinkit.get("execution_status") in {"WRONG_RESPONSE_CAPTURED", "CAPTURE_EMPTY", "PROVIDER_ACCESS_BLOCKED"}:
            blockers.append(f"Blinkit fixture for case {case['case_id']} is not a valid product search capture: {blinkit.get('execution_status')}.")
    return blockers


def command_exists(name: str) -> bool:
    from shutil import which

    return which(name) is not None


def find_local_executable(name: str, extra_candidates: list[Path] | None = None) -> str | None:
    from shutil import which

    resolved = which(name)
    if resolved:
        return resolved
    for candidate in extra_candidates or []:
        if candidate.exists():
            return str(candidate)
    return None


def android_tooling_report() -> dict[str, Any]:
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    userprofile = os.environ.get("USERPROFILE", "")
    android_home = os.environ.get("ANDROID_HOME")
    android_sdk_root = os.environ.get("ANDROID_SDK_ROOT")
    sdk_roots = [
        Path(android_home) if android_home else None,
        Path(android_sdk_root) if android_sdk_root else None,
        Path(local_appdata) / "Android" / "Sdk" if local_appdata else None,
        Path("C:/Android/Sdk"),
    ]
    sdk_roots = [path for path in sdk_roots if path is not None]
    adb_candidates = [path / "platform-tools" / "adb.exe" for path in sdk_roots]
    emulator_candidates = [path / "emulator" / "emulator.exe" for path in sdk_roots]
    adb_candidates.append(ROOT / "tools" / "android" / "platform-tools" / "adb.exe")
    emulator_candidates.append(ROOT / "tools" / "android" / "emulator" / "emulator.exe")
    maestro_candidates = [
        Path(userprofile) / ".maestro" / "bin" / "maestro.bat" if userprofile else None,
        Path(userprofile) / ".maestro" / "bin" / "maestro.exe" if userprofile else None,
    ]
    maestro_candidates = [path for path in maestro_candidates if path is not None]
    java_candidates = [
        ROOT / "tools" / "jdk21" / "bin" / "java.exe",
    ]
    java_candidates.extend((ROOT / "tools" / "microsoft-jdk21").glob("*/bin/java.exe"))
    adb_path = find_local_executable("adb", adb_candidates)
    devices: list[dict[str, str]] = []
    adb_error = None
    if adb_path:
        import subprocess

        try:
            completed = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=10, check=False)
            if completed.returncode != 0:
                adb_error = (completed.stderr or completed.stdout).strip()
            else:
                for line in completed.stdout.splitlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        devices.append({"serial": parts[0], "state": parts[1]})
        except Exception as exc:
            adb_error = f"{exc.__class__.__name__}: {exc}"
    return {
        "ANDROID_HOME": android_home,
        "ANDROID_SDK_ROOT": android_sdk_root,
        "adb_path": adb_path,
        "emulator_path": find_local_executable("emulator", emulator_candidates),
        "maestro_path": find_local_executable("maestro", maestro_candidates),
        "java_path": find_local_executable("java", java_candidates),
        "adb_devices": devices,
        "adb_error": adb_error,
        "checked_sdk_roots": [str(path) for path in sdk_roots],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="TrueCost final grocery pre-test verification harness")
    parser.add_argument("--quick", action="store_true", help="Only run a short preflight")
    args = parser.parse_args()

    test_engine = install_preflight_database()
    client = TestClient(app)
    cases = TEST_CASES[:1] if args.quick else TEST_CASES
    tooling_report = android_tooling_report()
    report: dict[str, Any] = {
        "status": "RUNNING",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": {
            "backend_framework": "FastAPI",
            "database_url": settings.database_url,
            "redis_url": settings.redis_url,
            "quickcommerce_enabled": bool(settings.quickcommerce_api_key),
            "adb_available": bool(tooling_report.get("adb_path")),
            "maestro_available": bool(tooling_report.get("maestro_path")),
            "quickcommerce_role": "optional backend external API path; mobile WebView provider data uses /api/v1/aggregator/ingest",
            "android_tooling": tooling_report,
            "fixture_dir": str(FIXTURE_DIR),
        },
        "search_endpoint": "/api/v1/aggregator/search",
        "ingest_endpoint": "/api/v1/aggregator/ingest",
        "live_provider_smoke": None,
        "fixture_replay_cases": [],
        "thirty_run": {"status": "NOT_RUN", "reason": "requires live provider execution, not replay"},
    }

    try:
        import asyncio

        report["live_provider_smoke"] = asyncio.run(run_quickcommerce_smoke("Amul Gold Milk"))
        for query, case_id in cases:
            report["fixture_replay_cases"].append(run_fixture_case(client, query, case_id))

        blockers = release_blockers(report)
        report["blockers"] = blockers
        report["status"] = "BLOCKED_NOT_READY_FOR_USER_TEST" if blockers else "PASSED"

        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        print("=" * 72)
        print("TRUECOST FINAL GROCERY PREFLIGHT")
        print("=" * 72)
        print(f"STATUS: {report['status']}")
        print(f"REPORT: {ARTIFACT}")
        print()
        print("ENVIRONMENT")
        for key, value in report["environment"].items():
            print(f"  {key}: {value}")
        print()
        print("LIVE PROVIDER SMOKE")
        print(json.dumps(report["live_provider_smoke"], indent=2, ensure_ascii=False))
        print()
        for case in report["fixture_replay_cases"]:
            print(f"QUERY: {case['query']}  SEARCH_ID: {case['search_id']}")
            print("Provider        Attempted  Raw  Parsed  Relevant  Exact  SoldOut  Status")
            for provider in GROCERY_PROVIDERS:
                stats = case["providers"][provider]
                print(
                    f"{provider:<15} {str(stats['request_attempted']):<9} "
                    f"{stats['raw_result_count']:<4} {stats['parsed_result_count']:<7} "
                    f"{stats['relevant_result_count']:<9} {stats['exact_result_count']:<6} "
                    f"{stats['sold_out_result_count']:<8} {stats['execution_status']}"
                )
            print(f"API groups: {case['api']['canonical_group_count']}  DB: {case['database']}")
            print()
        if blockers:
            print("BLOCKERS")
            for blocker in blockers:
                print(f"  - {blocker}")
        return 1 if blockers else 0
    finally:
        app.dependency_overrides.pop(get_db, None)
        test_engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
