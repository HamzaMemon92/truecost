# TrueCost Production Completion Plan

## Summary

Convert the current mobile/backend system into a production-ready platform while preserving these immutable boundaries:

- `ScraperManager.tsx` and `AgentSearchScreen.tsx` remain untouched.
- `/api/v1/aggregator/ingest` remains the trusted live-data entry point.
- All 32 providers remain recognized, but each is enabled publicly only after verification.
- Connected Accounts uses official OAuth only—never passwords, OTPs, WebView cookies, or reusable browser sessions.
- Release scope is mobile + backend; web parity follows separately.

Production foundation: Python 3.12, FastAPI, PostgreSQL 16, Redis 7, Celery workers/Beat, Docker, GitHub Actions, Expo EAS, OpenTelemetry and Sentry.

## Implementation Sequence

### 1. Canonical provider platform

- Replace duplicated provider arrays with one canonical provider manifest containing the 32 provider IDs, aliases, categories, handoff capabilities, freshness SLA, source mode and rollout state.
- Generate the backend ingest allowlist and mobile compatibility export from that manifest. CI fails if generated provider files drift.
- Preserve `/aggregator/ingest` payload compatibility and dynamically validate providers and aliases against the canonical catalog.
- Add operational states: `catalogued`, `testing`, `verified`, `degraded`, `disabled`; never interpret “catalogued” as live.
- Fix known drift:
  - Choose Cleartrip as the canonical fourth Flights provider and remove EaseMyTrip preview drift.
  - Add explicit Hotels provider metadata only when the corresponding result contract is enabled.
  - Separate Swiggy Food and Swiggy Instamart identities while allowing one Swiggy account-connection family.
- Production must fail closed: direct-provider errors return unavailable/partial state and never silently fall back to mock products.
- Keep development previews behind environment flags; Flights and Hotels cannot appear as live in production until their backend contracts return verified data.

### 2. Database, workers and reliable notifications

- Introduce Alembic and create a reviewed baseline migration for the complete existing schema, followed by revisions for provider operations, OAuth vault metadata, outbox delivery and health events.
- Production startup stops using `Base.metadata.create_all`; readiness fails when the database revision is behind Alembic head.
- Use PostgreSQL for development integration/staging/production. SQLite remains limited to fast unit tests.
- Replace the in-process price-watch thread with:
  - Celery worker for price evaluation, push delivery and receipt reconciliation;
  - Celery Beat for periodic scheduling;
  - Redis for task transport, distributed locks and shared rate limits.
- Preserve threshold-crossing and observation idempotency. Create notifications and an outbox row atomically, then deliver asynchronously with bounded retries and dead-letter status.
- Poll Expo receipts, deactivate invalid device tokens and retain delivery diagnostics without personal message content.
- Add account-scoped cleanup for SecureStore metadata, push devices, watches, OAuth connections and broker credentials during logout/account deletion.

### 3. Connected Accounts and verified personalization

- Deploy a separate `provider-broker` container implementing the existing signed callback contract.
- Store official provider access/refresh tokens only inside the broker vault using envelope encryption, key versions and a restricted PostgreSQL role. The API and mobile app never receive them.
- Implement PKCE, one-time state, short expiry, exact redirect allowlisting, callback signatures, token refresh, revocation and audit events.
- Initial eight candidates: Amazon, Flipkart, Swiggy, Zepto, Blinkit, Uber, Ola and Rapido.
- Because official credentials are expected gradually:
  - all eight begin as `pending_approval`;
  - a provider becomes connectable only after credentials, approved scopes, redirect registration and contract tests exist;
  - unavailable providers retain comparison functionality without showing a misleading Connect action.
- Add a provider-adapter interface for authorization, refresh, revocation, masked identity and official benefit retrieval.
- Persist only masked account labels and connection status in the TrueCost database and SecureStore.
- Add verified `provider_account_benefits` observations containing provenance, eligibility, terms, observation time and expiry. The deterministic backend may apply these benefits after ingestion; the protected engine is not modified.
- Disconnect and account deletion must revoke broker tokens before deleting metadata. Failed revocation enters a retry queue and remains visible operationally.
- Replace temporary monograms with provider-approved local logo assets as each agreement is approved; do not load logos through tracking CDNs.

### 4. Production security, mobile delivery and operations

- Add strict environment profiles for development, test, staging and production.
- Production configuration must require PostgreSQL, Redis, a strong JWT secret, restricted CORS origins, one fully configured non-console SMS provider, Expo/EAS, HTTPS API origin, encryption keys and broker secrets.
- Replace wildcard CORS with explicit origins; add trusted-host validation, request IDs, security headers and a consistent error envelope.
- Add Redis-backed limits for OTP requests/verifications, login, refresh, ingestion, optimization, support reports and OAuth starts.
- Extend account reauthentication so phone-authenticated users can export/delete their account using a short-lived verified reauthentication token rather than an unavailable password.
- Redact phone numbers, emails, OAuth state, tokens, addresses and provider identifiers from structured logs.
- Add:
  - `/health/live` for process health;
  - `/health/ready` for database, Redis, migration and worker dependencies;
  - `/api/v1/providers` for public provider capability/status metadata;
  - admin-only provider health, ingestion freshness, worker, cache and notification diagnostics.
