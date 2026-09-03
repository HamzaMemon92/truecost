# TrueCost mobile integration map

| Screen | Route | Component | API / state | Backend / database |
| --- | --- | --- | --- | --- |
| Welcome / guest | Welcome | WelcomeScreen | AuthContext.continueAsGuest | Device-only guest flag in SecureStore |
| Sign in / register | Auth | AuthScreen | Email/password, refresh-safe session | /api/v1/auth/login, /register, /refresh; users, refresh_tokens |
| Location setup | pre-shell gate | LocationGate, LocationContext | Explicit foreground permission or user-entered area; encrypted device persistence only after opt-in | Expo Location/geocoding; coordinates passed only to relevant search intent |
| Home dashboard | MainTabs/Home | FoundationHome | Cached dashboard query and active location | /commerce/dashboard/summary; carts, saved items, watches, activity |
| Category hub | MainTabs/Explore | ExploreHub | Category routes and in-session search history | Local intent state; no fabricated trend data |
| Universal search | MainTabs/Compare | ExploreHub | Debounced observed-product suggestions, product image/brand/provider context, local recent intent, category and location | GET `/aggregator/suggestions`; persisted sanitized `ingested_provider_results`; immutable AgentSearch bridge |
| Search engine | AgentSearch | SearchExecutionScreen → protected AgentSearchScreen | Existing proprietary search state wrapped by cache polling and a 35-second trusted-result deadline | `/aggregator/search`, `/ingest`, `/merge`, `/optimize`; no-result timeout never fabricates a product |
| Grocery home | GroceryHub | GroceryHubScreen | Current cart summary and search entry | /commerce/carts; carts, cart_items |
| Smart Cart | Cart | SmartCartScreen | Quantity mutations, delete, objective and deterministic optimization request | `/commerce/carts/*`; `carts`, `cart_items` |
| Basket optimization | CartOptimization | CartOptimizationScreen | Progressive offer-check/math states, fulfillment groups, versioned totals, single-store baseline, assumptions and destination-gated handoff | POST `/commerce/carts/{id}/optimize`, GET `/optimizations`; deployed `TrueCostOptimizer`, `cart_optimizations` |
| Substitutions | Substitutions | SubstitutionScreen | Persisted allow_substitution metadata | PATCH /commerce/carts/{cart}/items/{item} |
| Shopping home | ShoppingHub | ShoppingHubScreen | Search, saved and watch entry | Immutable search plus commerce APIs |
| Product detail | ProductDetail | ProductDetailScreen | Route product/offer payload; save/watch writes | /commerce/saved-items, /commerce/price-watches |
| Offer comparison | Comparison | ComparisonScreen | Supplied options and backend winner only | Ingested/merged result payload; no client-invented winner |
| Decision explanation | DecisionExplanation | DecisionExplanationScreen | Backend total, reason, evidence, confidence and assumptions | Deterministic decision response; LLM text never recalculates |
| Provider handoff | CheckoutHandoff | CheckoutHandoffScreen | Supplied URL/total/freshness, explicit disclosure and authenticated handoff recording | POST `/commerce/handoffs`; `user_activities`; final checkout remains external |
| Saved library | MainTabs/Saved | CommerceScreen | Saved items plus private/shared-list tabs, creation and deletion | GET/POST/PATCH/DELETE `/commerce/saved-items`, `/commerce/collections`; `saved_items`, `saved_collections` |
| Saved-list detail | SavedLists | SavedListDetailScreen | Add/remove saved items, per-item notes, explicit sharing and revocation | `/commerce/collections/{id}/*`; `saved_collection_items`, ownership checks |
| Shared-list preview | SharedList | SharedListScreen | Read-only token-scoped view with saved-observation disclosure | Public GET `/commerce/shared-lists/{token}`; no owner identity returned |
| Advanced watchlist | Watchlist | WatchlistScreen | Create/edit/pause/resume/delete alerts; active/reached/paused filters; newly ingested exact-title observations can cross a target | `/commerce/price-watches`, `/observations`; `price_watches`, `price_observations`, notification/activity writes |
| Notification center | Notifications | NotificationsScreen | Category and unread filters, unread counts, mark one/all read, allowlisted route deep links | `/commerce/notifications`, `/stats`, `/mark-all-read`; `notifications` |
| Activity dashboard | Activity | ActivityScreen | Event-group filters, activity metrics and recent comparisons | `/commerce/activity`, `/activity/summary`; `user_activities`, `search_sessions` |
| Comparison history | ComparisonHistory | ComparisonHistoryScreen | Category-filtered authenticated ingest sessions | `/commerce/comparisons`; `search_sessions`, `ingested_provider_results` |
| Comparison evidence | ComparisonHistoryDetail | ComparisonHistoryDetailScreen | Provider observations, capture time, historical-data disclosure and rerun action | `/commerce/comparisons/{id}` with ownership enforcement |
| Profile home | MainTabs/Profile | ProfileHubScreen | Identity, dashboard counts, active location and account-tool navigation | `/profiles/me`, `/commerce/dashboard/summary`; user_profiles and commerce aggregates |
| Profile editing | ProfileEdit | ProfileEditScreen | Display name, language/region/currency and category interests | PUT `/profiles/me`, PATCH `/profiles/me/preferences`; user_profiles |
| Decision/settings preferences | Settings | SettingsScreen | Cheapest/balanced/fastest, delivery, dietary, categories, favorite configured providers and budget | PATCH `/profiles/me/preferences`, GET `/commerce/catalog/categories`; user_profiles.preferences JSON |
| Notification/accessibility/privacy | Settings | SettingsScreen, PreferenceControls | Typed switches; activity retention and notification choices alter server behavior; location storage changes SecureStore behavior | PATCH `/profiles/me/preferences`; user_profiles.preferences; commerce activity/notification guards |
| Location management | LocationManagement | LocationManagementScreen, LocationContext | Add/edit/delete/activate address, GPS/manual geocode, explicit serviceability check | `/profiles/me/addresses/*`, `/profiles/me/serviceability`; saved_addresses; Expo Location |
| Payment preference metadata | PaymentPreferences | PaymentPreferencesScreen | Card last-four only, masked UPI/wallet/bank labels, preferred method and non-authoritative benefit tags | `/profiles/me/payment-preferences/*`; payment_preferences; API rejects full credentials |
| Connected accounts | ConnectedAccounts | ConnectedAccountsScreen | Disconnected/connecting/connected/expired states, consent sheet, visible system-browser OAuth, signed callback verification and non-secret SecureStore cache | `/provider-connections/*`; `provider_connections`, `provider_connection_attempts`; OAuth secrets remain in the configured broker |
| Account & sessions | AccountSecurity | AccountSecurityScreen | Session listing/revocation, JSON export through system share, password-confirmed deletion | `/auth/sessions*`, `/profiles/me/export`, DELETE `/profiles/me`; refresh tokens and user-owned tables |
| Permissions | Permissions | PermissionsScreen | In-context location, notification and camera consent with device-settings handoff | Expo permission APIs; no silent background permission |
| Mobile number sign-in | PhoneAuth | PhoneAuthScreen | E.164 number validation and SMS challenge request | POST `/auth/request-otp`; `otp_challenges`; pluggable console/MSG91/2Factor/Twilio provider chain |
| OTP verification | OtpVerification | OtpVerificationScreen | Six-digit code, retry budget, resend timer, explicit SMS/development-console delivery state and SecureStore-backed authenticated session | POST `/auth/verify-otp`; `otp_challenges`, `phone_identities`, `users`, `refresh_tokens` |
| Push registration | embedded after auth + Permissions | PushRegistrationSync, pushRegistration | Explicit permission request, physical-device/EAS checks, silent resync only after prior grant | POST/DELETE `/auth/push-tokens`; `push_devices`; Expo Push Service |
| Scan & Compare | ScanCompare | ScanCompareScreen | Camera barcode scan, photo selection, identity-unverified state, user confirmation and device-local recent scans | Expo Camera/ImagePicker/SecureStore; confirmed query links to immutable AgentSearch; no fabricated SKU |
| Help & support | HelpSupport | HelpSupportScreen | FAQ, trust model and issue-category navigation | Static product-policy copy; no fake support SLA |
| Issue report | ReportIssue | ReportIssueScreen | Wrong price/product/link/refund/other form, authenticated or anonymous submission and success state | POST `/support/reports`; `support_reports`; authenticated report ownership APIs |
| Category/provider catalog | Explore, Settings, Home | CATEGORY_CATALOG and typed catalog query | Ten extensible user-facing categories, engine-category mapping, capability labels and configured providers | GET `/commerce/catalog/categories`; backend `category_catalog.py`; availability is never implied |
| Mobility setup | Mobility | MobilityScreen | `getMobilityProviders`, exact coordinate entry, class/objective | GET `/mobility/providers`; no address-geocoding endpoint exists |
| Mobility results | MobilityResults | MobilityResultsScreen | `compareMobilityFares`; complete fare-component rendering | POST `/mobility/compare`; `estimated_reference_formula`, not live quotes |
| Flight setup | Travel | TravelScreen | `getPopularRoutes`, `searchFlights`; typed IATA/date/cabin request | GET popular routes; POST `/travel/flights/search` |
| Flight results | FlightResults | FlightResultsScreen | Typed FlightSearchResult with a verified-source gate; mock/preview provenance resolves to unavailable | Verified provider inventory only; preview generation defaults disabled |
| Hotel setup | Hotels | HotelsScreen | `searchHotels`; validated dates, guests, rooms, budget and stars | POST `/travel/hotels/search` |
| Hotel results | HotelResults | HotelResultsScreen | Typed HotelSearchResult, verified-source gate and local refundable display filter | Verified provider inventory only; preview generation defaults disabled; map remains coordinate-gated |
| Deals discovery | Deals | DealsScreen | `getDeals`; category/text/cashback/expiry presentation filters | GET `/deals`; derived from ingested_provider_results |
| Deal detail | DealDetail | DealDetailScreen | Typed Deal, source, supplied eligibility fields and terms | Persisted provider observation; missing fields shown as not supplied |
| Finance dashboard | Finance | FinanceScreen | `getDeals('Finance')`; safe method display filter | Observed finance-category deals only; no payment-ranking/ledger endpoint |
| Shared failures | embedded | SystemState, ErrorBoundary | Loading, empty, offline, timeout, unavailable and success | API error/status mapping |

