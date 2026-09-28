# 13 — Risks, Assumptions, Dependencies, and Constraints Log

**Product:** Sentinel AML

---

## 1. Assumptions (stated explicitly so they are never mistaken for validated facts)

| # | Assumption | Where it's used | Needs validation before reuse outside this capstone |
|---|---|---|---|
| A1 | Investigators currently spend "several hours" compiling evidence per moderately complex case | [01-Project-Vision-and-Business-Case.md](01-Project-Vision-and-Business-Case.md) | Yes — illustrative only |
| A2 | 6× reduction / "minutes instead of hours" style time savings | Value story, ROI language | Yes — no measured baseline exists |
| A3 | India (PMLA/FIU-IND/RBI) is an acceptable illustrative jurisdiction context | Scenario framing | Team decision pending; no specific regulation cited without a compliance-literate reviewer's check |
| A4 | An LLM with tool-calling and structured JSON output is accessible to the team at low/no cost | [08-Integration-and-API-Specifications.md](08-Integration-and-API-Specifications.md) | Yes — provider/key not yet assigned (see [12](12-Meeting-Notes-and-Decisions.md)) |
| A5 | Streamlit is an acceptable prototype UI technology for the evaluation | [06-Technical-Architecture.md](06-Technical-Architecture.md) | Team preference; document explicitly frames it as a stand-in for a target web architecture |
| A6 | 7-person team, ~10 working days of effective build time | [01](01-Project-Vision-and-Business-Case.md), [14](14-Delivery-Plan-and-Milestone-Roadmap.md) | Confirm actual availability per person |

## 2. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Live LLM call fails or behaves unexpectedly during the 15-minute demo | Medium | High | Cached report replay (F12); rehearse with network off at least once |
| R2 | Mock data looks too clean/scripted, undermining credibility | Medium | Medium | Deliberately add irregular timing, a legitimate-looking small outflow, and the C2 twin case (see [05](05-Functional-Requirements-and-Use-Case-Document.md) §2) |
| R3 | Team runs out of time before all Must-have features are built | Medium | High | Strict MoSCoW prioritization in [02-PRD](02-Product-Requirements-Document.md); Should/Could items dropped first, not Must items |
| R4 | Regulatory references added late by someone without compliance background, introducing inaccurate claims | Medium | High | Named reviewer requirement logged in [12-Meeting-Notes-and-Decisions.md](12-Meeting-Notes-and-Decisions.md); default to no specific-regulation claims if unverified |
| R5 | Evaluators perceive the product as "AI decides," undermining the human-in-the-loop positioning | Low–Medium | High | Enforced via UI design (visually separate panels), BR1/BR4 business rules, and explicit acceptance criteria in [11](11-Acceptance-Criteria-and-Definition-of-Done.md) |
| R6 | LLM produces an unsupported claim ("hallucination") in a finding | Medium | High | Grounding validator rejects/downgrades any finding without a citation (see [06](06-Technical-Architecture.md) §1) |
| R7 | Prompt injection via transaction reference or document text | Low–Medium | Medium | Explicit test case C8 in [05](05-Functional-Requirements-and-Use-Case-Document.md); untrusted-input handling in validator |
| R8 | Team members duplicate work or edit the same section simultaneously | Medium | Low–Medium | Single-owner-per-workstream model in the team-plan workbook; one master document owner |
| R9 | No confirmed LLM API access close to the build deadline | Medium | High | Assign an owner immediately (open item in [12](12-Meeting-Notes-and-Decisions.md)); have a rules-only fallback demo path (no live LLM, cached only) as a last resort |

## 3. Dependencies

| Dependency | Needed for | Status |
|---|---|---|
| LLM API access (provider + key) | AI Investigation Agent, live demo mode | **Not yet assigned** — see [12](12-Meeting-Notes-and-Decisions.md) |
| Team availability per the timeline | All build workstreams | Assumed per A6; not yet individually confirmed |
| Confirmed exact submission date/format | Final scheduling of all deadlines in [14](14-Delivery-Plan-and-Milestone-Roadmap.md) | **Not yet confirmed** — email only gives "1st/2nd week of October" |
| A team member with banking/compliance familiarity | Reviewing any regulatory language before submission | **Not yet assigned** |

## 4. Constraints

| Constraint | Detail |
|---|---|
| No real data | Fictional data only, by design and by necessity (no institutional access) |
| No budget | Academic project; must use free/low-cost tools throughout |
| Timeline | Submission window in the first/second week of October 2026; today is 27 September 2026 |
| Team size and skill mix | 7 members with unconfirmed individual strengths (see [03-User-Personas-and-Stakeholders.md](03-User-Personas-and-Stakeholders.md) and the team-plan workbook) |
| No production access or certification | Explicitly out of scope; documented as target-state only throughout this pack |

## 5. How This Log Should Be Used

Review and update this file at each team check-in alongside [12-Meeting-Notes-and-Decisions.md](12-Meeting-Notes-and-Decisions.md). An assumption that gets validated (or a risk that materializes) should be noted with a date, not silently removed.
