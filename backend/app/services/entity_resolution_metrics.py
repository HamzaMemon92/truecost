from sqlalchemy.orm import Session
from sqlalchemy import func, String, case, text
from typing import Any, Optional
from datetime import datetime, timezone, timedelta
from app.models import EntityResolutionRecord
from app.services.entity_resolution import get_contract_by_version, SHOPPING_CONTRACT, GROCERY_CONTRACT
import json

import re
def has_extractable_source_evidence(record: EntityResolutionRecord, factor: str) -> bool:
    c_name = record.candidate_entity.get("name", "").lower()
    raw_offer = str(record.provider_offer.get("raw_offer", {})).lower() if record.provider_offer else ""
    evidence_text = c_name + " " + raw_offer
    
    if factor in ("storage", "pack_size", "capacity", "ram"):
        return bool(re.search(r'\d+\s*(gb|tb|mb|kb|g|kg|ml|l|oz|lb|pcs|pack|pieces?)', evidence_text))
    
    if factor in ("color", "finish"):
        # simple check for residual text
        return len(re.sub(r'[^a-z]', '', c_name)) > 15
        
    if factor in ("model_signature", "product_signature", "variant_signature", "brand"):
        return len(evidence_text) > 15
        
    return len(evidence_text) > 10

class EntityResolutionMetricsService:
    def __init__(self, db: Session):
        self.db = db

    def get_metrics(
        self,
        provider: Optional[str] = None,
        category: Optional[str] = None,
        resolver_version: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> dict[str, Any]:
        
        # 8. METRICS SCALE BOUNDARY: low-volume analytics enforcement
        if not start_time:
            start_time = datetime.now(timezone.utc) - timedelta(days=30)
        else:
            span = (end_time or datetime.now(timezone.utc)) - start_time
            if span.days > 31:
                raise ValueError("Analysis window exceeds scale boundary of 31 days. This endpoint is for low-volume analytics.")
            
        query = self.db.query(EntityResolutionRecord)
        
        if resolver_version:
            query = query.filter(EntityResolutionRecord.resolver_version == resolver_version)
        if start_time:
            query = query.filter(EntityResolutionRecord.created_at >= start_time)
        if end_time:
            query = query.filter(EntityResolutionRecord.created_at <= end_time)

        records = query.all()

        filtered_records = []
        for r in records:
            p_offer = r.provider_offer or {}
            c_entity = r.selected_entity or {}
            rec_provider = p_offer.get("provider", "").lower() if p_offer.get("provider") else "unknown"
            rec_category = c_entity.get("category", "").lower() if c_entity.get("category") else "unknown"
            
            if provider and rec_provider != provider.lower():
                continue
            if category and rec_category != category.lower():
                continue
            
            filtered_records.append(r)

        total = len(filtered_records)

        decisions = {"EXACT": 0, "PROBABLE": 0, "RELATED": 0, "REJECTED": 0}
        disagreement_count = 0
        legacy_v3_matrix = {}
        
        # 10. Factor Record-Rate Semantics
        missing_factors_occurrences = {}
        missing_factors_records = {}
        conflicts_occurrences = {}
        conflicts_records = {}
        
        providers_stats = {}
        categories_stats = {}
        
        unknown_attrs_count = 0
        unknown_attrs_names = {}
        
        unknown_contract_version_count = 0
        unknown_contract_versions = {}
        
        llm_candidate_count = 0
        llm_candidate_factors = {}
        llm_prov_breakdown = {}
        llm_cat_breakdown = {}
        
        # 4. Explicit Denominators
        reviewed_sample_count = 0
        reviewed_v3_exact_count = 0
        reviewed_v3_probable_count = 0
        reviewed_v3_non_exact_identity_opportunities = 0
        
        v3_exact_correct_count = 0
        probable_correct_count = 0
        v3_false_merge_count = 0
        v3_false_reject_count = 0

        total_completeness_ratio = 0.0

        for r in filtered_records:
            v3_dec = (r.v3_decision or "REJECTED").upper()
            leg_dec = (r.legacy_decision or "REJECTED").upper()
            decisions[v3_dec] = decisions.get(v3_dec, 0) + 1

            if r.disagreement:
                disagreement_count += 1
            
            matrix_key = f"{leg_dec} -> {v3_dec}"
            legacy_v3_matrix[matrix_key] = legacy_v3_matrix.get(matrix_key, 0) + 1

            rec_missing_set = set()
            for mf in r.missing_factors:
                fname = mf.get("factor", "unknown") if isinstance(mf, dict) else mf
                missing_factors_occurrences[fname] = missing_factors_occurrences.get(fname, 0) + 1
                rec_missing_set.add(fname)
            for fname in rec_missing_set:
                missing_factors_records[fname] = missing_factors_records.get(fname, 0) + 1

            has_critical_conflict = False
            rec_conflict_set = set()
            for conf in r.conflicts:
                factor = conf.get("factor", "unknown")
                conflicts_occurrences[factor] = conflicts_occurrences.get(factor, 0) + 1
                rec_conflict_set.add(factor)
                if conf.get("severity") == "critical" or factor in ("model", "storage", "pack_size", "brand", "identity_numbers", "global_identifier", "model_signature", "product_signature"):
                    has_critical_conflict = True
            for factor in rec_conflict_set:
                conflicts_records[factor] = conflicts_records.get(factor, 0) + 1

            if r.unknown_attributes:
                unknown_attrs_count += 1
                for k in r.unknown_attributes.keys():
                    unknown_attrs_names[k] = unknown_attrs_names.get(k, 0) + 1

            prov = r.provider_offer.get("provider", "unknown").lower() if r.provider_offer else "unknown"
            cat = r.selected_entity.get("category", "unknown").lower() if r.selected_entity else "unknown"

            if prov not in providers_stats:
                providers_stats[prov] = {"total": 0, "EXACT": 0, "PROBABLE": 0, "RELATED": 0, "REJECTED": 0, "disagreements": 0, "records_missing": 0, "total_missing": 0, "records_conflicts": 0, "total_conflicts": 0, "cross_missing_recs": {}, "cross_conflict_recs": {}}
            providers_stats[prov]["total"] += 1
            providers_stats[prov][v3_dec] = providers_stats[prov].get(v3_dec, 0) + 1
            if r.disagreement: providers_stats[prov]["disagreements"] += 1
            if r.missing_factors:
                providers_stats[prov]["records_missing"] += 1
                providers_stats[prov]["total_missing"] += len(r.missing_factors)
                for fname in rec_missing_set:
                    providers_stats[prov]["cross_missing_recs"][fname] = providers_stats[prov]["cross_missing_recs"].get(fname, 0) + 1
            if r.conflicts:
                providers_stats[prov]["records_conflicts"] += 1
                providers_stats[prov]["total_conflicts"] += len(r.conflicts)
                for f in rec_conflict_set:
                    providers_stats[prov]["cross_conflict_recs"][f] = providers_stats[prov]["cross_conflict_recs"].get(f, 0) + 1

            if cat not in categories_stats:
                categories_stats[cat] = {"total": 0, "EXACT": 0, "PROBABLE": 0, "RELATED": 0, "REJECTED": 0, "disagreements": 0, "records_missing": 0, "total_missing": 0, "records_conflicts": 0, "total_conflicts": 0, "cross_missing_recs": {}, "cross_conflict_recs": {}}
            categories_stats[cat]["total"] += 1
            categories_stats[cat][v3_dec] = categories_stats[cat].get(v3_dec, 0) + 1
            if r.disagreement: categories_stats[cat]["disagreements"] += 1
            if r.missing_factors:
                categories_stats[cat]["records_missing"] += 1
                categories_stats[cat]["total_missing"] += len(r.missing_factors)
                for fname in rec_missing_set:
                    categories_stats[cat]["cross_missing_recs"][fname] = categories_stats[cat]["cross_missing_recs"].get(fname, 0) + 1
            if r.conflicts:
                categories_stats[cat]["records_conflicts"] += 1
                categories_stats[cat]["total_conflicts"] += len(r.conflicts)
                for f in rec_conflict_set:
                    categories_stats[cat]["cross_conflict_recs"][f] = categories_stats[cat]["cross_conflict_recs"].get(f, 0) + 1

            # 2. UNKNOWN CONTRACT VERSION MUST NOT FALL BACK
            contract = get_contract_by_version(r.resolver_version)
            if not contract:
                unknown_contract_version_count += 1
                unknown_contract_versions[r.resolver_version] = unknown_contract_versions.get(r.resolver_version, 0) + 1
                # Contract-dependent metrics unavailable
            else:
                critical_fields = set(contract.critical)
                variant_fields = set(contract.variant)
                expected_fields = critical_fields | variant_fields
                llm_eligible_fields = set(contract.llm_extractable)
    
                is_llm_candidate = False
                candidate_factors = []
                if not has_critical_conflict and len(r.missing_factors) > 0:
                    for fname in rec_missing_set:
                        if fname in expected_fields and fname in llm_eligible_fields:
                            if has_extractable_source_evidence(r, fname):
                                is_llm_candidate = True
                                candidate_factors.append(fname)
                
                if is_llm_candidate:
                    llm_candidate_count += 1
                    llm_prov_breakdown[prov] = llm_prov_breakdown.get(prov, 0) + 1
                    llm_cat_breakdown[cat] = llm_cat_breakdown.get(cat, 0) + 1
                    for cf in candidate_factors:
                        llm_candidate_factors[cf] = llm_candidate_factors.get(cf, 0) + 1
    
                sel_attrs = r.selected_entity.get("attributes", {}) if r.selected_entity else {}
                present = sum(1 for k in expected_fields if k in sel_attrs and sel_attrs[k])
                completeness = present / len(expected_fields) if expected_fields else 1.0
                total_completeness_ratio += completeness
            
            # Review Labels
            if r.review_label:
                reviewed_sample_count += 1
                
                if v3_dec == "EXACT":
                    reviewed_v3_exact_count += 1
                    if r.review_label in ("V3_CORRECT", "BOTH_CORRECT"):
                        v3_exact_correct_count += 1
                    if r.review_error_classification == "FALSE_MERGE":
                        v3_false_merge_count += 1
                
                if v3_dec == "PROBABLE":
                    reviewed_v3_probable_count += 1
                    if r.review_label in ("V3_CORRECT", "BOTH_CORRECT"):
                        probable_correct_count += 1
                        
                if v3_dec != "EXACT":
                    reviewed_v3_non_exact_identity_opportunities += 1
                    if r.review_error_classification == "FALSE_REJECT":
                        v3_false_reject_count += 1

        def to_rate(count, total_amt):
            return round(count / total_amt, 4) if total_amt > 0 else 0.0

        metrics = {
            "total_resolutions": total,
            "decision_distribution": decisions,
            "decision_percentages": {k: to_rate(v, total) for k, v in decisions.items()},
            "legacy_v3_disagreement": {
                "disagreement_count": disagreement_count,
                "disagreement_rate": to_rate(disagreement_count, total)
            },
            "disagreement_matrix": legacy_v3_matrix,
            "missing_factors": [{"factor": k, "record_count": v, "record_rate": to_rate(v, total), "occurrence_count": missing_factors_occurrences[k]} for k, v in sorted(missing_factors_records.items(), key=lambda item: item[1], reverse=True)],
            "conflicts": [{"factor": k, "record_count": v, "record_rate": to_rate(v, total), "occurrence_count": conflicts_occurrences[k]} for k, v in sorted(conflicts_records.items(), key=lambda item: item[1], reverse=True)],
            "unknown_attribute_analysis": {
                "records_with_unknown_attributes": unknown_attrs_count,
                "unknown_attribute_rate": to_rate(unknown_attrs_count, total),
                "aggregated_names": [{"attribute": k, "count": v} for k,v in unknown_attrs_names.items()]
            },
            "unknown_contract_status": {
                "unknown_contract_version_count": unknown_contract_version_count,
                "unknown_contract_versions": unknown_contract_versions
            },
            "identity_completeness": {
                "average_identity_completeness": to_rate(total_completeness_ratio, total - unknown_contract_version_count) if (total - unknown_contract_version_count) > 0 else None
            },
            "llm_opportunity_report": {
                "llm_candidate_count": llm_candidate_count,
                "llm_candidate_rate": to_rate(llm_candidate_count, total),
                "potential_llm_calls_per_1000_resolutions": round((llm_candidate_count / total) * 1000, 1) if total > 0 else 0.0,
                "top_llm_candidate_factors": [{"factor": k, "count": v, "rate": to_rate(v, llm_candidate_count)} for k, v in sorted(llm_candidate_factors.items(), key=lambda i: i[1], reverse=True)],
                "provider_llm_candidate_breakdown": [{"provider": k, "candidate_count": v, "candidate_rate_within_provider": to_rate(v, providers_stats[k]["total"]) if k in providers_stats else 0.0, "candidate_share_of_llm_pool": to_rate(v, llm_candidate_count)} for k, v in sorted(llm_prov_breakdown.items(), key=lambda i: i[1], reverse=True)],
                "category_llm_candidate_breakdown": [{"category": k, "candidate_count": v, "candidate_rate_within_category": to_rate(v, categories_stats[k]["total"]) if k in categories_stats else 0.0, "candidate_share_of_llm_pool": to_rate(v, llm_candidate_count)} for k, v in sorted(llm_cat_breakdown.items(), key=lambda i: i[1], reverse=True)]
            }
        }
        
        # 5. Review Sample Bias / Quality Denominators
        metrics["reviewed_quality"] = {
            "reviewed_sample_count": reviewed_sample_count,
            "reviewed_v3_exact_count": reviewed_v3_exact_count,
            "v3_exact_precision": to_rate(v3_exact_correct_count, reviewed_v3_exact_count) if reviewed_v3_exact_count > 0 else None,
            "v3_false_merge_count": v3_false_merge_count if reviewed_sample_count > 0 else None,
            "reviewed_sample_false_merge_rate": to_rate(v3_false_merge_count, reviewed_v3_exact_count) if reviewed_v3_exact_count > 0 else None,
            
            "reviewed_v3_probable_count": reviewed_v3_probable_count,
            "probable_precision": to_rate(probable_correct_count, reviewed_v3_probable_count) if reviewed_v3_probable_count > 0 else None,
            
            "reviewed_v3_non_exact_identity_opportunities": reviewed_v3_non_exact_identity_opportunities,
            "v3_false_reject_count": v3_false_reject_count if reviewed_sample_count > 0 else None,
            "v3_false_reject_rate": to_rate(v3_false_reject_count, reviewed_v3_non_exact_identity_opportunities) if reviewed_v3_non_exact_identity_opportunities > 0 else None,
        }

        prov_list = []
        for p, stats in providers_stats.items():
            ptot = stats["total"]
            prov_list.append({
                "provider": p,
                "resolution_count": ptot,
                "exact_rate": to_rate(stats["EXACT"], ptot),
                "probable_rate": to_rate(stats["PROBABLE"], ptot),
                "related_rate": to_rate(stats["RELATED"], ptot),
                "rejected_rate": to_rate(stats["REJECTED"], ptot),
                "disagreement_rate": to_rate(stats["disagreements"], ptot),
                "records_with_missing_factors": stats["records_missing"],
                "records_with_missing_factors_rate": to_rate(stats["records_missing"], ptot),
                "avg_missing_factors_per_resolution": to_rate(stats["total_missing"], ptot),
                "records_with_conflicts": stats["records_conflicts"],
                "records_with_conflicts_rate": to_rate(stats["records_conflicts"], ptot),
                "avg_conflicts_per_resolution": to_rate(stats["total_conflicts"], ptot),
                "cross_breakdowns": {
                    "missing": [{"factor": k, "record_count": v, "record_rate": to_rate(v, ptot)} for k, v in stats["cross_missing_recs"].items()],
                    "conflicts": [{"factor": k, "record_count": v, "record_rate": to_rate(v, ptot)} for k, v in stats["cross_conflict_recs"].items()]
                }
            })
        metrics["providers"] = prov_list

        cat_list = []
        for c, stats in categories_stats.items():
            ctot = stats["total"]
            cat_list.append({
                "category": c,
                "resolution_count": ctot,
                "exact_rate": to_rate(stats["EXACT"], ctot),
                "probable_rate": to_rate(stats["PROBABLE"], ctot),
                "related_rate": to_rate(stats["RELATED"], ctot),
                "rejected_rate": to_rate(stats["REJECTED"], ctot),
                "disagreement_rate": to_rate(stats["disagreements"], ctot),
                "records_with_missing_factors": stats["records_missing"],
                "records_with_missing_factors_rate": to_rate(stats["records_missing"], ctot),
                "avg_missing_factors_per_resolution": to_rate(stats["total_missing"], ctot),
                "records_with_conflicts": stats["records_conflicts"],
                "records_with_conflicts_rate": to_rate(stats["records_conflicts"], ctot),
                "avg_conflicts_per_resolution": to_rate(stats["total_conflicts"], ctot),
                "cross_breakdowns": {
                    "missing": [{"factor": k, "record_count": v, "record_rate": to_rate(v, ctot)} for k, v in stats["cross_missing_recs"].items()],
                    "conflicts": [{"factor": k, "record_count": v, "record_rate": to_rate(v, ctot)} for k, v in stats["cross_conflict_recs"].items()]
                }
            })
        metrics["categories"] = cat_list

        return metrics

    def get_records(
        self,
        provider: Optional[str] = None,
        category: Optional[str] = None,
        legacy_decision: Optional[str] = None,
        v3_decision: Optional[str] = None,
        missing_factor: Optional[str] = None,
        conflict_factor: Optional[str] = None,
        resolver_version: Optional[str] = None,
        disagreement_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        # 11. Pagination Fix
        limit = min(max(1, limit), 100)
        offset = max(0, offset)
        
        query = self.db.query(EntityResolutionRecord)
        if disagreement_only:
            query = query.filter(EntityResolutionRecord.disagreement == True)
        
        if resolver_version:
            query = query.filter(EntityResolutionRecord.resolver_version == resolver_version)
        if legacy_decision:
            query = query.filter(func.lower(EntityResolutionRecord.legacy_decision) == legacy_decision.lower())
        if v3_decision:
            query = query.filter(func.lower(EntityResolutionRecord.v3_decision) == v3_decision.lower())
            
        filtered = []
        batch_size = 500
        current_db_offset = 0
        collected_count = 0
        
        while len(filtered) < limit:
            records = query.offset(current_db_offset).limit(batch_size).all()
            if not records:
                break
                
            current_db_offset += batch_size
            
            for r in records:
                p_offer = r.provider_offer or {}
                c_entity = r.selected_entity or {}
                rec_provider = p_offer.get("provider", "").lower() if p_offer.get("provider") else "unknown"
                rec_category = c_entity.get("category", "").lower() if c_entity.get("category") else "unknown"
    
                if provider and rec_provider != provider.lower():
                    continue
                if category and rec_category != category.lower():
                    continue
                
                if missing_factor:
                    found_mf = False
                    for mf in r.missing_factors:
                        fname = mf.get("factor", "") if isinstance(mf, dict) else mf
                        if fname == missing_factor:
                            found_mf = True
                            break
                    if not found_mf:
                        continue
                        
                if conflict_factor and not any(c.get("factor") == conflict_factor for c in r.conflicts):
                    continue
                    
                collected_count += 1
                if collected_count > offset:
                    filtered.append(r)
                
                if len(filtered) >= limit:
                    break
            
        results = []
        for r in filtered:
            results.append({
                "id": r.id,
                "selected_entity": r.selected_entity,
                "candidate_entity": r.candidate_entity,
                "provider": r.provider_offer.get("provider") if r.provider_offer else None,
                "legacy_decision": r.legacy_decision,
                "v3_decision": r.v3_decision,
                "evidence": r.evidence,
                "conflicts": r.conflicts,
                "missing_factors": r.missing_factors,
                "resolver_version": r.resolver_version,
                "confidence_inputs": r.confidence_inputs,
                "review_label": r.review_label,
                "review_error_classification": r.review_error_classification,
                "review_notes": r.review_notes,
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                "reviewed_by": r.reviewed_by
            })
            
        return results
        
    def add_review(self, record_id: str, label: str, error_class: Optional[str] = None, notes: Optional[str] = None, admin_id: Optional[str] = None):
        rec = self.db.query(EntityResolutionRecord).filter(EntityResolutionRecord.id == record_id).first()
        if not rec:
            return False
            
        # 1. ENFORCE REVIEW SEMANTIC CONSISTENCY
        v3_dec = (rec.v3_decision or "REJECTED").upper()
        
        if label in ("V3_CORRECT", "BOTH_CORRECT"):
            if error_class in ("FALSE_MERGE", "FALSE_REJECT", "WRONG_PROBABLE", "WRONG_RELATED"):
                raise ValueError("Contradictory label and error classification.")
        
        if error_class == "FALSE_MERGE":
            if v3_dec != "EXACT":
                raise ValueError("FALSE_MERGE requires v3_decision EXACT.")
            if label in ("V3_CORRECT", "BOTH_CORRECT"):
                raise ValueError("FALSE_MERGE contradicts correct label.")
                
        if error_class == "FALSE_REJECT":
            if v3_dec == "EXACT":
                raise ValueError("FALSE_REJECT requires v3_decision non-EXACT.")
            if label in ("V3_CORRECT", "BOTH_CORRECT"):
                raise ValueError("FALSE_REJECT contradicts correct label.")
                
        if error_class == "WRONG_PROBABLE" and v3_dec != "PROBABLE":
            raise ValueError("WRONG_PROBABLE requires v3_decision PROBABLE.")
            
        if error_class == "WRONG_RELATED" and v3_dec != "RELATED":
            raise ValueError("WRONG_RELATED requires v3_decision RELATED.")
            
        rec.review_label = label
        rec.review_error_classification = error_class
        rec.review_notes = notes
        rec.reviewed_at = datetime.now(timezone.utc)
        rec.reviewed_by = admin_id
        self.db.commit()
        return True
