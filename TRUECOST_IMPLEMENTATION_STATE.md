# TrueCost Implementation State

> **Architecture Note**: The North-Star architectural blueprint for this repository is formally defined in [COMMON_MASTER_ARCHITECTURE.md](./COMMON_MASTER_ARCHITECTURE.md). It outlines the exact data, intelligence, and control planes guiding future implementation.
## LAST COMPLETED WORK
- **Phase 8: ONDC Foundation Hardened**
  - **Verdict**: 🟢 ONDC Foundation Hardened (Not "Production Integrated")

  ### Capability Status Matrix
  | Capability | Status |
  | :--- | :--- |
  | RET10 Grocery domain awareness | ✅ |
  | Mock environment | ✅ |
  | Source-type protection | ✅ |
  | Staging abstraction | ✅ |
  | Preprod abstraction | ✅ |
  | Live safety lock | ✅ |
  | Canonical ONDC → Grocery boundary | ✅/verify |
  | Ed25519 signing design | ✅/verify against exact current implementation |
  | Real staging network | ⏳ |
  | Real preprod network | ⏳ |
  | BAP onboarding | ⏳ |
  | Certification/qualification | ⏳ |
  | Production registry | ⏳ |
  | Live ONDC transactions | ❌ not yet |
  | 81 backend tests | ✅ |
  | Frontend build | ✅ |

  > **ONDC Next Steps**: The transition from foundational hardening to actual staging/production is formally managed via the [TRUECOST_ONDC_ONBOARDING.md](./TRUECOST_ONDC_ONBOARDING.md) checklist.

  ### Future Common Master Architecture Frozen
  ```text
  Common Master
  │
  ├── Grocery Domain
  │   │
  │   ├── Direct Providers (Blinkit, Zepto, etc.)
  │   │
  │   └── ONDC Integration
  │       ├── Environment Adapter
  │       ├── BAP Adapter
  │       ├── RET10 Payload Mapper
  │       ├── Signature Service
  │       ├── Registry Client
  │       ├── Network Callback Handler
  │       └── ONDC → Canonical Grocery Adapter
  │
  └── Shared Platform
      ├── MCP
      ├── LangGraph
      ├── Agents
      ├── Auth
      ├── Observability
      ├── Secrets
      └── Policy
  ```
  **Critical Boundary**: `ONDC/Beckn` ↓ `ONDC Adapter` ↓ `Canonical Grocery Model` ↓ `Common Master`. ONDC payload structures will never leak throughout the application.

- **Phase 7: Live Data & Catalog Integration Assessment**

- **Phase 6: Live Data Readiness**
  - Migrated search interaction to `useQuery` with `enabled: false` to preserve the manual Enter/Search flow while enabling full React Query cache/cancellation semantics.
  - Implemented `execute_providers_concurrently` orchestration layer to wrap providers in `asyncio.wait_for` isolation.
  - Added configurable `timeout_ms` property on `GroceryProvider`.
  - Independent timestamp schemas mapping `price_checked_at`, `availability_checked_at`, and `image_checked_at`.

- **Phase 5: Production-Quality Audit**
  - Executed Adversarial QA across Search, Pricing, UI, and Concurrency.
  - Removed dangerous `mock-*` hallucination fallbacks from `mock_grocery_provider.py` which leaked into random search categories.
  - Fixed pricing math in `pricing.py` where negative sub-totals occurred when discounts exceeded base price.
  - Implemented `.2f` bankers rounding mathematically into `EffectivePriceResult` to kill float anomalies.
  - Added robust API error handling and an empty state alert fallback in `BasketDrawer` to resolve blank screens on API failure.
  - Added visual `MOCK` tags in `product-card.tsx` to transparently indicate when data originates from simulated retailers.
  - See `TRUECOST_PRODUCTION_AUDIT.md` for full breakdown.

- **Phase 4B: Exact Retailer Purchase Handoff**
  - Updated `RetailerOffer`, `CanonicalGroceryItem`, and `FulfillmentGroup` with strict deep-linking metadata (`deep_link_type` and `deep_link_url`).
  - Added exact SKU mapping into mock providers so deterministic checkout destinations match the specific product variant perfectly.
  - Built `test_deep_link_integrity.py` asserting no cross-retailer leakage and strict SKU constraints.

## NEXT HIGHEST-VALUE WORK
- **Real Retailer Integrations:** Implement the first live adapter (e.g., Blinkit or Zepto) with authenticated endpoints, translating their proprietary schema into TrueCost's hardened `CanonicalGroceryItem`.
- **Verified Product Imagery:** Replace structural icon fallbacks with a centralized database of high-resolution canonical product images mapped to exact GTINs/SKUs.
