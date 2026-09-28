# 11 — Acceptance Criteria / Definition of Done

**Product:** Sentinel AML

---

## 1. Feature-Level Acceptance Criteria

### F3 — Trigger Engine
- [ ] Given the mock transaction feed, when a credit meets Rule R1 (≥5x baseline) AND a subsequent Rule R2 (≥80% out within 72h across ≥2 hops), an alert is created with the exact rule ID(s) and threshold values attached.
- [ ] Given a transaction that meets only R1 but not R2 (e.g., C7 in test scenarios), no alert is created in default config.
- [ ] The rule(s) and threshold values that fired are visible on the case (not just "alert exists").

### F5/F6 — Investigation Workspace & Evidence Status
- [ ] Every AI finding displayed has a non-empty citation (`supporting_txn_ids` or `source_refs`).
- [ ] Every AI finding has exactly one evidence status: Verified, Inferred, Missing, or Conflicting.
- [ ] A finding is never labeled "Verified" unless the validator confirms the cited record directly supports the stated claim.
- [ ] For case C1, at least one "Missing" finding appears (external-account KYC gap).
- [ ] For case C2, at least one "Conflicting" or counter-evidence finding appears that a reviewer can see differs meaningfully from C1's findings for the same trigger.

### F7 — Human Decision Panel
- [ ] Escalate and Close actions are blocked until a non-empty rationale is entered.
- [ ] Once submitted, a decision cannot be silently edited — a correction requires a new logged action.
- [ ] The Human Decision Panel is visually distinct from the AI Findings panel at a glance (color/border difference).

### F8 — Audit Log
- [ ] Every AI tool call during a case's investigation appears as a log entry.
- [ ] Every human action appears as a log entry with actor, timestamp, and rationale (where applicable).
- [ ] Log entries cannot be edited or deleted through the UI.

### F12 — Cached/Live Toggle
- [ ] With no network/API access, the demo cases still load a full report from cache.
- [ ] Switching to "live" regenerates a report for at least one case without error, when API access is available.

## 2. Guardrail Acceptance Criteria (from BR1–BR8 in [02-PRD](02-Product-Requirements-Document.md))

- [ ] No AI-generated text anywhere in the product uses the words "criminal," "illegal," "guilty," or equivalent verdict language (automated check + manual review).
- [ ] No AI-generated "next step" appears without a `playbook_id` citation.
- [ ] The prompt-injection test case (C8 in [05](05-Functional-Requirements-and-Use-Case-Document.md)) produces a report that does not follow the injected instruction, and the attempt is visible in the audit log.
- [ ] Every screen carries the "Prototype — fictional data" banner.

## 3. Definition of Done — Prototype

The prototype is **Done** for submission when:
1. All Must-have features (F1–F8, F11) from [02-PRD](02-Product-Requirements-Document.md) work end to end for both C1 and C2 without manual intervention.
2. All acceptance criteria in sections 1–2 above pass.
3. The full flow — trigger fires → case in queue → investigation workspace with cited findings → human decision recorded with rationale → audit log entry visible — has been run start to finish at least twice successfully (once in rehearsal, once on demo hardware) per [14-Delivery-Plan-and-Milestone-Roadmap.md](14-Delivery-Plan-and-Milestone-Roadmap.md).
4. A cached fallback exists for every demo case in case of live API failure.

## 4. Definition of Done — Documentation Pack

1. All 14 documents in this folder exist, are internally consistent (same product name, scenario names, rule IDs across all files), and cross-reference each other correctly.
2. Both flowcharts render correctly when pasted into a Mermaid-compatible tool.
3. The full pack has been reviewed against the sample blueprint's evaluation rubric (see the earlier blueprint conversation / rubric section) by at least one team member other than the author of each section.

## 5. Definition of Done — Presentation

1. Slide deck built from this documentation pack (not duplicating it verbatim).
2. One presenter identified and rehearsed within the 15-minute limit including Q&A buffer.
3. Live demo (or a screen recording, as a fallback) of the end-to-end flow is ready.
