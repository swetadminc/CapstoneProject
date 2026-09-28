# 14 — Delivery Plan / Milestone Roadmap

**Product:** Sentinel AML
**Note:** Dates are proposals working backward from "1st/2nd week of October" — confirm the exact submission date and adjust (see [12-Meeting-Notes-and-Decisions.md](12-Meeting-Notes-and-Decisions.md), open item).

---

## 1. Capstone Delivery Milestones (this submission)

| Date (proposed) | Milestone | Depends on |
|---|---|---|
| 27–28 Sep 2026 | Use case, jurisdiction, and track confirmed by team; workstreams claimed | Team call |
| 29 Sep 2026 | Mock dataset spec finalized (customers, accounts, transactions for C1–C4 minimum) | Use case confirmed |
| 30 Sep – 1 Oct | Trigger Engine (R1, R2) + data layer built and tested against the dataset | Dataset ready |
| 1–2 Oct | AI Investigation Agent + tool layer + grounding validator built | Trigger Engine, LLM access confirmed |
| 2–3 Oct | Investigation Workspace UI built (case queue, workspace, decision panel) | Agent producing valid reports |
| 3 Oct | Audit log, escalation queue, admin screen added | Core workspace working |
| 4 Oct | Full end-to-end run-through: trigger → case → AI report → decision → audit, for C1 and C2 | All modules integrated |
| 4–5 Oct | Cached report fallback captured for demo reliability; test scenarios C3–C8 run | End-to-end working |
| 5 Oct | Documentation pack finalized and cross-checked (this folder) | Prototype behavior matches documents |
| 5–6 Oct | Slide deck built; presenter rehearsal (timed, 15 minutes incl. Q&A) | Documentation + prototype done |
| 6 Oct | Internal freeze — final QA pass against [11-Acceptance-Criteria-and-Definition-of-Done.md](11-Acceptance-Criteria-and-Definition-of-Done.md) | Everything above |
| 1st–2nd week Oct | **Submission** (exact date TBD) | Freeze complete |

## 2. Phased Roadmap Beyond the Capstone (target-state — documented for blueprint completeness, not built)

| Phase | Objective | Key activities | Not part of this capstone |
|---|---|---|---|
| Phase 1 — Real data discovery | Validate assumptions in [13-Risks-Assumptions-Dependencies-Constraints.md](13-Risks-Assumptions-Dependencies-Constraints.md) against a real institution | Process mapping, data inventory, measured baseline (actual hours/alert, false-positive rate) | Entire phase |
| Phase 2 — Real integrations | Replace mock data with real source systems | Core banking, KYC, case-management integration (see [08](08-Integration-and-API-Specifications.md) target-state table) | Entire phase |
| Phase 3 — Multi-agent split | Move from single Investigation Agent to the six-agent design (Triage, Transaction, Relationship, KYC, Evidence, Summary) | Agent-by-agent migration, each replacing one tool-call sequence | Documented design only (see [06-Technical-Architecture.md](06-Technical-Architecture.md) §5) |
| Phase 4 — Screening & policy RAG | Add sanctions/PEP/adverse-media review and real policy-document retrieval | Vendor selection, RAG index over approved policy documents | Out of scope; noted as extension |
| Phase 5 — Governance & model risk | Formal model risk management, bias/drift monitoring, compliance sign-off | Model documentation, monitoring dashboards, periodic review | Out of scope |
| Phase 6 — Production hardening | Full IAM, encryption, scale testing, SLAs | Security certification, load testing | Out of scope |
| Phase 7 — Pilot and scale | Controlled pilot with real (masked) data, then broader rollout | Pilot design, adoption plan, KPI baselining | Out of scope |

## 3. KPIs (target-state, illustrative — see [13](13-Risks-Assumptions-Dependencies-Constraints.md) A1/A2 for the assumption flag)

| KPI | How it would be measured in production | Not measured in this prototype |
|---|---|---|
| Time per alert (compile-to-decision) | Timestamp diff, case creation to disposition | Yes — prototype has no real user population |
| False-positive rate after AI-assisted triage | Investigator disposition vs. alert volume | Yes |
| Evidence completeness at first review | % of findings with no "Missing" status at case open | Partially observable in demo cases, not a measured population metric |
| Investigator satisfaction / adoption | Survey, usage metrics | Yes |
| Audit completeness | % of decisions with full traceable evidence chain | **This one the prototype can actually demonstrate structurally** — every decision in the prototype has a full chain by construction |

## 4. ROI Logic (illustrative, explicitly marked as assumption-based)

A simple illustrative frame for the blueprint's value section — **not a claim of actual measured savings**:

> If an investigator currently spends an assumed *N* hours compiling evidence per case, and Sentinel AML reduces that to *M* minutes of review time, the illustrative time saved per case is (N hours − M minutes), which can be multiplied by case volume and loaded cost per investigator-hour to estimate an illustrative annual saving. **Both N and M are placeholders for the team to fill in only if they choose to include this in the blueprint, and must be labeled as assumptions, not measured results.**

## 5. Final Recommendation & Decisions Needed (for the blueprint's closing section)

1. Confirm the twin-case (C1/C2) design as the anchor demo — recommended.
2. Confirm Blueprint + shallow prototype as the submission track — recommended, given the timeline.
3. Assign the open items in [12-Meeting-Notes-and-Decisions.md](12-Meeting-Notes-and-Decisions.md) before Phase-1-equivalent build work starts (29 Sep target).
4. Treat everything in section 2 of this document as the "roadmap beyond the capstone" slide — it demonstrates forward thinking without implying it was built.
