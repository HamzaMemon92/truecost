# TrueCost Multi-Category Implementation Tasks

## Phase 1 — Backend Connector Fixes
- [x] `amazon.py` — handle `{ amazonData: [...] }` shape from DOM scraper
- [x] `swiggy_food.py` — update path to `data.restaurants[].info` with recursive finder
- [x] `zomato.py` — recursive parser for restaurant nodes
- [x] `tata1mg.py` — read `data.skus[]` with `selling_price` + `mrp`
- [x] `ola.py` — read `serviceTypes[]` instead of `ride_estimate.categories`
- [x] `pharmeasy.py` — recursive finder for `productList` or `skus` nodes
- [x] `flipkart.py` — recursive finder for product nodes with title + price
- [x] `rapido.py` — handle multiple nesting shapes with recursive finder
- [x] `makemytrip.py` — recursive finder for fare + airline nodes
- [x] `meesho.py` — recursive find `product_name` + `discountedPrice`
- [x] `myntra.py` — recursive find `productName` + `price`

## Phase 1 — Mobile Scraper Fixes
- [x] `UberScraper.tsx` — filter GraphQL to only ride operations, start on booking page
- [x] `OlaScraper.tsx` — changed to `book.olacabs.com` with correct fare URL patterns
- [x] `RapidoScraper.tsx` — added geolocation override + XHR interceptor
- [x] `Tata1mgScraper.tsx` — updated intercept URL to `/v5/search/drugs` + XHR
- [x] `PharmEasyScraper.tsx` — added XHR interceptor + broadened URL patterns
- [x] `MakeMyTripScraper.tsx` — fires actual search URL with query params
- [x] `ZomatoScraper.tsx` — improved intercept pattern

## Phase 2 — Recursive Parser Upgrades (merged into Phase 1)
- [x] All connectors now use recursive finders — WAF-proof

## Phase 3 — Category-Aware UI
- [x] `RideCompareCard.tsx` — created for Mobility (groups ride types, BEST badge, savings indicator)
- [x] `RestaurantCard.tsx` — created for Food (restaurant image, brand badge, price/person, ETA)
- [x] `FlightCard.tsx` — created for Travel (airline, duration, price, provider badge)
- [x] `AgentSearchScreen.tsx` — category layout switcher, dynamic labels, dynamic empty states

## Verification
- [x] Python import tests: all 11 connectors pass
- [x] CJS live tests: 5/5 categories pass (Amazon DOM, Ola serviceTypes, Zomato recursive, MakeMyTrip, 1mg skus)
- [x] Backend restarted with fresh code
