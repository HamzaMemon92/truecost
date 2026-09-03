# TrueCost AI Onboarding & System Context

**Welcome, AI Assistant!** 
You are being onboarded to the "TrueCost" project. This document provides the critical context, architecture, and current state of the system so you can seamlessly continue development with the human co-founder.

## 1. System Overview
TrueCost is a universal aggregation platform that compares prices and data across multiple domains (Shopping, Grocery, Food Delivery, Pharmacy, Mobility, and Travel). 

Because many of these platforms block traditional backend scrapers, we use a **hybrid architecture**:
1. **Frontend (React Native / Expo Mobile App):** Acts as a distributed scraper. It uses hidden `react-native-webview` instances to load provider websites (Amazon, Swiggy, Zepto, Uber, etc.), intercepts their native API calls (fetch/XHR) or falls back to DOM parsing, and extracts pure JSON product/price data.
2. **Backend (Python / FastAPI):** Receives the raw JSON payloads from the mobile app via `/api/v1/aggregator/ingest`, parses them using Provider-specific Connectors (`backend/app/connectors/`), performs Entity Resolution (matching identical items across providers), and returns unified results to the frontend.

## 2. Directory Structure
- `/mobile`: The Expo React Native app. **Crucial:** `mobile/components/scrapers/` contains 32+ scraper files. They inject JS to intercept network calls and parse DOM. We recently updated ALL scrapers to use a reactive `source` prop and avoid `useEffect` race conditions.
- `/backend`: The FastAPI python server. Contains the API, the Connectors (`backend/app/connectors/`), and the Entity Resolution engine (`backend/app/services/entity_resolution.py`).
- `/src`: A web dashboard / React frontend (if applicable to current sprint).

## 3. How to Run the System
**Backend:**
```bash
cd backend
python -m venv .venv
# activate venv
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Mobile (Scraper Engine & UI):**
```bash
cd mobile
npm install
npx expo start -c
```

## 4. Architectural Rules & Patterns (CRITICAL)
- **Scraper Pattern:** Scrapers must NEVER use `isReady` state to trigger `injectJavaScript` navigation. They must use the reactive `source` prop (e.g., `source={{ uri: query ? 'search-url' : 'homepage' }}`) to ensure the `injectedJavaScriptBeforeContentLoaded` runs *before* the search payload fires.
- **Entity Resolution (ER):** Located in `backend/app/services/entity_resolution.py`. ER is *category-aware*. Shopping uses standard product matching, while Food uses `FOOD_CONTRACT`, Mobility uses `MOBILITY_CONTRACT`. Never apply shopping item-matching logic to restaurants or cabs.
- **Testing:** The backend uses `pytest`. Run it via `pytest` inside the `/backend` folder. Live parser accuracy can be tested via `python run_live_accuracy.py`.

## 5. Current State
- All 32+ scrapers are 100% operational with intercept and DOM fallback logic.
- Live backend parsers have a 23/23 pass rate.
- Aggregator and ER engines are stable and guarded by tests.

Read `COMMON_MASTER_ARCHITECTURE.md` and `TRUECOST_DECISIONS.md` for historical architectural decisions.

Good luck! You are working on an elite, fully-functioning distributed scraper and aggregator system.
