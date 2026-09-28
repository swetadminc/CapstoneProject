# 01 — Project Vision & Business Case

**Product:** Sentinel AML — AI-Assisted AML Detection & Investigation Platform
**Tagline:** From transaction to trigger to traceable decision.
**Document owner:** [assign]
**Status:** Draft for team review — capstone academic project, fictional data only

---

## 1. Purpose

Sentinel AML is an end-to-end product, not a chatbot. It watches a bank's transaction activity, automatically **detects** patterns that warrant investigation, and gives an AML investigator an **AI-assisted workspace** to investigate the case — evidence gathered, connections traced, red flags identified, and a structured report drafted — while the human investigator retains every decision.

It has three moving parts a reader should picture immediately:
1. **A trigger.** Something happens in the transaction feed that the system is watching for.
2. **A landing experience.** The investigator opens the product and sees a queue of cases, not a blank chat box.
3. **An investigation.** The AI assembles the evidence; the human decides.

## 2. Business Problem

Financial institutions must review transaction-monitoring alerts for possible money laundering. Today this review is manual: an investigator opens 6–8 separate systems (core banking, KYC, case management, screening tools) to piece together the customer's history, trace where money went, check for related parties, and write up findings. This is slow, inconsistent between investigators, and hard to audit after the fact.

Two consequences of the status quo:
- **Investigation backlog and inconsistent quality** — investigators spend most of their time compiling evidence rather than applying judgment.
- **Weak traceability** — when a regulator or auditor asks "how was this decided," the answer is scattered across systems and inboxes.

## 3. Business Case (why build this)

| Driver | Current state (assumption, to validate with real data if this goes beyond the capstone) | Target state |
|---|---|---|
| Time per alert | Investigator manually compiles evidence across systems — assumed several hours per moderately complex case | AI assembles the evidence pack in minutes; investigator spends time on judgment, not compilation |
| Consistency | Write-ups vary by investigator | Structured report format every time, same evidence categories |
| Auditability | Evidence trail reconstructed after the fact from emails/notes | Every AI action and human decision logged automatically as it happens |
| Missed connections | Related accounts / prior alerts easy to miss under time pressure | System explicitly traces fund flow and relationships, and lists what is missing |

**All time/effort figures above are illustrative assumptions for the capstone, not measured data**, and are flagged as such throughout this pack (see [13-Risks-Assumptions-Dependencies-Constraints.md](13-Risks-Assumptions-Dependencies-Constraints.md)).

## 4. Vision Statement

> Give every AML investigator a case that already has its evidence gathered, its connections traced, and its open questions written down — so their first hour on a case is spent deciding, not searching.

## 5. Who This Is For

See [03-User-Personas-and-Stakeholders.md](03-User-Personas-and-Stakeholders.md) for full detail. In short: AML Investigators (primary users), Investigation Team Leads, Compliance Officers, and a System Admin role for rule/threshold configuration.

## 6. Scope of This Capstone

### In scope
- A rule-based **trigger engine** that scans a mock transaction feed and raises alerts (no AI in this layer — deliberately rules-based; see [06-Technical-Architecture.md](06-Technical-Architecture.md)).
- A **case queue landing page** (the product's home screen after login).
- An **AI-assisted investigation workspace** for one frozen scenario family: *sudden high-value credit followed by rapid movement of funds*, demonstrated with a suspicious case and a legitimate "twin" case (see [05-Functional-Requirements-and-Use-Case-Document.md](05-Functional-Requirements-and-Use-Case-Document.md)).
- A **human decision layer**, kept visually and structurally separate from AI output.
- A **light escalation queue** for a Compliance role.
- A **full audit log** of AI actions and human decisions.
- All data is **fictional / mock**, clearly labelled throughout the product and documentation.

### Out of scope
- Real integrations with core banking, KYC providers, credit/sanctions bureaus, or case-management systems.
- Automated regulatory filing (STR/CTR) or any AI-made legal/criminal determination.
- Full identity and access management, production-grade security certification, multi-jurisdiction support.
- Every AML typology — only the frozen scenario family above, plus documented extension points.

## 7. Success Measures (for the capstone demo, not a production KPI set)

| Measure | Target for demo |
|---|---|
| End-to-end story is demonstrable live | Trigger fires → case appears in queue → AI report generated → investigator decision recorded → audit entry visible |
| Twin-case distinction is clear | Suspicious case (C1) and legitimate case (C2) produce visibly different AI findings from the same trigger rule |
| Every AI claim is traceable | 100% of AI findings cite an underlying mock record or are labelled Missing/Inferred |
| Human boundary is visible | No screen implies the AI decided the case; every disposition requires a human action + rationale |

Production-style KPIs (turnaround time, false-positive rate, adoption) belong in the roadmap document ([14-Delivery-Plan-and-Milestone-Roadmap.md](14-Delivery-Plan-and-Milestone-Roadmap.md)) as **forward-looking targets**, not measured results.

## 8. Budget & Timeline Assumptions

This is an **academic capstone**, not a funded product build.

- **Team:** 7 members (see [03-User-Personas-and-Stakeholders.md](03-User-Personas-and-Stakeholders.md) for the team roster and role split, and the team plan workbook for the task-level split).
- **Timeline:** submission window is the 1st–2nd week of October 2026; working backward, internal freeze target is ~6 October 2026 (adjust once the exact date is confirmed).
- **Budget:** none — uses free/low-cost LLM API tier, open-source libraries, mock data. Any live LLM API cost is the only real spend, kept small by caching demo responses (see [06-Technical-Architecture.md](06-Technical-Architecture.md)).
- **Effort assumption:** a working prototype covering the in-scope items above, not a production system.

## 9. What "Done" Looks Like for This Capstone

A submitted blueprint document, a slide deck, and a running (or reliably screen-recorded) prototype that together show: a transaction pattern gets detected → an investigator opens the case in a real product screen → the AI has already assembled evidence and flagged what's missing → the investigator makes and records the decision → the whole thing is logged. See [11-Acceptance-Criteria-and-Definition-of-Done.md](11-Acceptance-Criteria-and-Definition-of-Done.md) for the checklist version.
