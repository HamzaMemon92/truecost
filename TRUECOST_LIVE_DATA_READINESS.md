# TrueCost Live Data Readiness

This document outlines the system architecture and boundaries prepared to transition TrueCost from mocked test data to verified, live retailer APIs.

## 1. Supported Provider Contract
All retailer integrations must implement the `GroceryProvider` protocol. The strict boundary demands that **Raw Retailer Data** is captured by a `GroceryProviderAdapter` and immediately normalized into `CanonicalGroceryItem` schemas. The internal `calculate_effective_price` engine will govern the final presentation mathematically. Retailers may not implement custom bypass pricing.

## 2. Mock vs Live Providers
- **Mock Providers:** `MockGoldenGroceryProvider`, `MockFastGroceryProvider`, `MockCheapGroceryProvider` remain active for isolated development and CI testing.
- **Live Providers:** None currently connected. The infrastructure awaits configured, authenticated API access.

## 3. Freshness Model
Because live inventory is highly volatile, TrueCost implements explicit freshness tracking:
- `retrieved_at` timestamps are bound to every payload item.
- `DataFreshnessStatus` (`FRESH`, `STALE`, `UNKNOWN`) is evaluated at the adapter layer. Any item older than 120 minutes is marked `STALE`.

## 4. Image Trust Model
Retailer URLs (`retailer_image_url`) are supported, but inherently mistrusted for the canonical variant representation.
- A live retailer image defaults to `KNOWN_SOURCE` and will never automatically override an administratively `TRUSTED` Canonical Variant Image.
- This prevents a retailer from returning an image for a "1L Amul Milk" variant when the user asked for "500ml", silently corrupting the comparison UI.

## 5. Price & Availability Model
- **Price:** Explicitly broken down into `price`, `mrp`, `discount`, `coupon_discount`, `delivery_fee`, and `platform_fee`.
- **Availability:** Supported enums are `IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK`, `UNAVAILABLE_IN_AREA`, and `UNKNOWN`. TrueCost forces strict exclusion of any unavailable item from winning the rank.

## 6. Concurrency Model (Search)
- **Frontend Search State:** Migrated from un-cancellable `useMutation` to `useQuery` mapped directly to `query`, `objective`, and `location`. React Query automatically uses `AbortController` cancellation.
- **Manual UX:** `useQuery` is set to `enabled: false`. Search is explicitly invoked via `refetch()` when the user presses Enter, or changes refinements. This preserves the manual execution intent and prevents backend keystroke spam, while still granting React Query's staleness/abort protections.

## 7. Failure Isolation (Observability)
- **Timeouts:** Retailer integrations are wrapped by a central orchestration engine (`execute_providers_concurrently` in `grocery_registry.py`). Timeouts are configurable per provider (`timeout_ms`), defaulting to 4.5 seconds.
- **Partial Comparisons:** If 1 of 3 providers fails (`TimeoutError`, `ValueError`, etc.), TrueCost cleanly isolates the failure, successfully resolving the remaining 2 providers, and returns an `observability` payload. The frontend displays a non-intrusive warning (e.g. "Compared 2 of 3 retailers").
- **Observability:** Centralized status representations (`success`, `timeout`, `error`, `no_results`) provide frontend context without leaking API secrets or internal stack traces.

## 8. Data Freshness
- Missing timestamps natively evaluate to `UNKNOWN` for live providers, ensuring we don't accidentally bless unverified cache. Mock providers intrinsically default to `FRESH`.
- `price_checked_at`, `availability_checked_at`, and `image_checked_at` are tracked independently.

## 9. Data Ingestion & Integration Strategy (Live Assessment)
Based on the Live Data Assessment (see `TRUECOST_RETAILER_INTEGRATION_MATRIX.md`), TrueCost's integration roadmap strictly follows this ingestion hierarchy to guarantee data lawfulness and structural integrity:
1. **Authorized Partner API / ONDC Buyer Protocol** (Highest Priority)
2. **Authorized Affiliate Feeds (CSV/XML)** (Medium Priority)
3. **Verified Canonical Master Catalogs (GS1)** (For GTIN/Image mapping)

*Unauthorized DOM scraping of QuickCommerce apps (Zepto, Blinkit) is explicitly rejected for production due to legal fragility and aggressive bot mitigation.*

### Recommended First Live Integration
**BigBasket (via Affiliate/Partner Feed) OR ONDC (Buyer App Protocol).**
BigBasket's historic structured feeds offer a stable environment to battle-test the `GroceryProviderAdapter` with real GTINs, clear e-commerce imagery, and standardized units without combating hostile WAFs. Alternatively, ONDC grants authorized protocol-level access to multiple grocery sellers natively.

## 10. What Is Still Required Before Live Launch
1. **API Credentials:** Keys and authentication protocols for the chosen authorized retailer/partner (e.g., BigBasket feed access or ONDC developer sandbox).
2. **Verified Canonical Product Catalog:** A master database of GTIN/EAN barcodes mapped to definitive high-resolution imagery for core grocery items, overriding volatile `KNOWN_SOURCE` retailer images.
3. **Backend Rate-Limiting:** Intermediate caching layers (e.g., Redis) or connection pooling to handle partner API thresholds.
