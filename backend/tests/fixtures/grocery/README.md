# Grocery Provider Fixture Harness

This folder stores provider payload fixtures used to test connector parsing and
TrueCost comparison correctness without calling live provider networks.

## Fixture Types

- `synthetic`: hand-built payloads shaped like known provider responses. These
  prove the regression harness works, but they do not prove live provider
  behavior.
- `captured`: raw payloads exported from a real device/provider session. These
  can be used as evidence for provider-specific fixes.

## Required Metadata

Each fixture must be registered in `manifest.json` with:

- provider
- category
- query
- pincode
- latitude and longitude
- captured_at
- source, either `synthetic` or `captured`
- expected product/offers
- notes comparing against the real provider app when available

## Adding A Real Capture

1. Search from the target location in Expo Go.
2. Export the raw `SEARCH_SUCCESS` payload before backend normalization.
3. Save it under `backend/tests/fixtures/grocery/{provider}/`.
4. Add a manifest entry with `source: "captured"`.
5. Record what the real provider app showed for the same location.
6. Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_provider_fixture_harness.py
```

Do not mark a provider-specific production fix as proven until at least one
captured fixture covers that provider/query/location behavior.
