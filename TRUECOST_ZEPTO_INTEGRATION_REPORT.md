# Zepto Integration Engineering Report — v2 (Final)
**Date:** 2026-08-18  
**Status:** 🔴 RED — Direct backend integration blocked. Zepto data available via authorized aggregator.

---

## A. What We Discovered

The Zepto consumer search endpoint (`POST bff-gateway.zepto.com/user-search-service/api/v3/search`)
is observable in a user's own browser DevTools and returns rich, structured product catalog data.
However, the endpoint is protected by Amazon WAF + CloudFront and cannot be reproduced by a
standalone backend HTTP client.

The investigation was run twice (prior session + 2026-08-18). Both attempts produced identical results.

**However:** Zepto data IS currently accessible to TrueCost's backend through the
**QuickCommerceAPI authorized aggregator**, which is already live in production.

---

## B. Exact Zepto Request Architecture

```
Browser:
  POST https://bff-gateway.zepto.com/user-search-service/api/v3/search
  Body: { query, pageNumber, mode, userSessionId, storeId[], lat, lon }
  Auth: Amazon WAF JS challenge + browser cookies + userSessionId

Backend attempt (BLOCKED):
  POST https://bff-gateway.zepto.com/...
  Response: HTTP 202, x-amzn-waf-action: challenge, Body: (empty)

Authorized path (WORKING):
  GET https://api.quickcommerceapi.com/v1/groupsearch?q=...&platforms=Zepto&lat=...&lon=...
  Header: X-API-Key: [configured in .env, never in frontend]
  Response: HTTP 200, Zepto product catalog
```

---

## C. Authentication / Session Requirements

| Requirement                  | Direct Endpoint              | Via QuickCommerceAPI       |
|------------------------------|------------------------------|----------------------------|
| Browser session              | Required (cannot fake)       | Not required               |
| WAF JS challenge pass cookie | Required (cannot fake)       | Not required               |
| userSessionId                | Required (cannot extract)    | Not required               |
| API key                      | No (proprietary, internal)   | Yes (`QUICKCOMMERCE_API_KEY`) |
| TLS fingerprint matching     | Required (cannot fake)       | Standard TLS — safe        |

**Decision:** Use QuickCommerceAPI. Do NOT attempt to bypass Zepto WAF.

---

## D. Location / Store Mechanics

Zepto's native endpoint translates `lat`/`lon` → `storeId` server-side.
The QuickCommerceAPI aggregator accepts `lat`/`lon` directly and performs
the same store resolution on behalf of the client.

TrueCost passes the user's location from the `Location` schema:
- `latitude` + `longitude` → `?lat=&lon=` on the QuickCommerceAPI call
- `postal_code` → `?pincode=` as fallback

Store identity is preserved in the aggregator response under `platform.name = "Zepto"`.

---

## E. Product JSON Structure (Via Authorized Aggregator)

```json
{
  "id": "zepto-amul-taaza-500ml-001",
  "name": "Amul Taaza Toned Milk",
  "brand": "Amul",
  "available": true,
  "images": ["https://cdn.zepto.com/.../amul-taaza-500ml.jpg"],
  "mrp": 30,
  "offer_price": 30,
  "quantity": "500 ml",
  "deeplink": "https://www.zeptonow.com/pn/...",
  "rating": 4.6,
  "rating_count": 12000,
  "inventory": 10,
  "platform": {
    "name": "Zepto",
    "sla": "10 mins",
    "open": true
  }
}
```

---

## F. Whether Backend Reproduction Works (Direct Endpoint)

🔴 **NO.**

Two independent diagnostic runs:

| Run  | Date       | Status Code | WAF Header                    | Body   |
|------|------------|-------------|-------------------------------|--------|
| 1    | Prior      | 202         | `x-amzn-waf-action: challenge`| empty  |
| 2    | 2026-08-18 | 202         | `x-amzn-waf-action: challenge`| empty  |

The endpoint is behind Amazon CloudFront and issues a JS challenge. A Python
`httpx` client cannot solve this challenge without circumventing WAF controls.

---

## G. Whether a Real Product Reached CanonicalGroceryItem

🟡 **YES — via authorized aggregator path.**

Zepto-attributed `CanonicalGroceryItem` records ARE produced successfully via
the `QuickCommerceProvider`, which uses the authorized QuickCommerceAPI aggregator.
Items appear with `provider="Zepto"` and `source_type="live"`.

Direct Zepto endpoint: 🔴 Not proven (WAF blocked)  
Via QuickCommerceAPI aggregator: 🟢 Live and verified (see existing live tests)

