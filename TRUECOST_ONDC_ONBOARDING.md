# ONDC Buyer App (BAP) Onboarding Checklist

This document tracks the formal engineering and network onboarding process for integrating TrueCost with the ONDC network as a Buyer Application (BAP). 

The goal is to move securely from our hardened foundation to production via ONDC's staged certification process.

> [!CAUTION]
> **Production Guardrail**
> The `ONDC_ENV=live` configuration must remain strictly **BLOCKED** in the application until the certification and production credentials phases are completely verified.

## Phase 1: Identity & Staging Foundation
- [ ] **BAP Identity Definition**
  - Define `bap_id` (e.g., `ondc.truecost.ai`)
  - Define `bap_uri` (e.g., `https://api.truecost.ai/ondc/callback`)
- [ ] **Cryptographic Keys (Ed25519)**
  - Generate signing key pair (Ed25519)
  - Generate encryption key pair (X25519)
  - Securely store private keys in Vault/Secrets Manager
- [ ] **Staging Registry Entry**
  - Register `bap_id` and public keys on the ONDC Staging Registry
  - Obtain `ukId` (Unique Key ID) from the registry
- [ ] **Staging Gateway Access**
  - Obtain ONDC Staging Gateway URLs and network endpoints
  - Configure `ONDC_ENV=staging` backend environments

## Phase 2: Implementation & Networking
- [ ] **Callback URLs (Webhook Endpoint)**
  - Deploy public-facing endpoints to receive unsolicited POST callbacks (`/on_search`, `/on_select`, etc.)
  - Ensure payload signature verification middleware is active on incoming callbacks
- [ ] **HTTP Detached Signatures**
  - Implement request signing logic (libsodium/PyNaCl) for outbound requests
  - Implement signature verification for incoming gateway callbacks
- [ ] **RET10 Domain Configuration**
  - Ensure ONDC search payloads strictly conform to the `RET10` (Grocery) specification
  - Validate fulfillment mapping and categorical constraints

## Phase 3: Staging Execution (RET10 Discovery)
- [ ] **Trigger Staging Search**
  - Broadcast `/search` via Staging Gateway
  - Receive HTTP 200 (ACK) from Gateway
- [ ] **Process Staging Callbacks**
  - Receive and parse asynchronous `/on_search` payloads from Seller Apps (BPPs)
  - Successfully map ONDC payload to TrueCost `CanonicalGroceryItem` schemas
- [ ] **End-to-End Staging Validation**
  - Complete a test cycle: Search → Select → Init → Confirm → Status

## Phase 4: Certification & Qualification
- [ ] **Log Capture for Certification**
  - Capture all request/response JSON payloads and headers
- [ ] **ONDC Qualification Process**
  - Submit staging logs to ONDC verification team
  - Complete functional and security review
  - Remediate any non-compliant schema mappings

## Phase 5: Pre-Production & Production
- [ ] **Preprod Registration**
  - Move to Pre-Production environment
  - Conduct pilot/closed-beta searches against real sellers on the preprod network
- [ ] **Production Approval**
  - Receive formal production approval from ONDC
  - Register `bap_id` on the Live Production Registry
  - Upload Live public keys
- [ ] **Live Activation**
  - Unlock `ONDC_ENV=live` within TrueCost configuration
  - Monitor production telemetry and error rates

---
*Note: This checklist bridges the gap between our internal system architecture and external network compliance.*