## P2 contract audit

- `mobile/api/mobility.ts`, `travel.ts`, and `deals.ts` are the only P2 clients imported by P2 screens.
- Mobility is a deterministic estimate service based on reference formulas. It is not live provider pricing.
- Flights and Hotels fail closed unless verified inventory is supplied. The backend preview flag defaults off, and mobile result screens reject `mock`, `preview` or `generated` provenance instead of exposing a handoff.
- Deals are no longer embedded in the mobile client. `/api/v1/deals` derives discounts only from persisted provider observations containing an original price greater than the observed price, or explicit supplied offer terms.
- Finance currently has no typed ranking or savings-ledger API. It uses the Deals client for observed Finance offers and does not invent a best card, UPI benefit or verified savings.

## P3 retention contract audit

- Every list mutation validates collection ownership and saved-item ownership. Duplicate list membership returns `409`; cross-user resources remain indistinguishable from missing resources with `404`.
- Shared lists are private by default. Sharing generates an opaque token, exposes a read-only item view without user identity, and revocation invalidates the token immediately.
- Comparison history is not reconstructed on-device. It reads the authenticated `search_sessions` and `ingested_provider_results` already written by `/aggregator/ingest` and labels observations as historical rather than current prices.
- Notification deep links are consumed through a mobile allowlist. Unknown or absent destinations are never executed as arbitrary links.
- Watch targets, active state, and last observed price use the commerce API as the authority; the UI does not promise that a target will be reached or that an observation remains current.

