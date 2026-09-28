# 06 — Technical Architecture Document

**Product:** Sentinel AML
**See also:** [Flowchart-1-End-to-End-Data-Flow.md](Flowchart-1-End-to-End-Data-Flow.md), [08-Integration-and-API-Specifications.md](08-Integration-and-API-Specifications.md)

---

## 1. Architecture Principle

**Compute deterministically, reason with the LLM, verify before display.**

- All numbers (baselines, totals, velocity, fund-flow chains) are computed by plain code, never by the LLM.
- The LLM only interprets computed results, drafts findings/questions/next steps, and must cite the record IDs it used.
- A grounding validator checks every AI output against the underlying data before it reaches the UI; unsupported claims are rejected or downgraded to "Inferred."

## 2. System Layers

| Layer | Responsibility | Technology (prototype) | Technology (target/production framing) |
|---|---|---|---|
| Data layer | Stores mock customer/account/transaction/relationship/alert/case/document/playbook records | CSV/Excel loaded into SQLite/DuckDB | Core banking, KYC system, case management DB, document store (real integrations — out of scope) |
| Monitoring layer | Rule-based Trigger Engine (R1, R2) scanning the transaction feed | Python scheduled/batch job over the mock feed | Real-time or near-real-time transaction monitoring platform (existing system in a real bank — not rebuilt here) |
| Tool layer | Deterministic functions: baseline calc, fund-flow trace, relationship lookup, prior-alert/case lookup, document lookup | Python functions, optionally wrapped as an MCP tool server | Same, backed by real source-system APIs |
| AI layer | Investigation Agent: selects tools, drafts structured report, cites sources | LLM with tool-calling + JSON-schema output | Same, with potential move to a multi-agent split (see phased design below) |
| Validation layer | Grounding validator: citation check, number check, forbidden-wording check | Python | Same, potentially with a second-model "critic" pass |
| Application layer | Case queue, Investigation Workspace, Human Decision Panel, Escalation Queue, Audit Log, Admin | Streamlit (single-tier, fastest path to a working prototype) | Web app: React/Next.js frontend + FastAPI (or similar) backend + auth service |
| Governance layer | Audit log, role-based views | Append-only log table + role selector (mock auth) | Immutable audit store, real RBAC/IAM, SIEM integration |

**Why Streamlit for the prototype, not a "real" web stack:** given the team's timeline (see [14](14-Delivery-Plan-and-Milestone-Roadmap.md)), Streamlit gets a working, demoable product-shaped UI (multi-page, stateful, role-aware) built fastest. The architecture is still designed in layers so it maps cleanly onto a production frontend/backend split later — this is noted explicitly so evaluators see the target architecture, not just the shortcut.

## 3. Component Diagram (text form; see also the end-to-end flowchart)

```
Digital Channel (browser)
   -> Sentinel AML App (Streamlit)
        -> Case Queue / Dashboard module
        -> Investigation Workspace module
        -> Human Decision module
        -> Escalation / Compliance module
        -> Admin module
   -> Application talks to:
        -> Data Access Layer (SQLite/DuckDB over mock CSVs)
        -> Trigger Engine (rule evaluation service)
        -> AI Investigation Agent (LLM + tool layer)
        -> Grounding Validator
        -> Audit Log service
```

## 4. Why an Agent, Not a Chatbot

A chatbot answers one question at a time and puts the burden of asking the right questions on the user. The Investigation Agent instead runs a **fixed investigation procedure** (profile check → transaction/baseline analysis → fund-flow trace → relationship check → history check → evidence assembly → report), calling tools in that sequence, and always produces the same structured report shape. The user never has to "prompt it correctly" — this is what makes it a product feature, not a chat window bolted onto the case screen.

## 5. Phased Agent Design

- **Prototype (now):** one Investigation Agent orchestrating all tool calls.
- **Roadmap (documented, not built for the capstone):** split into six specialist agents — Alert Triage, Transaction Investigation, Relationship, Customer/KYC, Evidence, Investigation Summary — as originally proposed by the team. See [14-Delivery-Plan-and-Milestone-Roadmap.md](14-Delivery-Plan-and-Milestone-Roadmap.md). The single-agent prototype is deliberately built so this split is additive, not a rewrite: each future agent takes over one existing tool-call sequence.

## 6. Security & Guardrail Notes (architecture-level; full list in [10-Non-Functional-Requirements.md](10-Non-Functional-Requirements.md))

- AI tools are **read-only** against the data store.
- Free-text fields (transaction reference, document text) are treated as **untrusted input**; the agent's system prompt and the validator both guard against embedded instructions (prompt injection).
- No customer-identifying real data is used anywhere; the dataset is synthetic by construction (see [07-Data-Requirements.md](07-Data-Requirements.md)).
- Every AI action and human decision writes to the audit log — this is treated as a non-optional side effect of the workflow, not a bolt-on.

## 7. Deployment (prototype)

Single machine or shared cloud dev environment running the Streamlit app and a local SQLite/DuckDB file; LLM calls go to a hosted API. No production deployment, container orchestration, or multi-environment setup is in scope for the capstone (see [10-Non-Functional-Requirements.md](10-Non-Functional-Requirements.md) for what a production deployment would additionally require).
