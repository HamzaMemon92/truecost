# Zepto Endpoint Request Dependency Analysis — v2 (Updated 2026-08-18)

This document is the result of a systematic Phase 4 investigation of the
`POST https://bff-gateway.zepto.com/user-search-service/api/v3/search` endpoint.

## Investigation Method

1. Endpoint was observed in the user's own authenticated browser session via DevTools.
2. A safe diagnostic harness (`backend/tests/scratch/zepto_harness.py`) was executed against
   the endpoint with no authentication, no cookies, and no WAF bypass.
3. The harness was run a second time on 2026-08-18 to confirm prior findings.

## Confirmed Live Result (2026-08-18)

```
Status Code:           202
Server:                CloudFront
x-amzn-waf-action:     challenge
x-cache:               Error from cloudfront
Content-Length:        0
Body:                  (empty — WAF dropped the request before it reached the origin)
```

The endpoint is served via Amazon CloudFront and protected by Amazon WAF.
A non-browser backend client that cannot solve the WAF JS challenge receives HTTP 202
with no body instead of a catalog response.

---

## Field / Header Classification Table

| Field / Header             | Category                      | Required?      | Why                                                                 | Safe Backend Equivalent                            |
|----------------------------|-------------------------------|----------------|----------------------------------------------------------------------|----------------------------------------------------|
| `Host`                     | REQUIRED_FOR_SERVER           | Yes            | Routes to correct Zepto microservice                                 | Static value, safe.                                |
| `Content-Type`             | REQUIRED_FOR_SERVER           | Yes            | Signals JSON body encoding                                           | Safe (`application/json`)                          |
| `query`                    | REQUIRED_FOR_SERVER           | Yes            | The search string                                                    | Safe to construct in backend                       |
| `pageNumber`               | REQUIRED_FOR_SERVER           | Yes            | Pagination offset                                                    | Safe (integer, starts at 1)                        |
| `mode`                     | REQUIRED_FOR_SERVER           | Yes            | API operation mode (`SEARCH`, etc.)                                  | Safe (static constant)                             |
| `storeId` / store IDs      | REQUIRED_FOR_STORE_SELECTION  | Yes            | Determines which hyperlocal fulfillment center to search             | Requires legitimate store-ID resolution from lat/lon|
| `userSessionId`            | REQUIRED_FOR_AUTHENTICATION   | Yes (inferred) | Ties request to a Zepto user account/cart session                    | **BLOCKED** — cannot safely extract from browser   |
| `location context` (lat/lon)| REQUIRED_FOR_LOCATION         | Yes            | Correlates user coordinates to a serviceable store                   | Safe value if user grants permission               |
| `store serviceability`     | REQUIRED_FOR_STORE_SELECTION  | Yes            | Serviceability envelope required for pricing                         | Requires a Zepto-internal location→store lookup    |
| `User-Agent`               | WAF/BROWSER_BOUND             | Yes (implicit) | Amazon WAF validates User-Agent and browser fingerprint              | **BLOCKED** — browser UA alone is insufficient     |
| `x-amzn-waf-action`        | WAF/BROWSER_BOUND             | Yes (implicit) | WAF issues JS challenge; clients that cannot solve it get 202        | **BLOCKED** — solving WAF challenge requires browser |
| `Cookie` (WAF token)       | WAF/BROWSER_BOUND             | Yes (implicit) | CloudFront/WAF stores a challenge-pass cookie in the browser         | **BLOCKED** — cannot safely extract/rotate         |
| `Referer`                  | OPTIONAL_BROWSER_METADATA     | No             | Browser-sent referrer header                                         | Safe to omit                                       |
| `Accept-Language`          | OPTIONAL_BROWSER_METADATA     | No             | Locale hints                                                         | Safe to omit                                       |
| `sec-ch-ua` / TLS entropy  | WAF/BROWSER_BOUND             | Yes (implicit) | TLS fingerprinting / JA3 heuristics feed WAF bot score               | **BLOCKED** — cannot safely reproduce              |
| Analytics / tracing headers| ANALYTICS/TELEMETRY           | No             | Internal telemetry for Zepto BI                                      | Safe to omit                                       |

---

## Verdict on Each Investigation Question

| Question                                                    | Answer                                                                         |
|-------------------------------------------------------------|--------------------------------------------------------------------------------|
| 1. What does the request require?                           | POST JSON body + WAF-solved browser session + auth session token + store ID    |
| 2. Which fields are mandatory?                              | `query`, `pageNumber`, `mode`, `storeId`, `userSessionId`, WAF cookie          |
| 3. Which are browser metadata?                              | `Referer`, `Accept-Language`, `sec-ch-ua`                                      |
| 4. Which are location/store?                                | `lat`, `lon` → Zepto maps to `storeId` internally                              |
| 5. Which are auth/session?                                  | `userSessionId`, WAF cookie, auth headers                                      |
| 6. Can it be reproduced by backend HTTP client?             | **NO** — WAF returns HTTP 202 + empty body (challenge) to non-browser clients  |
| 7. Requires authenticated session?                          | Yes — `userSessionId` required                                                 |
| 8. Requires short-lived request signatures / CSRF?          | Likely yes — WAF challenge is ephemeral                                        |
| 9. Depends on browser cookies?                              | Yes — WAF challenge pass is stored as a cookie                                 |
| 10. Depends on WAF / browser state?                         | Yes — Amazon WAF + CloudFront enforce browser fingerprinting                   |
| 11. Can backend safely maintain necessary state?            | **NO** — WAF challenge state is not reproducible without browser environment   |
| 12. Suitable for a persistent provider adapter?             | **NO** — WAF blocks all current non-browser access attempts                    |
| 13. What data can reliably be extracted?                    | None via this mechanism                                                        |
| 14. Which fields must remain UNKNOWN?                       | `delivery_minutes`, precise inventory, coupon_discount, platform_fee           |

---

## Conclusion

🔴 **RED — BLOCKED / NOT PROVEN**

Backend replication of `POST bff-gateway.zepto.com/user-search-service/api/v3/search` is not
currently possible without:

1. Solving WAF JS challenges (not legitimate for a backend service)
2. Extracting and rotating browser session tokens (violates security rules)
3. Bypassing TLS fingerprinting (not legitimate)

**IMPLEMENTATION HALTED at the adapter boundary.**
No `zepto_grocery_provider.py` will be implemented against this endpoint.

## Recommended Legitimate Paths

| Path                          | Trust Level | Difficulty | Status         |
|-------------------------------|-------------|------------|----------------|
| QuickCommerceAPI aggregator   | Medium      | Done       | ✅ LIVE TODAY  |
| ONDC Buyer App Protocol       | High        | Medium     | ⏳ Foundation built |
| Zepto Official Partner API    | High        | High       | ⏳ Requires BD |
| Zepto via ONDC (if they join) | High        | Medium     | ⏳ Future      |
