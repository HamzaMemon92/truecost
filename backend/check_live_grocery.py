"""
Phase 2D Live Diagnostic
Runs the full QuickCommerce fan-out across Blinkit, Zepto, Swiggy Instamart
for a real grocery basket and prints a structured accuracy report.
"""
import asyncio
import json
import os
import sys
from datetime import datetime

# Ensure backend app is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env before importing app
from dotenv import load_dotenv
load_dotenv()

from app.providers.quickcommerce_provider import QuickCommerceProvider
from app.providers.grocery_base import normalize_grocery_results
from app.graph.grocery_basket_engine import BasketBuilder, CostCalculator, ConstraintEngine, BasketOptimizer

ITEMS_TO_TEST = [
    "milk",
    "eggs",
    "bread",
    "butter",
    "rice",
]

SEP = "─" * 72


def fmt_inr(v: float) -> str:
    return f"₹{v:.2f}"


async def run_diagnostic():
    provider = QuickCommerceProvider()

    if not provider.is_enabled():
        print("❌ QUICKCOMMERCE_API_KEY not set. Copy .env.example to .env first.")
        return

    print(f"\n{'═'*72}")
    print("  DECISION ADVISOR — Phase 2D Live Diagnostic")
    print(f"  Key: ...{provider.name}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═'*72}\n")

    all_canonical = []

    for query in ITEMS_TO_TEST:
        print(f"🔍 Searching: '{query}'")
        try:
            raw_results = await provider.search(query)
            canonical = normalize_grocery_results(provider, raw_results)

            print(f"   ✅ {len(canonical)} items returned across Blinkit/Zepto/Swiggy")

            by_platform: dict[str, list] = {}
            for item in canonical:
                by_platform.setdefault(item.provider, []).append(item)

            for platform, items in sorted(by_platform.items()):
                best = min(items, key=lambda x: x.price)
                print(f"   [{platform:20}] {len(items):2d} results | cheapest: {best.title[:40]:<40} {fmt_inr(best.price)}"
                      f" | {best.delivery_minutes or '?'} min")

            all_canonical.extend(canonical)
        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()

    print(SEP)
    print("🧺 BUILDING BASKETS from all results...")
    print(SEP)

    # Build full basket across all items
    baskets = BasketBuilder.build(all_canonical)
    baskets = CostCalculator.calculate_all(baskets)
    baskets = ConstraintEngine.evaluate_all(baskets, ITEMS_TO_TEST)

    print(f"\n{'Provider':<25} {'Items':>5} {'Subtotal':>10} {'Delivery':>10} {'Total':>10} {'Missing':>8} {'ETA':<12}")
    print("─" * 85)
    for b in sorted(baskets, key=lambda x: x.final_total):
        missing_str = str(len(b.missing_items)) if b.missing_items else "none"
        print(
            f"{b.provider:<25} "
            f"{len(b.items):>5} "
            f"{fmt_inr(b.subtotal):>10} "
            f"{fmt_inr(b.delivery_fee):>10} "
            f"{fmt_inr(b.final_total):>10} "
            f"{missing_str:>8} "
            f"{b.estimated_delivery or '?':<12}"
        )

    print()
    for objective in ["cheapest", "fastest", "balanced"]:
        ranked = BasketOptimizer.optimize(baskets, objective)
        if ranked:
            winner = ranked[0]
            print(f"🏆 [{objective:8}] → {winner.provider:<25} {fmt_inr(winner.final_total):>10} | ETA: {winner.estimated_delivery or '?'}")

    print(f"\n{'═'*72}")
    print("  ACCURACY SUMMARY")
    print(f"{'═'*72}")
    total = len(all_canonical)
    with_image = sum(1 for i in all_canonical if i.source_url and i.source_url != "https://example.com")
    with_eta = sum(1 for i in all_canonical if i.delivery_minutes is not None)
    in_stock = sum(1 for i in all_canonical if i.availability == "In Stock")
    live_items = sum(1 for i in all_canonical if i.source_type == "live")
    confidence_avg = (sum(i.confidence for i in all_canonical) / total) if total else 0

    print(f"  Total items fetched  : {total}")
    print(f"  Live source          : {live_items}/{total}")
    print(f"  In stock             : {in_stock}/{total}")
    print(f"  With delivery ETA    : {with_eta}/{total}")
    print(f"  With deeplink        : {with_image}/{total}")
    print(f"  Avg confidence       : {confidence_avg:.2%}")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    asyncio.run(run_diagnostic())
