# TrueCost provider connection broker contract

Connected Accounts supports official provider authorization only. The broker owns provider-specific OAuth clients and stores any provider access/refresh tokens in its server-side secret store. It must never return passwords, OTPs, WebView cookies, access tokens or refresh tokens to the TrueCost mobile app.

## Configuration

- `PROVIDER_CONNECTION_BROKER_URL=https://connections.example.com`
- `PROVIDER_CONNECTION_BROKER_SECRET=<at-least-32-random-characters>`

TrueCost calls the broker at:

`GET {BROKER_URL}/authorize?provider={provider_id}&state={opaque_state}&redirect_uri=truecost%3A%2F%2Fprovider-connect`

The broker completes the provider's approved OAuth flow and redirects the system browser to `truecost://provider-connect` with:

- `provider`: canonical provider ID
- `state`: the unchanged opaque TrueCost state
- `result`: `connected`, `expired`, or `cancelled`
- `account_label`: optional masked label only
- `expires_at`: optional UTC ISO-8601 timestamp
- `signature`: lowercase HMAC-SHA256 hex digest

The signed canonical text is:

`provider|state|result|account_label|expires_at`

Empty optional values are represented by empty strings. `expires_at` is normalized to UTC ISO-8601 form before signing. The mobile app forwards this result to `POST /api/v1/provider-connections/complete`; the backend verifies ownership, attempt expiry, one-time use and signature before persisting connection metadata.

Disconnecting removes TrueCost metadata. A production broker should also provide provider-token revocation and users should retain the ability to revoke TrueCost from the provider's own account-security page.
