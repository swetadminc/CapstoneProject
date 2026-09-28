# 05 — Functional Requirements & Use-Case Document

**Product:** Sentinel AML
**Related:** [02-Product-Requirements-Document.md](02-Product-Requirements-Document.md)

---

## 1. Frozen Use Case

**Scenario family:** Sudden high-value credit followed by rapid movement of funds.

**One-line statement:** An AI assistant that turns an AML alert for rapid movement of a large credit into an evidence-backed investigation package, while the human investigator keeps the decision.

**Two demonstration cases sharing the same trigger rules:**

| Case | Story | Outcome the demo shows |
|---|---|---|
| **C1 — Suspicious** | Customer with a small, steady transaction history suddenly receives ₹1 crore from an unrelated/unknown-relationship counterparty; ~86% moves out within 48 hours across 3 accounts (one hop external, thin data) | Multiple Verified red flags, several Missing items (no KYC on external hop accounts, undeclared source of funds), no counter-evidence on file |
| **C2 — Legitimate twin** | Same size and speed of movement, but the credit is a documented property-sale payment and the outbound transfer is to a verified family member, with a sale deed on file | Same trigger fires (amount deviation), but Verified counter-evidence is present; AI still lists the same category of red flag but with contrary evidence attached, and a lower recommended review priority — the human still decides |

## 2. Alert Trigger Definitions

| Rule ID | Name | Condition | Fires for |
|---|---|---|---|
| R1 | Amount deviation | Single incoming credit ≥ 5× the account's trailing 6-month average credit amount | C1, C2 |
| R2 | Rapid pass-through | ≥ 80% of a flagged credit's value leaves the receiving account within 72 hours, across ≥ 2 outbound transactions/hops | C1, C2 |

Both rules must fire to create a case in the default demo configuration (reduces noise); thresholds are configurable by the Admin role (F10).

## 3. Step-by-Step Use Case: "Investigate a rapid-movement alert"

**Actor:** AML Investigator
**Precondition:** Trigger Engine has raised an alert (R1 + R2 fired) and a case exists in the queue.

| Step | User action | System response | Validation / error handling |
|---|---|---|---|
| 1 | Investigator opens case queue (landing page) | Displays open cases sorted by priority/age, shows alert type and rule(s) fired | Empty queue shows "No open cases" state |
| 2 | Investigator selects a case | Opens Investigation Workspace: case header, alert summary strip (trigger amount, baseline, review period) | If case data incomplete, shows explicit "Missing" banner rather than blank fields |
| 3 | Investigator reviews AI-generated findings | Findings panel shows red flags, counter-evidence, missing items, conflicts — each with evidence status and citations | Any finding without a citation is blocked by the grounding validator and never reaches this screen (see [06](06-Technical-Architecture.md)) |
| 4 | Investigator reviews transaction timeline & fund-flow view | Chronological chart + account/fund-flow graph render from the same underlying data the AI used | If a downstream account is external (no data), UI shows it as "External — no data available" rather than omitting it silently |
| 5 | Investigator reviews investigation questions & recommended next steps | Each next step cites a playbook entry ID | A next step with no playbook citation cannot be displayed (validator rule) |
| 6 | Investigator takes an action | Options: Request information / Add evidence / Escalate / Close | Escalate and Close require a non-empty rationale field before submission is allowed |
| 7 | System records the decision | Human Decision Panel updates; Audit Log receives a new entry with actor, action, timestamp, rationale | Decision is immutable once submitted (correction requires a new logged action, not an edit) |

## 4. Expected Outcomes by Case

- **C1:** Investigator sees enough Verified + Missing evidence to justify escalation or a request for more information; decision remains theirs.
- **C2:** Investigator sees the same trigger but sufficient counter-evidence to justify closing with rationale "reviewed, documented legitimate transfer" — again, their decision, not the system's.

## 5. Error / Edge Cases Covered

| Case | Requirement |
|---|---|
| Missing data (stale KYC, no source-of-funds declared) | Shown as explicit "Missing" finding, never silently filled in or guessed |
| Conflicting data (declared occupation vs. observed activity mismatch) | Shown as "Conflicting" finding, both sources cited |
| Prompt injection via transaction reference text | Free-text fields are treated as untrusted data by the AI agent; validator strips/ignores any instruction-like content found there and logs the attempt |
| LLM/API unavailable during demo | Cached report replay available (F12) so the demo does not depend on a live call |

## 6. Non-Goals for This Use Case

- No claim of criminal determination.
- No automatic filing of any regulatory report.
- No coverage of typologies outside the rapid-movement family in the Must-have scope (see [02](02-Product-Requirements-Document.md) for Could-have extensions).
