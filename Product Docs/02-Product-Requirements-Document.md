# 02 — Product Requirements Document (PRD)

**Product:** Sentinel AML
**Related:** [01-Project-Vision-and-Business-Case.md](01-Project-Vision-and-Business-Case.md), [05-Functional-Requirements-and-Use-Case-Document.md](05-Functional-Requirements-and-Use-Case-Document.md)

---

## 1. Product Overview

Sentinel AML has two halves that together make it a product rather than a single AI feature:

1. **Detect** — a rule-based Trigger Engine continuously scans transaction activity and raises alerts when defined conditions are met.
2. **Investigate** — an AI-assisted workspace turns each alert into a structured, evidence-linked case for a human investigator to review and decide.

## 2. Features

| ID | Feature | Description | Priority |
|---|---|---|---|
| F1 | Login / role landing | Role-based entry (Investigator, Team Lead, Compliance, Admin); mock auth for prototype | Must |
| F2 | Case queue dashboard | Landing page after login: open cases, priority, alert type, SLA/age, quick filters | Must |
| F3 | Trigger engine | Background rule evaluation over mock transaction feed; generates alerts with rule ID + threshold values shown | Must |
| F4 | Case intake | Alert becomes a case; claimed by an investigator | Must |
| F5 | Investigation workspace | Case header, alert summary, transaction timeline, fund-flow/relationship view, AI findings panel, investigation questions, recommended next steps | Must |
| F6 | Evidence status tagging | Every AI finding tagged Verified / Inferred / Missing / Conflicting with citations | Must |
| F7 | Human decision panel | Separate UI region; actions = request info / add evidence / escalate / close; rationale mandatory | Must |
| F8 | Audit log | Immutable, per-case and system-wide log of AI actions and human decisions | Must |
| F9 | Escalation / compliance queue | Escalated cases appear in a Compliance role view | Should |
| F10 | Admin rule configuration (light) | View/adjust the two trigger rule thresholds; view/edit playbook | Should |
| F11 | Twin-case scenario library | Pre-loaded suspicious case (C1) and legitimate case (C2) sharing the same trigger, for demo and testing | Must |
| F12 | Cached / live report toggle | AI report can replay from cache (demo reliability) or regenerate live | Should |
| F13 | Second trigger scenario (velocity/structuring) | Additional rule + case for variety | Could |
| F14 | Network graph visualization | Visual account/fund-flow graph in the workspace | Could |

MoSCoW note: **Must** = required for capstone demo/acceptance; **Should** = strengthens the demo, build if time allows; **Could** = stretch, defer to roadmap if short on time. See [14-Delivery-Plan-and-Milestone-Roadmap.md](14-Delivery-Plan-and-Milestone-Roadmap.md).

## 3. Business Rules

| # | Rule |
|---|---|
| BR1 | The AI never sets, changes, or recommends a final legal/criminal determination. It surfaces indicators and evidence status only. |
| BR2 | Every AI finding must cite the record(s) it is based on. A finding with no citation is not permitted in the output. |
| BR3 | "Verified" may only be used when the underlying data directly supports the claim; anything inferred from multiple data points is "Inferred," never "Verified." |
| BR4 | Case disposition (close/escalate) is a human action only, and requires a written rationale before it can be recorded. |
| BR5 | The Trigger Engine is rule-based only — no AI/LLM involvement in raising an alert (keeps detection deterministic and explainable). |
| BR6 | AI tools are read-only against the mock data store. The AI cannot alter alert status, transaction records, or KYC data. |
| BR7 | Recommended next steps must cite a playbook entry (mock internal procedure), never be generated from the model's unstated assumptions about regulation. |
| BR8 | All data, customers, accounts, and transactions are fictional; the product must visibly label itself as a prototype using mock data on every screen. |

## 4. Out-of-Scope Items (explicit)

- Real-time payment blocking or transaction interdiction.
- Regulatory report (STR/CTR) generation or submission.
- Full KYC onboarding / remediation workflow.
- Automatic case closure without human action.
- Any claim that the product performs a legal or definitive AML determination.
- Production identity/access management, encryption-at-rest infrastructure, and security certification (documented as target-state requirements only — see [10-Non-Functional-Requirements.md](10-Non-Functional-Requirements.md)).

## 5. Assumptions

- One institution, one jurisdiction context (India) for terminology and illustrative scenario framing; no jurisdiction-specific legal claims are made (see [13-Risks-Assumptions-Dependencies-Constraints.md](13-Risks-Assumptions-Dependencies-Constraints.md)).
- A single LLM provider with tool-calling and JSON-schema output is available to the team (provider/key TBD by team — open item, see Meeting Notes).
- Prototype runs locally / on a shared demo machine; no production hosting required.

## 6. Dependencies

- Mock dataset (customers, accounts, transactions, relationships, alerts, documents, playbook) — see [07-Data-Requirements.md](07-Data-Requirements.md).
- LLM API access — see [08-Integration-and-API-Specifications.md](08-Integration-and-API-Specifications.md).

## 7. Release Criteria

See [11-Acceptance-Criteria-and-Definition-of-Done.md](11-Acceptance-Criteria-and-Definition-of-Done.md).
