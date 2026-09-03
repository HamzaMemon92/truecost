import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.providers.grocery_registry import get_grocery_providers
from app.providers.registry import get_providers as get_shopping_providers
from app.schemas.grocery import Location
from app.tools.invariant_evaluator import InvariantEvaluator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "../../tests/fixtures/live_provider_certification_cases.json")

def load_cases():
    if not os.path.exists(FIXTURE_PATH):
        logger.error(f"Fixtures not found at {FIXTURE_PATH}")
        return []
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

async def run_certification_for_provider(provider, cases, domain):
    provider_name = provider.__class__.__name__
    if "Mock" in provider_name:
        return None

    if not provider.is_enabled():
        return {
            "provider": provider_name,
            "environment": "live",
            "cases_total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": len(cases),
            "latency_p50_ms": 0,
            "latency_p95_ms": 0,
            "status": "NOT_CONFIGURED",
            "case_details": []
        }

    logger.info(f"\nEvaluating Provider: {provider_name} (Domain: {domain})")
    logger.info("=" * 50)
    
    total_applicable_cases = 0
    passed = 0
    failed = 0
    skipped = 0
    critical_failures = 0
    latencies = []
    
    case_results = []
    
    
    for case in cases:
        if domain not in case.get("domains", []):
            continue
            
        total_applicable_cases += 1
        query = case.get("query", "")
        test_case_id = case.get("test_case_id")
        severity = case.get("severity", "OPTIONAL")
        
        # Determine location
        location_strategy = case.get("location_strategy", "valid_explicit")
        location = None
        if location_strategy == "valid_explicit":
            lat = os.environ.get("TRUECOST_CERT_LOCATION_1_LAT")
            lon = os.environ.get("TRUECOST_CERT_LOCATION_1_LON")
            if lat and lon:
                location = Location(latitude=float(lat), longitude=float(lon))
        elif location_strategy == "alternate_valid":
            lat = os.environ.get("TRUECOST_CERT_LOCATION_2_LAT")
            lon = os.environ.get("TRUECOST_CERT_LOCATION_2_LON")
            if lat and lon:
                location = Location(latitude=float(lat), longitude=float(lon))
                
        if location_strategy in ["valid_explicit", "alternate_valid"] and not location:
            logger.warning(f"[SKIP] {test_case_id:<25} (Reason: Env location missing)")
            skipped += 1
            case_results.append({"id": test_case_id, "status": "SKIP", "reason": "Location env missing", "severity": severity})
            continue
            
        start_time = time.time()
        try:
            results = await provider.search(query, location=location)
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)
            
            
            # Evaluate Invariants
            evaluations = await InvariantEvaluator.evaluate(
                results=results, 
                invariants=case.get("expected_invariants", []), 
                provider_name=provider_name, 
                query=query,
                test_config=case.get("entity_test_config"),
                observability=None
            )
            
            failures = [ev for ev in evaluations if ev["status"] == "FAIL"]
            skips = [ev for ev in evaluations if ev["status"] == "SKIP"]
            
            if failures:
                logger.error(f"[FAIL] {test_case_id:<25} (Invariants Failed: {[f['name'] for f in failures]})")
                failed += 1
                if severity == "CRITICAL":
                    critical_failures += 1
                case_results.append({"id": test_case_id, "status": "FAIL", "severity": severity, "evaluations": evaluations})
            elif skips and severity == "CRITICAL":
                logger.warning(f"[SKIP] {test_case_id:<25} (CRITICAL invariant skipped)")
                skipped += 1
                case_results.append({"id": test_case_id, "status": "SKIP", "severity": severity, "evaluations": evaluations})
            else:
                logger.info(f"[PASS] {test_case_id:<25} (Query: '{query}', Results: {len(results)}, {latency:.0f}ms)")
                passed += 1
                case_results.append({"id": test_case_id, "status": "PASS", "latency_ms": latency, "results_count": len(results), "evaluations": evaluations})
            
        except Exception as e:
            err_str = str(e)
            if "401" in err_str or "403" in err_str: err_str = "AUTH_FAILURE"
            elif "402" in err_str: err_str = "CREDITS_EXHAUSTED"
            elif "429" in err_str: err_str = "RATE_LIMITED"
            elif "timeout" in err_str.lower(): err_str = "TIMEOUT"
            
            logger.error(f"[FAIL] {test_case_id:<25} (Error: {err_str})")
            failed += 1
            if severity == "CRITICAL":
                critical_failures += 1
            case_results.append({"id": test_case_id, "status": "FAIL", "error": err_str, "severity": severity})

    grade = "UNAVAILABLE"
    if total_applicable_cases > 0:
        if critical_failures > 0 or total_applicable_cases < 10:
            grade = "BLOCKED"
        elif failed > 0 or skipped > 0:
            grade = "PARTIAL"
        elif passed == total_applicable_cases:
            grade = "CERTIFIED"
        else:
            grade = "PARTIAL"
    else:
        grade = "NOT_CONFIGURED"
        
    latencies.sort()
    p50 = latencies[len(latencies)//2] if latencies else 0
    p95 = latencies[int(len(latencies)*0.95)] if latencies else 0
        
    report = {
        "provider": provider_name,
        "environment": "live",
        "cases_total": total_applicable_cases,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "critical_failures": critical_failures,
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
        "status": grade,
        "case_details": case_results
    }
    
        
    return report

async def main():
    if os.environ.get("TRUECOST_LIVE_PROVIDER_TESTS", "").lower() != "true":
        print("LIVE_PROVIDER_TESTS_DISABLED")
        sys.exit(0)

    import argparse
    parser = argparse.ArgumentParser(description="TrueCost Provider Live Certification")
    parser.add_argument("--provider", type=str, help="Specific provider to test")
    parser.add_argument("--force-live-tests", action="store_true", help="Explicit intent")
    args = parser.parse_args()

    cases = load_cases()
    if not cases:
        return

    # In a real environment we pull dynamically, but we instantiate explicitly here to get the full list for reporting
    from app.providers.flipkart_grocery_provider import FlipkartGroceryProvider
    
    grocery_providers = get_grocery_providers()
    
    if not any(isinstance(p, FlipkartGroceryProvider) for p in grocery_providers):
        grocery_providers.append(FlipkartGroceryProvider())
        
    shopping_providers = get_shopping_providers()

    all_reports = []
    
    print("\nTRUECOST LIVE PROVIDER CERTIFICATION")
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)
    
    for provider in grocery_providers:
        if args.provider and args.provider.lower() not in provider.__class__.__name__.lower():
            continue
        report = await run_certification_for_provider(provider, cases, "grocery")
        if report:
            all_reports.append(report)
            
    for provider in shopping_providers:
        if args.provider and args.provider.lower() not in provider.__class__.__name__.lower():
            continue
        report = await run_certification_for_provider(provider, cases, "shopping")
        if report:
            all_reports.append(report)
            
    print("\n" + "=" * 60)
    print("FINAL SUMMARY REPORT")
    print("=" * 60)
    
    for r in all_reports:
        print(f"Provider: {r['provider']}")
        print(f"Status:   {r['status']}")
        print(f"Cases:    {r.get('passed', 0)} PASS | {r.get('failed', 0)} FAIL | {r.get('skipped', 0)} SKIP | {r.get('critical_failures', 0)} CRITICAL FAILS")
        print(f"Latency:  {r.get('latency_p50_ms', 0):.0f}ms (p50) | {r.get('latency_p95_ms', 0):.0f}ms (p95)")
        print("-" * 60)
        
    print("\nNO purchases executed. NO LLM calls made. ENTITY_RESOLUTION_MODE=shadow.")
    
    output_file = "live_certification_report.json"
    with open(output_file, "w") as f:
        json.dump(all_reports, f, indent=2)
    print(f"\nDetailed JSON report saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())