- Keep `/commerce/catalog/categories` as a backward-compatible projection of the canonical provider API.
- Add Expo EAS development, preview and production profiles with environment-specific API/EAS values, channel separation and controlled OTA runtime versions.
- Make Connected Accounts’ SecureStore cache account-scoped and clear it on logout, account switching and deletion.
- Use explicit loading, offline, partial-provider, expired-session and unavailable-integration states throughout mobile.
- Add Dockerfiles and local Compose services for API, worker, Beat, broker, PostgreSQL and Redis. Production uses managed PostgreSQL/Redis and managed TLS.
- Add OpenTelemetry traces/metrics, Sentry backend/mobile error reporting, JSON logs and alerts for ingestion failure rate, stale providers, worker backlog, OAuth refresh failure and push delivery failure.

### 5. CI/CD, verification and rollout

- GitHub Actions gates:
  - Ruff, Python type checks and complete pytest suite;
  - Alembic upgrade from empty database and previous production revision;
  - PostgreSQL integration tests;
  - mobile TypeScript, component tests, Expo Doctor and production export;
  - protected-file hash regression;
  - provider-manifest drift check;
  - secret scanning, dependency audit and container scanning.
- Add React Native Testing Library coverage and Maestro E2E flows for auth, OTP, restored sessions, profile, location, cart, watch alerts, push registration and Connected Accounts.
- Provider verification requires contract normalization, provenance, handoff validation, timeout/partial-failure handling and production-like sample checks before changing `testing` to `verified`.
- Add load tests for authentication, ingestion, dashboard, optimization and worker throughput; verify duplicate tasks cannot create duplicate notifications.
- Add security tests for OAuth state replay, callback forgery, cross-user completion, token leakage, redirect manipulation, OTP abuse and account deletion.
- Release through development → staging → production:
  1. migrate and validate schema;
  2. deploy Redis/workers and shadow-run price watches;
  3. enable outbox push delivery;
  4. deploy canonical provider catalog with every provider initially non-live;
  5. enable verified ingestion providers individually;
  6. enable OAuth adapters individually after approval;
  7. release EAS preview, complete smoke tests, then promote the same artifact.
- Roll back application containers independently; database migrations must be backward-compatible for one release.
- Enable PostgreSQL point-in-time recovery with a 15-minute maximum RPO and perform a documented restoration test before public launch.

## Public Interfaces and Data Contracts

- `GET /api/v1/providers`: canonical categories, providers, source mode, rollout state, connection availability, freshness and handoff capability.
- Existing `/api/v1/provider-connections` routes remain; completion is accepted only after broker signature and attempt ownership validation.
- Internal broker contracts cover authorize, callback, refresh, revoke and verified-benefit retrieval.
- Notifications use transactional outbox and receipt states: `pending`, `sent`, `delivered`, `retrying`, `failed`, `invalid_device`.
- All API errors follow `{ "error": { "code", "message", "request_id", "details?" } }`.
- No mock or development-preview response may carry a `live`, `verified`, or authoritative-price designation.

## Acceptance Criteria

- Exactly 32 canonical provider identities exist with no backend/mobile/runtime drift.
- Production can run with zero verified providers without fabricating results; provider availability is communicated clearly.
- Every trusted ingest result is persisted with user/session/provider provenance.
- Price alerts are generated once per threshold crossing and delivered within five minutes of a trusted observation.
- Connected Accounts cannot become connected through a mobile-only action, forged callback or replay.
- No OAuth credential, third-party cookie, OTP, full payment identifier or unmasked account identity appears in mobile storage, API responses or logs.
- Production schema reaches Alembic head from an empty database and from the current schema.
- All backend, mobile, migration, E2E, security and protected-file gates pass.
- Staging backup restoration, worker failover, provider degradation and mobile offline recovery are demonstrated before production promotion.

## Assumptions and Defaults

- Docker-first portable deployment is the selected infrastructure strategy.
- Providers use a phased verified rollout; being listed does not mean being live.
- Official OAuth credentials and approvals arrive gradually, so no provider is falsely enabled at initial deployment.
- The protected ingestion engine remains the sole core producer of provider search observations.
- Mobility remains explicitly estimated until a verified live provider contract exists.
- Flights and Hotels remain development-only or hidden until verified backend data replaces previews.
- Mobile is the primary release target; web API parity is preserved, but web UI migration is a later release.
- Published Lovable-connected Git history will not be rewritten.
