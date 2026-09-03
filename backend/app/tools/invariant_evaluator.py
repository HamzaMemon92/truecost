import logging
from typing import Any, List, Dict
import asyncio

logger = logging.getLogger(__name__)

class InvariantEvaluator:
    @staticmethod
    async def evaluate(results: List[Any], invariants: List[str], provider_name: str, query: str, test_config: Dict[str, Any] = None, observability: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if not invariants:
            return []

        evaluations = []
        
        for inv in invariants:
            eval_result = {"name": inv, "status": "FAIL", "evidence": {}}
            try:
                if inv == "results_exist":
                    if len(results) < 1:
                        raise ValueError("Expected >= 1 result, got 0.")
                    eval_result["status"] = "PASS"
                    
                elif inv == "multiple_results":
                    if len(results) < 2:
                        raise ValueError(f"Expected >= 2 results, got {len(results)}.")
                    eval_result["status"] = "PASS"
                    
                elif inv == "price_valid":
                    # All non-null prices must be >= 0
                    for idx, r in enumerate(results):
                        price = getattr(r, "price", None)
                        if price is not None and float(price) < 0:
                            raise ValueError(f"Found negative price {price} at index {idx}.")
                    eval_result["status"] = "PASS"
                    
                elif inv == "price_required":
                    # At least one result must have a valid price >= 0
                    found_price = False
                    for r in results:
                        price = getattr(r, "price", None)
                        if price is not None and float(price) >= 0:
                            found_price = True
                            break
                    if not found_price:
                        raise ValueError("No valid prices found in any results.")
                    eval_result["status"] = "PASS"
                    
                elif inv == "deeplink_valid":
                    # At least one link required, all present links must be valid
                    found_link = False
                    for idx, r in enumerate(results):
                        link = getattr(r, "url", getattr(r, "deeplink", None))
                        if link is not None:
                            found_link = True
                            if not str(link).startswith("http"):
                                raise ValueError(f"Invalid link format '{link}' at index {idx}.")
                    if not found_link:
                        raise ValueError("No deeplink found in any results.")
                    eval_result["status"] = "PASS"
                    
                elif inv in ["empty_or_unavailable", "empty_results"]:
                    if len(results) != 0:
                        raise ValueError(f"Expected 0 results, got {len(results)}.")
                    eval_result["status"] = "PASS"
                    
                elif inv == "live_provenance":
                    for idx, r in enumerate(results):
                        source = getattr(r, "source_type", None)
                        if source in ["mock", "staging", None]:
                            raise ValueError(f"CRITICAL FAIL - Invalid source_type '{source}' at index {idx}.")
                    eval_result["status"] = "PASS"
                    
                elif inv == "no_false_exact_merge":
                    status, evidence, error = await InvariantEvaluator._evaluate_no_false_exact_merge(results, query, test_config)
                    if error:
                        raise ValueError(error)
                    eval_result["status"] = status
                    eval_result["evidence"] = evidence
                    
                elif inv == "location_passed_unchanged":
                    if observability and observability.get("location_passed"):
                        eval_result["status"] = "PASS"
                    else:
                        eval_result["status"] = "SKIP"
                        eval_result["evidence"] = {"reason": "No observational evidence available"}
                        
                elif inv == "no_fabricated_location":
                    if observability and observability.get("network_calls", -1) == 0:
                        eval_result["status"] = "PASS"
                    elif observability and not observability.get("location_fabricated"):
                        eval_result["status"] = "PASS"
                    else:
                        eval_result["status"] = "SKIP"
                        eval_result["evidence"] = {"reason": "No observational evidence available"}

                else:
                    raise ValueError(f"CRITICAL FAIL: Unknown invariant '{inv}' declared.")
                    
            except Exception as e:
                eval_result["status"] = "FAIL"
                eval_result["evidence"]["error"] = str(e)
                
            evaluations.append(eval_result)
            
        return evaluations
                
    @staticmethod
    async def _evaluate_no_false_exact_merge(results: List[Any], query: str, test_config: Dict[str, Any]) -> tuple:
        if not test_config:
            return "FAIL", {}, "Missing entity_test_config in fixture"
            
        idx_a = test_config.get("candidate_a_index", 0)
        idx_b = test_config.get("candidate_b_index", 1)
        category = test_config.get("category", "General")
        
        if len(results) <= max(idx_a, idx_b):
            return "SKIP", {"reason": "INSUFFICIENT_EVIDENCE"}, None
            
        try:
            from app.services.entity_resolution import EntityResolutionService
            from app.services.entity_resolution import SourceRecord, TrueCostProduct
            
            engine = EntityResolutionService()
            
            r1 = results[idx_a]
            r2 = results[idx_b]
            
            r1_dict = r1.model_dump() if hasattr(r1, "model_dump") else r1.__dict__
            r2_dict = r2.model_dump() if hasattr(r2, "model_dump") else r2.__dict__
            
            source_rec = SourceRecord(
                product=r2_dict, observed_metadata=r2_dict,
                provider="test_harness",
                
            )
            
            res = engine.resolve(
                query=query,
                selected_product=r1_dict,
                category=category,
                source_record=source_rec,
                enable_llm_extraction=False
            )
            
            evidence = {
                "legacy_decision": getattr(res, "legacy_decision", None),
                "v3_decision": res.decision.value,
                "disagreement": getattr(res, "disagreement", False),
                "conflicts": getattr(res, "conflicts", []),
                "missing_factors": getattr(res, "missing_factors", []),
                "resolver_version": getattr(res, "resolver_version", "v3"),
                "confidence": getattr(res, "confidence", 0.0)
            }
            
            if res.decision.value == "EXACT":
                return "FAIL", evidence, "FALSE_EXACT_MERGE"
                
            return "PASS", evidence, None
                
        except Exception as e:
            return "FAIL", {"error_type": "ENTITY_RESOLUTION_ERROR"}, f"Entity Resolution threw exception: {str(e)}"