## P4 personalization contract audit

- Profile and settings updates use a typed deep-merge endpoint, so changing one nested preference does not erase unrelated preferences.
- Disabling activity retention prevents new commerce activity rows. Disabling price-drop notifications prevents watch-creation notifications; provider-side messages remain outside TrueCost control.
- Saved addresses are user-owned records. Serviceability is reported as `verification_required` until a category request actually checks providers; configured providers are not treated as nearby or available.
- Active-location persistence is opt-in and uses Expo SecureStore. Disabling it removes the encrypted device value; manual area selection is geocoded before it enters search state.
- Payment records accept safe presentation metadata only. The API rejects full card numbers, CVVs, bank account numbers, PINs, OTPs and unmasked UPI identifiers.
- The category catalog separates product labels from immutable engine labels—for example Flights maps to Travel and Services maps to Productivity—so new verticals can be added without changing the protected search engine.

## Protected boundary

mobile/components/core/ScraperManager.tsx and mobile/screens/AgentSearchScreen.tsx remain immutable. `npm run test:protected` verifies their approved hashes.

## P5 completion audit

- Search results cross the protected boundary only through `ProductCard`, which retains observed offers/provenance, opens Product Detail, and persists authenticated cart items. It never substitutes generic provider homepages for a missing supplied deep link.
- Cart optimization results are persisted as immutable versions. The mobile result renders backend totals and fulfillment groups without recomputing them. If a requested objective is not authoritative in the deployed optimizer response, that difference is disclosed.
- Scan captures remain device-local until comparison is explicitly requested. Barcodes and images are labeled identity-unverified; image comparison requires user-confirmed product words.
- Motion respects both the operating-system reduced-motion setting and the stored TrueCost accessibility preference. Navigation transitions and progressive loading pulses are disabled accordingly.
- Shared lists use `truecost://shared-list/:shareToken`; notification navigation remains route-allowlisted. Unknown strings and missing provider destinations are never executed.
- Support reports store only the fields submitted by the user. UI and API warn against secrets and full payment data; anonymous reports have no user ownership attached.

