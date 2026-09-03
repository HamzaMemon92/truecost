# TrueCost mobile implementation plan

## Reference-informed consolidation

The full image audit produced 18 route families rather than hundreds of screenshot routes: Entry, Permissions/Location, Home, Explore/Search, Grocery, Smart Cart, Shopping Detail, Comparison, Price Intelligence, Mobility, Flights, Hotels, Deals, Finance, Saved/Watchlist, Notifications/Activity, Profile/Settings and Trust/Support.

## Delivery status

1. P0 Foundation — implemented: semantic tokens, shared UI primitives, compact Orbit Rail, SecureStore auth and guest state, concurrent-safe refresh, request cache/deduplication, explicit foreground location, app error boundary and reusable system states.
2. P1 Core journey — implemented: Home, universal search, category browsing, Grocery and Shopping hubs, immutable search bridge, persisted Smart Cart editing, substitutions, product intelligence, observed-option comparison, deterministic decision explanation, price history and provider handoff.
3. P2 Category intent — implemented: Mobility, Flights, Hotels, Deals and Finance have dedicated setup routes, observed result rendering, partial/empty/error states, backend recommendation boundaries, explanation and provider handoff. Dedicated category endpoints can replace the shared cache adapter without changing screen contracts.
4. P3 Retention — implemented: advanced watch creation/editing/pause/delete, target-state filters, notification counts/category/unread filters and safe deep links, activity dashboard/event filters, authenticated comparison history with observation provenance, private collections, notes, explicit token sharing/revocation and read-only shared views.
5. P4 Personalization — implemented: full profile editing, persistent objective/delivery/category/provider/dietary preferences, notification and accessibility controls, privacy-enforced activity and location behavior, saved-address management with honest serviceability state, and safe masked payment metadata.
6. P5 Polish — implemented: consent-driven barcode/image capture with identity provenance, Help/Trust/FAQ and persisted issue reports, account/session/export/deletion controls, progressive deterministic-cart loading, reduced-motion-aware navigation/loading, 48dp interaction targets, responsive tablet content width, deep links, route repairs and web export verification.

## API boundaries

- Commerce routes back carts, saved items, price watches, activity and notifications.
- Aggregator routes remain the sole source of provider/search facts.
- P2 imports the existing typed clients in `mobile/api/mobility.ts`, `travel.ts`, and `deals.ts`; the temporary shared category adapter has been removed.
- Mobility is labeled as an estimate, Travel/Hotels require verified inventory and fail closed, and Deals use persisted observations. The mobile UI does not recalculate backend totals, savings, eligibility, ranking, or payment value.
- No UI surface asserts delivery, fees, savings, freshness, confidence, offers or provider support unless returned by an API response.
- Ten important comparison areas are represented through one extensible catalog: Grocery, Food, Pharmacy, Shopping, Mobility, Flights, Hotels, Deals, Finance and Services. A configured provider is never presented as currently available until a provider response verifies it.
- Mobile-number OTP, social login, wallet balances, order tracking, loyalty and refunds remain capability-gated until backend contracts exist.
- Capability-gated means the product does not render a fake success path: no OTP is generated locally, no finance ranking is invented, no live Travel/Mobility claim is made, and no provider destination is synthesized.
- ScraperManager.tsx and AgentSearchScreen.tsx are protected by SHA-256 regression verification.
