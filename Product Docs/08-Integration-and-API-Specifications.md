# 08 — Integration / API Specifications

**Product:** Sentinel AML
**Scope note:** The prototype has **no external integrations** — everything runs against the mock dataset. This document specifies (a) the internal tool-layer "API" the AI agent actually calls, and (b) the external integrations a production version would need, clearly separated.

---

## 1. Internal Tool Layer (built and used in the prototype)

These are plain Python functions in the prototype; optionally exposed as MCP tools so the architecture matches the product story. Each has a fixed schema so the grounding validator can check every call.

| Tool | Input | Output | Notes |
|---|---|---|---|
| `get_customer_profile(customer_id)` | customer_id | Customer record | Read-only |
| `get_account(account_id)` | account_id | Account record incl. is_internal | Read-only |
| `get_transaction_history(account_id, window)` | account_id, date range | List of transactions | Used for baseline calc |
| `compute_baseline(account_id)` | account_id | Trailing 6-month average/median credit and debit | Deterministic, code-only |
| `trace_fund_flow(txn_id, hops, time_window)` | trigger txn_id, max hops, window | Ordered chain of downstream transactions/accounts | Deterministic graph trace |
| `get_relationships(account_id)` | account_id | List of relationship records | Read-only |
| `get_prior_alerts_and_cases(customer_id_or_account_id)` | id | List of prior alerts/cases | Read-only |
| `get_documents(customer_id, case_id)` | ids | List of document summaries | Read-only |
| `get_playbook(scenario_id)` | scenario_id | Ordered list of next-step entries | Used to ground "next steps" |
| `evaluate_rules(transaction_feed_window)` | feed window | List of fired rule+alert candidates | Trigger Engine only — not called by the AI agent |

**Authentication:** none required in-prototype (single local process). **Failure handling:** any tool call that raises an error is caught, logged to AuditLog with `actor=system`, and surfaced to the agent as an explicit "data unavailable" result rather than silently retried or guessed around.

## 2. External Integrations — Target State Only (NOT built for this capstone)

| System | Purpose | Likely protocol | Notes |
|---|---|---|---|
| Core banking / transaction ledger | Real transaction feed | Batch file or streaming API (bank-specific) | Replaces mock Transaction table |
| KYC / CKYC / PAN verification | Real customer verification | REST API, licensed integration | Replaces mock Customer.kyc_status |
| Credit/AML screening providers | Sanctions/PEP/adverse media (if the product scope later expands to screening) | REST API, licensed integration | Not part of the frozen use case; noted for roadmap only |
| Case management system | System of record for case status | REST API or DB integration | Prototype's case queue stands in for this |
| Document management system | Real supporting documents | REST API / file store | Replaces mock Document table |
| LLM provider | Investigation Agent reasoning + report generation | REST API (chat/completions with tool-calling, JSON-schema output) | **This is the one real external call the prototype makes** — see below |

## 3. The One Real External Call: LLM API

| Item | Detail |
|---|---|
| Direction | Outbound only — the app calls an LLM provider's API |
| Data sent | Only mock/fictional data — no real customer data ever leaves the environment |
| Auth | API key held by the team, not committed to any shared repo; open item — see [12-Meeting-Notes-and-Decisions.md](12-Meeting-Notes-and-Decisions.md) for who owns the key/budget |
| Failure handling | On error/timeout, the app falls back to a **cached report** for the demo case (F12 in [02-PRD](02-Product-Requirements-Document.md)) rather than failing the screen |
| Expected payload shape (conceptual) | System prompt (fixed investigation procedure + guardrail instructions) + tool-call results + request for a structured JSON report matching the schema in [07-Data-Requirements.md](07-Data-Requirements.md) `AIReport.report_json` |

## 4. Why No Other Integrations Are Built

Building against real bank systems is out of scope by definition (fictional data, academic capstone, no production access). Documenting the target integrations here — rather than omitting them — lets the blueprint show build/buy/partner reasoning for each (see the blueprint's build/buy/partner matrix) without pretending the prototype connects to them.