## Phase 6 production infrastructure

- Active price watches are scheduled by Celery Beat and evaluated by distributed-lock Celery workers. The pricing engine reads only trusted observations already persisted by ingestion; it never starts a provider scraper.
- A unique `(watch_id, observation_key)` trigger and one-row-per-notification outbox make alert generation and dispatch safe across retries and concurrent workers.
- Target events atomically persist an in-app notification, activity and delivery intent. Expo delivery/receipt failures do not roll back the alert; invalid device tokens are deactivated.
- OTP challenges store only an HMAC of the code, expire after five minutes by default, are single-use, and enforce request plus verification-attempt limits.
- Production startup rejects the development console SMS adapter. MSG91 is the recommended India primary, 2Factor can be its explicit failover, and Twilio remains optional; every selected provider and Expo read credentials only from deployment environment variables.
- SMS failover occurs only after a confirmed rejection or connection failure. An ambiguous read/write timeout does not trigger a second vendor, preventing duplicate OTP delivery. TrueCost remains the verification authority and stores only an HMAC of each code.
- Provider account connection is capability-gated behind `PROVIDER_CONNECTION_BROKER_URL` and a deployment secret. The mobile app cannot mark itself connected; a short-lived attempt and signed broker callback are required.
- No provider password, OTP, browser cookie, access token or refresh token enters the mobile app or API-owned tables. Official tokens are encrypted only in the broker-owned vault table under a restricted database role.
- Expo Go is a supported comparison runtime but not a remote-push runtime on SDK 53+. `expo-notifications` is dynamically loaded only after the Expo Go guard; Expo Go receives an explicit development-build message while EAS/development builds retain full push registration.
# Production platform completion (2026-08-21)

| Screen / system | Route / component | API / state | Backend / database |
| --- | --- | --- | --- |
| Category availability | Home / Explore / generated category catalog | `GET /api/v1/providers`; generated `providerManifest.generated.ts` | Canonical `provider_catalog.json`, `provider_operational_states` |
| Connected Accounts | `ConnectedAccounts` | Account-scoped SecureStore status cache; system OAuth browser | `/api/v1/provider-connections`; one-time attempt ownership; broker PKCE; broker-only encrypted vault |
| Account deletion (email) | `AccountSecurity` | Password reauthentication | `DELETE /profiles/me`; broker revocation outbox before cascade |
| Account deletion (phone) | `AccountSecurity` OTP state | `/auth/request-otp`, `/auth/reauth/verify-otp` | Hashed expiring OTP challenge and 10-minute reauthentication JWT |
| Price alerts | Watchlist / Notifications | Commerce watches and notification deep links | Celery evaluation, threshold trigger, transactional `notification_outbox`, Expo receipt reconciliation |
| Provider status | Reusable unavailable/partial states | `catalogued`, `testing`, `verified`, `degraded`, `disabled` | Public provider API plus admin operational diagnostics |
| Active location | Location gate / management | Account-scoped SecureStore location | Saved-address profile APIs; explicit serviceability verification |

The two protected search modules remain external to this map's implementation
scope. All persisted results still enter through `/api/v1/aggregator/ingest`.
