# Common Master North-Star Architecture

This document defines the **Common Master North-Star Architecture**. It serves as the target blueprint for all domain implementations (Grocery, Rides, Travel, etc.). It establishes explicit boundaries across the intelligence plane, data/capability plane, and control plane.

**Status:** 🟢 Approved as the north-star architecture

## Core Design Principles

1.  **Evidence → Verify → Calculate → Optimize → Explain:**
    Data must be normalized, deduplicated, and explicitly verified *before* applying optimization, payment intelligence, and decision ranking. LLM synthesis operates only on deterministic, verified outcomes.
2.  **Separate Payment Intelligence from Ranking:**
    Payment intelligence (rewards, cashback, fees, effective value) is a distinct calculation step that occurs before the final decision/optimization engine.
3.  **Deep Agents are a Capability, not the Architecture:**
    The complex path relies on a Research/Planning subgraph where deep reasoning (e.g., Deep Agents) is an optional implementation detail, not the overarching system structure.
4.  **A2A is for External Agents Only:**
    Agent-to-Agent (A2A) communication is strictly reserved for interactions with external, independent agents. Internal category workflows use standard subgraphs and specialist agents.
5.  **ONDC is a Network Boundary:**
    ONDC acts as a distinct network/protocol integration path (BAP Adapter → Network), strictly separate from direct API providers.

---

## 1. Intelligence, Data, and Control Flow

```text
                              USER
                                │
                                ▼
                     WEB / MOBILE CATEGORY PAGE
                                │
                                ▼
                            API / BFF
                                │
                                ▼
                     CONTEXT / AUTH / SESSION
                                │
                                ▼
                        MASTER LANGGRAPH
                                │
                                ▼
                        TASK ANALYSIS
                                │
                                ▼
                      EXECUTION POLICY
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
              SIMPLE        MODERATE        COMPLEX
                 │              │              │
                 ▼              ▼              ▼
          Deterministic     Specialist     Research /
             Tools            Agent        Planning
                                │              │
                                └──────┬───────┘
                                       ▼
                                   MCP CLIENT
                                       │
                                       ▼
                               DOMAIN MCP SERVER
                                       │
                         ┌─────────────┴─────────────┐
                         ▼                           ▼
                  DIRECT PROVIDERS              NETWORKS
                         │                           │
                  Provider Adapter              ONDC BAP
                         │                           │
                         └─────────────┬─────────────┘
                                       ▼
                              COMMON DOMAIN DATA
                                       │
                                       ▼
                             NORMALIZE / MATCH
                                       │
                                       ▼
                               EVIDENCE / VERIFY
                                       │
                                       ▼
                              CONSTRAINT ENGINE
                                       │
                                       ▼
                            PAYMENT INTELLIGENCE
                                       │
                                       ▼
                             DECISION / OPTIMIZE
                                       │
                                       ▼
                              LLM SYNTHESIS
                                       │
                                       ▼
                              WEB / MOBILE UI
```

---

## 2. High-Risk Action Execution (Control Plane)

```text
                 HIGH-RISK ACTION
                       │
                       ▼
                Policy + AuthZ
                       │
                       ▼
                User Confirmation
                       │
                       ▼
                Execution Service
                       │
                       ▼
                Provider / Network
                       │
                       ▼
                 Verification
```

---

## 3. Future External Agent Boundary (A2A)

```text
             FUTURE EXTERNAL AGENT
                       │
                Agent Registry
                       │
                Trust / Policy
                       │
                   A2A Gateway
                       │
                 Remote Agent
```

---

## 4. Platform Foundation (Adopt as Needed)

These components represent the future infrastructure required to operate Common Master at scale. They should be adopted progressively as product capabilities demand, rather than being deployed prematurely.

**NOW:**
- Postgres
- Redis
- Secrets
- Observability

**LATER:**
- Temporal
- Event Bus
- Service Mesh
- Kubernetes
