import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.services.entity_resolution_metrics import EntityResolutionMetricsService
import sys

def main():
    parser = argparse.ArgumentParser(description="TrueCost Entity Resolution Shadow Report")
    parser.add_argument("--provider", type=str, help="Filter by provider")
    parser.add_argument("--category", type=str, help="Filter by category")
    parser.add_argument("--resolver-version", type=str, help="Filter by resolver version")
    args = parser.parse_args()

    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        service = EntityResolutionMetricsService(db)
        metrics = service.get_metrics(
            provider=args.provider,
            category=args.category,
            resolver_version=args.resolver_version
        )
        
        print("\nTRUECOST ENTITY RESOLUTION — SHADOW REPORT\n")
        print(f"Records: {metrics['total_resolutions']:,}\n")
        
        print("V3 Decisions")
        print(f"EXACT       {metrics['decision_percentages'].get('EXACT', 0)*100:.1f}%")
        print(f"PROBABLE    {metrics['decision_percentages'].get('PROBABLE', 0)*100:.1f}%")
        print(f"RELATED     {metrics['decision_percentages'].get('RELATED', 0)*100:.1f}%")
        print(f"REJECTED    {metrics['decision_percentages'].get('REJECTED', 0)*100:.1f}%\n")
        
        print(f"Legacy/V3 disagreement: {metrics['legacy_v3_disagreement']['disagreement_rate']*100:.1f}%\n")
        
        print("Top Missing Factors")
        for factor in metrics['missing_factors'][:5]:
            print(f"{factor['factor']:<15} {factor['record_rate']*100:.1f}% (Total occurrences: {factor['occurrence_count']})")
        print()
        
        print("Top Conflicts")
        for conf in metrics['conflicts'][:5]:
            print(f"{conf['factor']:<15} {conf['record_rate']*100:.1f}% (Total occurrences: {conf['occurrence_count']})")
        print()
        
        if metrics.get('providers'):
            worst = max(metrics['providers'], key=lambda p: p['records_with_missing_factors_rate'])
            print("Worst Provider by Missing Metadata")
            print(f"{worst['provider']:<15} {worst['records_with_missing_factors_rate']*100:.1f}%\n")
            
        print("LLM Opportunity")
        llm = metrics.get('llm_opportunity_report', {})
        print(f"Candidate count: {llm.get('llm_candidate_count', 0)}")
        print(f"Candidate rate:  {llm.get('llm_candidate_rate', 0.0)*100:.1f}%")
        print(f"Projected calls / 1k: {llm.get('potential_llm_calls_per_1000_resolutions', 0.0)}")
        if llm.get('top_llm_candidate_factors'):
            print("  Top Candidate Factors:")
            for cf in llm['top_llm_candidate_factors'][:3]:
                print(f"  - {cf['factor']}: {cf['count']} ({cf['rate']*100:.1f}%)")
        print()
        
        rq = metrics.get('reviewed_quality', {})
        if rq and rq.get('reviewed_sample_count', 0) > 0:
            print("Quality (Reviewed Sample)")
            print(f"Reviewed Count: {rq['reviewed_sample_count']}")
            print(f"Reviewed V3 EXACT Count: {rq['reviewed_v3_exact_count']}")
            print(f"Reviewed V3 PROBABLE Count: {rq['reviewed_v3_probable_count']}")
            print(f"V3 Exact Precision: {rq['v3_exact_precision']*100:.1f}%" if rq.get('v3_exact_precision') is not None else "V3 Exact Precision: N/A")
            print(f"Reviewed Sample False Merge Rate: {rq['reviewed_sample_false_merge_rate']*100:.1f}%" if rq.get('reviewed_sample_false_merge_rate') is not None else "Reviewed Sample False Merge Rate: N/A")
        else:
            print("Quality: No reviewed samples available.")
        
    finally:
        db.close()

if __name__ == '__main__':
    main()