---

## H. Code Changed / Created

| File                                                                | Action  | Purpose                                               |
|---------------------------------------------------------------------|---------|-------------------------------------------------------|
| `TRUECOST_ZEPTO_ENDPOINT_ANALYSIS.md`                               | Updated | Full field classification table with live harness results |
| `backend/tests/fixtures/zepto_search_response.json`                 | Created | Sanitized fixture for contract tests (no secrets)     |
| `backend/tests/test_zepto_grocery_contract.py`                      | Created | Deterministic mapping contract tests (35 assertions)  |
| `backend/tests/test_zepto_grocery_live.py`                          | Created | Live test via QuickCommerceAPI (skips without key)    |
| `TRUECOST_ZEPTO_INTEGRATION_REPORT.md`                              | Updated | This document                                         |

**NOT created:** `backend/app/providers/zepto_grocery_provider.py`  
Rationale: A direct Zepto provider adapter cannot be implemented without violating WAF/security rules. Zepto data is served via the existing `QuickCommerceProvider`.

---

## I. Tests and Results

### Contract Tests

```
pytest backend/tests/test_zepto_grocery_contract.py -v
```

All tests use sanitized fixture data. No network calls. No credentials required.
Expected: all PASS.

### Live Test

```
pytest backend/tests/test_zepto_grocery_live.py -v -s
```

- Without `QUICKCOMMERCE_API_KEY`: **SKIP** (clean, no failure)  
- With `QUICKCOMMERCE_API_KEY` configured: **PASS** if QuickCommerceAPI returns Zepto data  
- With `QUICKCOMMERCE_API_KEY` but API failure: **FAIL** (clearly labeled)

---

## J. Security Limitations

1. The Zepto consumer endpoint is protected by Amazon WAF + CloudFront. Any attempt to bypass
   this protection would require solving WAF JS challenges or rotating stolen browser cookies.
   Both are explicitly prohibited by TrueCost's security mandate.

2. `userSessionId` from a user's Zepto browser session must never be extracted, stored, or
   transmitted by TrueCost's backend. Doing so would constitute unauthorized session hijacking.

3. Zepto CDN image URLs (`cdn.zepto.com`) are served from a third-party CDN and must be treated
   as `image_verified=False` until explicitly validated by an authorized admin or GTIN match.
   Hotlinking these in the TrueCost UI may violate Zepto's Terms of Service.

4. The QuickCommerceAPI key must remain exclusively server-side. It is stored in `backend/.env`
   and never exposed to the frontend.

---

## K. Whether Zepto Should Become a Production Provider

**Current answer: It already is — via QuickCommerceAPI.**

`QuickCommerceProvider` correctly attributes returned items as `provider="Zepto"` and
`source_type="live"`. The frontend already renders Zepto results when available.

**Direct Zepto provider** (`zepto_grocery_provider.py`): 🔴 Do NOT implement.
The direct endpoint is WAF-blocked and session-bound. Implementation would require
security control circumvention, which is explicitly prohibited.

**Upgrade path:** Approach Zepto for an official B2B/partner API key (separate from
consumer app credentials). If granted, a direct `ZeptoGroceryProvider` adapter could
be built against the partner endpoint using standard API key authentication.

---

## L. Recommended Next Provider / Integration Strategy

| Priority | Path                              | Status          | Rationale                                                   |
|----------|-----------------------------------|-----------------|-------------------------------------------------------------|
| 1        | QuickCommerceAPI (current)        | 🟢 LIVE         | Authorized aggregator for Zepto + Blinkit + Swiggy          |
| 2        | ONDC Buyer App integration        | 🟡 Foundation   | Open protocol, legally sound, multi-seller access           |
| 3        | BigBasket affiliate feed          | ⏳ Research     | Structured catalog, GTIN data, moderate auth complexity     |
| 4        | Zepto official partner API        | ⏳ BD required  | Requires business development relationship with Zepto       |
| 5        | Zepto direct consumer endpoint    | 🔴 BLOCKED      | WAF + session bound. Do not attempt without authorization   |

---

## Final Statement

> "We can see the request in Chrome DevTools" ≠ "We have a stable backend integration."
>
> The Zepto consumer search endpoint is not safely reproducible by a TrueCost backend service.
> Zepto data is legitimately accessible today through the QuickCommerceAPI authorized aggregator,
> which is already live, tested, and integrated. No security controls were bypassed or circumvented.
> No credentials were fabricated, extracted, or rotated. No mock data was used to simulate success.
