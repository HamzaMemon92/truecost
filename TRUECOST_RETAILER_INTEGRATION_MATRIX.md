# TrueCost Retailer Integration Matrix

This document provides an evidence-based assessment of potential live retailer integrations. It classifies each retailer based on technical availability, commercial requirements, data richness, and geographic scope to determine the optimal integration strategy for TrueCost.

## Retailer Assessment

### 1. Zepto
**Classification:** RESEARCH REQUIRED / PARTNER ACCESS REQUIRED
*   **Official Consumer API:** No documented public consumer API. Apps use internal proprietary endpoints.
*   **Official Partner/Developer API:** No open developer portal. Likely requires business development/partnership.
*   **Catalog/Feed:** Typically provided only to authorized affiliate partners or aggregators (e.g., ONDC if they participate).
*   **Pricing & Inventory:** Highly volatile, hyperlocal. Only available via reverse-engineered internal APIs (unauthorized/fragile) or official partner webhooks.
*   **Location/PIN Support:** Hyperlocal geofencing (latitude/longitude polygons) is essential. PIN codes are often too broad.
*   **Product Images:** High-quality SKU imagery exists, but direct hotlinking is likely against terms of service.
*   **SKU Availability:** Internal SKUs are used; mapping to GTIN/EAN requires a master catalog.
*   **Deep-link Support:** Deep-linking to product pages or cart is generally supported in-app via specific intent URIs.
*   **Authentication:** Strong bot protection (Cloudflare, Captchas) on web and app endpoints.
*   **Integration Difficulty:** High (if unauthorized scraping) / Medium (if official API).
*   **Freshness Potential:** Excellent (minutes) if authorized.

### 2. Swiggy Instamart
**Classification:** RESEARCH REQUIRED / PARTNER ACCESS REQUIRED
*   **Official Consumer API:** No documented public consumer API.
*   **Official Partner API:** Swiggy has developer programs, but Instamart access is tightly controlled and usually restricted to massive enterprise partners.
*   **Catalog/Feed:** Unknown availability without a partner agreement.
*   **Pricing & Inventory:** Highly dynamic and location-dependent.
*   **Location/PIN Support:** Exact latitude/longitude required for accurate delivery estimation and stock.
*   **Product Images:** Hosted on Swiggy's CDN. Unauthorized scraping and hotlinking face strict security measures.
*   **SKU Availability:** Internal IDs.
*   **Deep-link Support:** Web and App deep-links exist (e.g., `swiggy://`).
*   **Authentication:** Complex token-based auth, device fingerprinting, and rate limiting.
*   **Integration Difficulty:** High.

### 3. Blinkit (Zomato)
**Classification:** RESEARCH REQUIRED / PARTNER ACCESS REQUIRED
*   **Official Consumer API:** No public API.
*   **Official Partner API:** Requires Zomato/Blinkit partnership.
*   **Catalog/Feed:** Partner feeds exist for major brands and aggregators.
*   **Pricing & Inventory:** Hyperlocal and fast-changing.
*   **Location/PIN Support:** Latitude/longitude or specific store IDs.
*   **Product Images:** Good quality, but CDN protected.
*   **SKU Availability:** Proprietary SKUs.
*   **Deep-link Support:** Deep links to products are available on the web (`blinkit.com/prn/...`).
*   **Authentication:** Strong perimeter defense.
*   **Integration Difficulty:** High.

### 4. BigBasket (Tata)
**Classification:** RESEARCH REQUIRED
*   **Official Consumer API:** No public API, but web endpoints are sometimes less aggressively blocked than pure Q-commerce apps.
*   **Official Partner API:** Affiliate and partner feeds exist (historically had an affiliate program).
*   **Catalog/Feed:** Feeds are structured and more traditional e-commerce style.
*   **Pricing & Inventory:** Slotted delivery and BB Now (Q-commerce). Less volatile than Zepto for slotted delivery.
*   **Location/PIN Support:** Works well with standard PIN codes for slotted, lat/lng for BB Now.
*   **Product Images:** Standardized e-commerce imagery.
*   **SKU Availability:** Clear internal SKUs, often exposes EANs in structured data.
*   **Deep-link Support:** Standard web URLs.
*   **Authentication:** Token-based, moderately protected.
*   **Integration Difficulty:** Medium.

### 5. ONDC (Open Network for Digital Commerce)
**Classification:** RECOMMENDED FIRST TARGET / RESEARCH REQUIRED
*   **Official Consumer API:** N/A (ONDC is a protocol, not a retailer). TrueCost would act as a Buyer App.
*   **Official Partner API:** Yes, fully documented and open protocol.
*   **Catalog/Feed:** Standardized catalog format across all participating seller apps.
*   **Pricing & Inventory:** Standardized availability, price, and logistics tracking.
*   **Location/PIN Support:** Pincode and Lat/Lng standard.
*   **Product Images:** Standardized URLs provided in the catalog.
*   **SKU Availability:** Standardized items, often with EAN/GTIN.
*   **Deep-link Support:** Cart/Checkout is handled natively within the ONDC protocol.
*   **Authentication:** Standardized signing and verification (Beckn protocol).
*   **Integration Difficulty:** Medium to High (protocol complexity), but strictly authorized and legal.
*   **Freshness Potential:** Defined by the protocol and seller app SLAs.

## Source of Truth Hierarchy

TrueCost cannot rely on scraped, brittle data. Data ingestion must follow this strict hierarchy of trust:

1.  **Official Retailer API (Authorized Partner):** Direct, authorized API access with API keys. Guaranteed structure, freshness, and legality. (Highest Trust)
2.  **ONDC Network (Authorized Buyer Node):** Standardized, authorized catalog and pricing data across multiple sellers. (High Trust)
3.  **Authorized Affiliate Product Feeds:** Provided via affiliate networks (e.g., Admitad, Cuelinks) offering periodic CSV/XML dumps of catalogs and pricing. (Medium Trust - Often stale availability).
4.  **Verified Catalog Provider (Database):** A master database (like GS1, specialized FMCG databases) mapping EANs to canonical metadata and images. Provides core identity but no live pricing.
5.  **Internal Normalized Catalog:** TrueCost's own database caching previously observed canonical items.
6.  **Unauthorized Scraping:** Explicitly rejected for production due to fragility, legal risk, and IP blocking.

## Product Catalog & SKU Matching Strategy

### Ingestion Strategy
*   **Brand, Name, Variant, Quantity, Pack:** Extracted from retailer data or master catalog.
*   **Identity Keys:**
    1.  `GTIN/EAN/UPC`: The absolute source of truth. If available, this definitively links a Retailer SKU to a `CanonicalProduct`.
    2.  `Brand + Normalized Title + Variant + Quantity`: Fallback composite key. Requires strict string normalization (lowercasing, unit standardization).
*   **Retailer Offer Creation:** An incoming retailer item is first searched against `GTIN`. If matched, a `RetailerOffer` is attached to the existing `CanonicalProduct`. If no GTIN, the composite key is used. If confidence is low, a *new* `CanonicalProduct` is created to avoid false merges.

### Matching Outcomes
1.  **EXACT_MATCH:** GTIN matches, or 100% composite key match. Offer merged.
2.  **HIGH_CONFIDENCE_MATCH:** High string similarity on brand + title + normalized quantity. Offer merged.
3.  **POSSIBLE_MATCH:** Partial string match but missing quantity/variant data. Offer kept separate as a distinct product to prevent cross-contamination.
4.  **NO_MATCH:** Completely new item. New `CanonicalProduct` created.

## Verified Image Pipeline

Images are critical for trust. A 500ml milk packet must not show a 1L milk image.

### Acquisition Priority
1.  **Trusted Product Database (GS1/FMCG APIs):** Guaranteed GTIN-to-Image mapping. Authorized.
2.  **Authorized Retailer Feed Image:** Provided via official API. Capped at `KNOWN_SOURCE` until validated against GTIN.
3.  **Fallback SVG/Iconography:** Used when no verified image exists.

### Rejected Sources
*   Google Image Search / Bing scraping.
*   Generative AI packaging.
*   Unauthorized hotlinking from competitor CDNs.

### Image Status Lifecycle
*   `IMAGE_PENDING`: Newly ingested retailer image.
*   `KNOWN_SOURCE`: Image from an authorized retailer feed, awaiting manual/heuristic verification.
*   `TRUSTED`: Image explicitly verified against GTIN or manually approved.
*   `REJECTED`: Image flagged for inaccuracy.
*   `FALLBACK`: Category-level iconography.

## Data Ingestion & Freshness

*   **Catalog/Metadata/Images:** Periodic synchronization (daily/weekly). These rarely change.
*   **Price/Availability/ETA:** On-demand (Live Search) or highly frequent polling (minutes).
*   **Freshness Thresholds (Configurable):**
    *   Price: `STALE` if > 120 mins.
    *   Availability: `STALE` if > 30 mins.
    *   Images/Catalog: `STALE` if > 7 days.

## First Retailer Recommendation

**Recommendation:** BigBasket (via Affiliate/Partner Feed) OR ONDC Protocol Integration.

**Reasoning:**
While Zepto/Blinkit are the target Q-commerce leaders, they have the highest technical and legal barriers to entry (no public APIs, extreme bot protection). 
1.  **BigBasket:** Has historically offered affiliate product feeds and possesses a massive, structured catalog with clear GTINs and standardized units. It allows TrueCost to test the integration, matching, and image pipelines with real, authorized data before tackling the complexities of reverse-engineering or business-developing Q-commerce APIs.
2.  **ONDC:** Alternatively, integrating as an ONDC Buyer App immediately grants authorized, structured access to multiple grocery sellers (including aggregators) using a standardized API, completely bypassing the need to scrape proprietary walled gardens.

**First Step Action:** Pursue an ONDC developer sandbox account or a BigBasket affiliate feed to build the first `LiveGroceryProviderAdapter` legally.

## First Live-Integration Implementation Plan (Conceptual)

Assuming BigBasket via Authorized Feed/API:

1.  **Configuration:** Add `BIGBASKET_API_KEY`, `BIGBASKET_AFFILIATE_ID` to `.env` (backend only).
2.  **Adapter Creation:** Create `backend/app/providers/bigbasket_provider.py` implementing `GroceryProvider`.
3.  **Authentication:** Implement secure token fetching inside the adapter.
4.  **Search Method:** Map TrueCost `search(query, location)` to the partner API's search endpoint. Map Pincode.
5.  **Normalization:** Parse the response into `CanonicalGroceryItem`.
    *   Map `bb_price` -> `price`.
    *   Map `bb_stock` -> `availability` (`IN_STOCK` or `OUT_OF_STOCK`).
    *   Inject `retrieved_at = datetime.now(timezone.utc)`.
6.  **Image Handling:** Ingest the provided image URL as `KNOWN_SOURCE`.
7.  **Deep-links:** Construct the authorized affiliate deep-link (`https://bigbasket.com/pd/SKU/?affiliate_id=...`).
8.  **Testing:** Add `test_bigbasket_provider.py` using VCR.py or mocked HTTPX responses to ensure the adapter maps perfectly without hitting the live API during CI.
