# TrueCost production runbook

## Release invariant

`backend/app/provider_catalog.json` is the only provider identity source. Run
`python backend/scripts/generate_provider_catalog.py --check` before release.
Every provider begins non-live. Operations may promote one identity from
`catalogued` to `testing` and then `verified` only after normalization,
provenance, handoff, timeout and partial-failure contract tests pass.

## Deployment order

1. Build immutable API, worker, Beat and broker container images.
2. Back up PostgreSQL and record the current Alembic revision.
3. Run `alembic upgrade head` as the migration role.
4. Start Redis, workers and Beat. Shadow-run price evaluation with delivery disabled.
5. Start API and require `/health/live` and `/health/ready` to pass.
6. Enable outbox delivery, then enable verified ingestion providers individually.
7. Enable an OAuth adapter only after official credentials, redirect registration,
   approved scopes and its contract suite exist.
8. Promote the already-tested EAS preview artifact to the production channel.

Application containers can roll back independently. Schema changes must remain
backward-compatible for one release; never downgrade a production database as an
application rollback mechanism.

## Alerting

Page the on-call engineer for provider ingestion failure-rate spikes, freshness
SLA breach, Celery queue age above two minutes, OAuth refresh/revocation failure,
notification outbox retry growth, Expo invalid-device spikes, readiness failure,
or PostgreSQL/Redis saturation. Logs must not include emails, phone numbers,
addresses, tokens, OAuth state, full account labels or personal notification text.

## Backup and restoration

Production PostgreSQL must have point-in-time recovery with a maximum 15-minute
RPO. Before launch and quarterly thereafter:

1. Restore the latest full backup plus WAL into an isolated staging project.
2. Stop at a timestamp selected inside the previous 15 minutes.
3. Run `alembic current`, `/health/ready`, row-count checks and ownership smoke tests.
4. Run a watch observation twice and confirm only one threshold-crossing notification.
5. Record restore start/end, recovery point, revision, checksums and approver.
6. Destroy the isolated restore using the cloud provider's recoverable workflow.

## Degradation drills

- Stop one worker and verify queued jobs are claimed by another worker.
- Disable Redis connectivity and confirm readiness fails without fabricated results.
- Mark a verified provider degraded and confirm public/mobile status changes.
- Return one provider timeout during a comparison and verify a partial-provider state.
- Revoke an Expo token and confirm receipt reconciliation deactivates the device.
- Replay an OAuth state and verify both broker and API reject it.

## Secrets and roles

Use deployment-managed secrets for JWT, SMS providers, Expo, broker HMAC, OAuth clients and
Fernet key versions. The broker database role alone receives CRUD on
`broker_vault_credentials`; the API role must not receive access. Rotate by placing
the new Fernet key first, retaining the old decrypt-only key during re-encryption,
then removing it after verification.

## OTP delivery rollout

1. Complete Indian DLT entity, sender and exact login-template approval before enabling production SMS.
2. Configure `SMS_PROVIDER=msg91` with `MSG91_AUTH_KEY` and `MSG91_TEMPLATE_ID`.
3. Optionally configure `SMS_FALLBACK_PROVIDER=twofactor` with `TWOFACTOR_API_KEY` and the exact approved `TWOFACTOR_TEMPLATE_NAME`.
4. Keep Twilio configured only where its approved sender and destination coverage are required.
5. Send staging OTPs to test numbers on every intended carrier, then verify expiry, resend throttling, attempt limits and vendor failure behavior.
6. Confirm logs contain neither the phone number, code nor provider credentials. `SMS_PROVIDER=console` must never be enabled outside development/test.

The backend generates and HMAC-hashes the code; providers only deliver it. Failover is attempted after a definite rejection or connection failure, but not after an ambiguous read/write timeout that might otherwise send duplicate messages.
