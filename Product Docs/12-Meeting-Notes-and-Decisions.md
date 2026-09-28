# 12 — Meeting Notes and Decisions

**Product:** Sentinel AML
**Purpose:** Running log of decisions, unresolved questions, action owners, and deadlines. **Every item below is a proposal or an open question awaiting human confirmation from the team — nothing here is final until the team confirms it on a call or in writing.**

---

## Log Format

Each entry: Date | Topic | Decision or Open Question | Owner | Status

---

## Entries

| Date | Topic | Decision / Open Question | Owner | Status |
|---|---|---|---|---|
| 2026-09-26 | Use case | Proposed: "sudden high-value credit followed by rapid movement of funds," with a suspicious case (C1) and a legitimate twin case (C2) | Team | **Needs team confirmation** |
| 2026-09-26 | Jurisdiction | Proposed: India context (illustrative only; no specific regulation cited without verification) | Team | **Needs team confirmation** |
| 2026-09-26 | Submission track | Proposed: Blueprint + shallow prototype | Sweta (stated preference) | **Needs final team confirmation** |
| 2026-09-27 | Trigger mechanism | Decision direction: build a visible, rule-based Trigger Engine (R1 amount deviation, R2 rapid pass-through) as a real first stage of the demo, not a pre-seeded alert | Team | **Needs team confirmation** |
| 2026-09-27 | Product framing | Decision direction: build as an end-to-end product (landing page, case queue, investigation workspace, human decision panel, audit log) rather than a single chatbot screen | Team (per Sweta's direction) | **Adopted for this documentation pack — confirm at next call** |
| — | LLM provider & API key/budget | **Open.** Which provider (e.g., a specific vendor), whose account, who pays for/monitors usage? | **Unassigned — needs owner** | Open |
| — | Presenter | **Open.** Who is the one presenter for the 15-minute slot? | **Unassigned** | Open |
| — | Master document ownership | **Open.** Who merges all sections into the final submission and does final QA? Suggested: Sweta, per earlier team-plan draft | **Unassigned — needs confirmation** | Open |
| — | Workstream owners | **Open.** See the team-plan workbook (`Capstone Team Plan.xlsx`) — owners not yet assigned to workstreams A–J | **Unassigned** | Open |
| — | Exact submission date/portal | **Open.** Email says "1st/2nd week of October" — exact date and submission mechanism not yet confirmed | **Unassigned** | Open |
| — | Second trigger rule (velocity/structuring, F13) | **Open.** Build only if time allows after Must-haves are done | Team | Open — deprioritized by default |
| — | Regulatory references in blueprint | **Open.** Any specific PMLA/FIU-IND/RBI citation added to the blueprint text must be checked by a team member with compliance/banking background before submission | **Needs a named reviewer** | Open |

## Unresolved Questions Needing a Team Decision

1. Do we confirm the use case and twin-case design as final, or does anyone have a competing AML scenario to propose?
2. Is the India/PMLA framing acceptable, or should the team stay jurisdiction-agnostic to avoid citing anything unverified?
3. Who owns the LLM API key and cost, and what is the budget ceiling (even if near-zero)?
4. Who is the single presenter, and who is the backup if that person is unavailable on presentation day?
5. Confirm: Streamlit for the prototype UI (fastest path), or does anyone want to push for a React/FastAPI build given more lead time?

## Action Items (until claimed, these have no owner)

| Action | Suggested owner | Deadline (proposed) |
|---|---|---|
| Confirm use case, twin case, jurisdiction on next team call | All | Next call |
| Claim workstreams A–J in team-plan workbook | All | Within 24h of next call |
| Provide/confirm LLM API access | TBD | Before prototype build starts |
| Verify any regulatory references before they go in the blueprint | TBD (compliance/banking background preferred) | Before final submission |
| Confirm exact submission date and format from IIT Mumbai | Sweta or admin contact | ASAP |

**Reminder:** This file should be updated after every team call, not rewritten from scratch — add new rows, don't delete history.
