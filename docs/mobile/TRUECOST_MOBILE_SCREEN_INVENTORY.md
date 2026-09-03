# TrueCost mobile screen inventory

## Verified reference audit

- 65 physical files were opened and visually inspected.
- 9 exact duplicate pairs were verified by SHA-256.
- 56 unique image hashes remain after deduplication.
- 2 jewellery collages (12_13_04 PM and 12_38_53 PM) are unrelated and excluded.
- Therefore the product has 63 relevant physical files and 54 unique TrueCost visual references.

Each visually distinct product state is normalized into a production route or a reusable component state. Duplicate and variant designs do not create duplicate navigation routes.

## Canonical route families

| Product area | Canonical screens represented | Route family |
| --- | --- | --- |
| Entry | Welcome, email auth, mobile number, OTP verification, guest and permissions | Welcome, Auth, PhoneAuth, OtpVerification, LocationGate |
| Discovery | Home, universal search, suggestions, recent intent and category hub | Home, Explore, Compare |
| Grocery | Grocery home, basket builder, quantity, substitution, comparison and handoff | GroceryHub, AgentSearch, Cart, Substitutions, CheckoutHandoff |
| Shopping | Search, detail, offers, product comparison, price trends and alerts | ShoppingHub, AgentSearch, ProductDetail, Comparison, PriceTrends, Watchlist |
| Decision | Recommendation, alternatives, evidence, assumptions and sensitivity | Comparison, DecisionExplanation |
| Mobility | Trip setup, pickup/drop coordinates, timing, class, objective, estimated provider results and recommendation | Mobility, MobilityResults |
| Flights / Travel | One-way/round-trip setup, airports, dates, travellers, cabin, flexibility, preview results and recommendation | Travel, FlightResults |
| Hotels | Stay setup, destination, dates, guests/rooms, budget/rating/value filters, preview results and recommendation | Hotels, HotelResults; map data capability-gated |
| Deals | Observed/cashback/expiring filters, results, offer detail and terms boundary | Deals, DealDetail |
| Finance | Dashboard, Cards/UPI/Wallet/Net banking, observed finance offers and safety state | Finance, DealDetail; verified ledger and ranking capability-gated |
| Retention | Saved items, baskets, alerts, notifications and activity | Saved, Watchlist, Notifications, Activity |
| Personalization | Profile editing, settings, locations, serviceability, safe payment preferences and official provider connections | Profile, ProfileEdit, Settings, LocationManagement, PaymentPreferences, ConnectedAccounts |
| Utility | Scan camera/barcode/image states, permissions, support/report forms, trust/FAQ and system states | ScanCompare, Permissions, HelpSupport, ReportIssue plus reusable SystemState |

## Normalization rules

- One compact five-item Orbit Rail replaces every oversized or category-specific navigation variant.
- Marketing claims such as “100% accurate,” guarantees, provider counts and user counts are never copied without backend evidence.
- Mobile OTP is production-wired through expiring, hashed, rate-limited challenges and a pluggable SMS provider. Social login remains capability-gated because no approved provider contract exists.
- Missing screenshots are self-designed from Porcelain, Deep Ink, Electric Iris, Evidence Mint and the shared interaction rules.
- The client never receives an OTP from the API. Console delivery is development/test-only; production selects MSG91, 2Factor or Twilio using deployment-managed secrets, with failover configured explicitly.
- Connected Accounts uses official OAuth through a configured backend broker. It never extracts WebView cookies, provider passwords or reusable browser sessions; unsupported providers remain capability-gated.
- The production catalog intentionally consolidates the broad comparison surface into ten extensible categories: Grocery, Food, Pharmacy, Shopping, Mobility, Flights, Hotels, Deals, Finance and Services. User-facing names map to stable engine categories without modifying the protected search files.
