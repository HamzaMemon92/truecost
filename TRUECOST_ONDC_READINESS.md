# TrueCost ONDC Readiness Assessment

This document maps the official ONDC (Open Network for Digital Commerce) protocol requirements against TrueCost's architecture for the **RET10 (Grocery)** domain. TrueCost integrates as a **Buyer Network Participant (BNP)**, meaning it discovers products across the network and facilitates purchases without owning inventory or maintaining seller agreements.

## 1. Network Role & Domain
- **Role:** Buyer Network Participant (BAP / Buyer App).
- **Domain Scope:** `ONDC:RET10` (Grocery).
- **Protocol Base:** Beckn Protocol (asynchronous, decentralized).

## 2. ONDC Discovery & Transaction Lifecycle
Based on official ONDC specifications, the expected transaction lifecycle for a buyer application is strictly asynchronous and relies on webhooks. TrueCost's backend must implement:
1.  **Discovery:** 
    - `POST /search`: TrueCost broadcasts a search intent (location, product name, or category) to the ONDC Gateway. Must include `context` (domain ONDC:RET10, action search, version 1.2.0, bap_id, bap_uri, transaction_id, message_id, timestamp, ttl, city, country) and `message.intent`.
    - `POST /on_search`: Seller Apps (BPPs) respond asynchronously with catalog items, seller identities, and initial pricing/availability.
2.  **Selection (Cart Building):**
    - `POST /select`: TrueCost requests confirmation of item availability, serviceability to the buyer's location, and exact delivery quotes.
    - `POST /on_select`: Seller confirms exact price, fulfillment charges, and availability.
3.  **Initialization (Checkout Prep):**
    - `POST /init`: Buyer provides billing/shipping details.
    - `POST /on_init`: Seller provides final payment terms and exact order quotes.
4.  **Confirmation (Order Finalization):**
    - `POST /confirm`: TrueCost confirms the order (post-payment).
    - `POST /on_confirm`: Seller generates the order ID and begins fulfillment.

## 3. Data Integration Strategy (Discovery)

ONDC cannot be treated as a single retailer. A single `/on_search` webhook will return results from *multiple distinct sellers*. TrueCost must enforce the following boundaries:

- **Seller Identity:** 
  - Extracted from `provider.id` and `bpp_id` in the ONDC payload.
  - Mapped directly to `RetailerOffer.retailer_name` and `RetailerOffer.retailer_id`.
- **Product Identity:**
  - ONDC items contain `item.descriptor.code` (often EAN/GTIN) and `item.id` (seller's internal ID).
  - TrueCost must use the GTIN to resolve the `CanonicalProduct` across different sellers. If GTIN is missing, fallback to string normalization (`brand` + `name` + `quantity`).
- **Location:**
  - ONDC requires context objects containing `city`, `country`, and fulfillment bounds (e.g., specific PIN or Lat/Lng constraints).
- **Pricing:**
  - `item.price.value` (selling price) and `item.price.maximum_value` (MRP).
  - Normalizes directly into `price` and `mrp` within TrueCost's pricing engine. Delivery fees are resolved during the `/select` phase.
- **Availability:**
  - `item.quantity.available` determines stock. Maps to `IN_STOCK` or `OUT_OF_STOCK`.

## 4. Credential & Environment Readiness
TrueCost backend must accommodate the following environment variables. **No credentials will be hardcoded or committed.**

| Variable | Description | Status |
| :--- | :--- | :--- |
| `ONDC_BAP_ID` | The unique Subscriber ID for TrueCost's Buyer App. | 🔴 REQUIRES ONDC ACCESS |
| `ONDC_BAP_URI` | The webhook endpoint URL where TrueCost receives ONDC callbacks (e.g., `/on_search`). | 🔴 REQUIRES ONDC ACCESS |
| `ONDC_ENV` | `mock`, `staging`, `preprod`, or `live`. | ✅ VERIFIED / IMPLEMENTED |
| `ONDC_PRIVATE_KEY` | Ed25519 private key used to sign Beckn headers for authentication. | 🔴 REQUIRES ONDC ACCESS |
| `ONDC_PUBLIC_KEY_ID` | The key ID registered with the ONDC registry. | 🔴 REQUIRES ONDC ACCESS |

## 5. Security & Authentication
All Beckn requests must include an `Authorization` header with a detached HTTP signature created using the BAP's private key. TrueCost will require a robust cryptography utility (e.g. `libsodium` via PyNaCl) to sign outgoing requests using Ed25519 and verify incoming `/on_search` webhooks from the registry. No improvised cryptography is permitted.

## 6. Implementation Architecture
1. **Mock Environment:** `MockOndcProvider` deterministically simulates the asynchronous multi-seller outcome of `/on_search`.
2. **Adapter Boundaries:** `backend/app/providers/ondc_provider.py` translates internal search requests into standard ONDC contexts and orchestrates the transformation of complex multi-provider catalog payloads back into TrueCost's decoupled `CanonicalProduct` and `RetailerOffer` domains.

## 7. Known Blockers
- **Authentication:** Cannot implement real HTTP signatures without undergoing the formal ONDC registration process to acquire a verifiable subscriber ID and public key registry entry.
- **Webhook Infrastructure:** ONDC is strictly asynchronous. TrueCost needs a publicly accessible webhook URL and an event queue (e.g., Redis + Celery/FastAPI BackgroundTasks) to stitch the `/on_search` callback back to the synchronous HTTP request waiting on the frontend.

## 8. Live-Data Status

| Status | State |
| :--- | :--- |
| **ARCHITECTURE READY** | ✅ |
| **CODE READY FOR ENVIRONMENT INTEGRATION** | ✅ |
| **ONDC NETWORK ACCESS** | ⏳ Pending onboarding/credentials |
| **CERTIFIED PRODUCTION BAP** | ❌ Not yet |

## 9. Future Integration Phases
The broader Beckn protocol explicitly separates discovery, ordering, and fulfillment. Future ONDC expansion will proceed in isolated phases:
- **PHASE ONDC-1 (Discovery):** `search` / `on_search` → Catalog normalization (Currently Mocked)
- **PHASE ONDC-2 (Selection):** `select` / `on_select` → Quote / fulfillment
- **PHASE ONDC-3 (Cart / Init):** `init` / `on_init`
- **PHASE ONDC-4 (Checkout):** `confirm` / `on_confirm`
- **PHASE ONDC-5 (Post-order):** `status`, `track`, `cancel`, `update`

## 10. Architectural Boundary
To protect the core system from ONDC protocol evolution, ONDC integration is strictly isolated:
`ONDC/Beckn` → `ONDC Adapter` → `Canonical Grocery Model` → `Common Master`
ONDC payload structures will never leak throughout the application.
