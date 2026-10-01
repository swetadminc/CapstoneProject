# InvestigateIQ — Build Status

> **Historical snapshot (29 September 2026).** The “current” wording below was true when this snapshot was written but is no longer authoritative for all counts or claims. The local database now has 42 alerts, 24 playbook documents, and 57 chunks; its fixed six-step workflow is not six independently planning AI agents. See [16-Course-Source-Evidence-Register.md](16-Course-Source-Evidence-Register.md) and [17-Repository-File-Audit.md](17-Repository-File-Audit.md) for the verified present state. Keep this file as build history until a deliberate full refresh.

**As of:** 29 September 2026
**Purpose:** The CEO Playbook and the original documentation pack describe the *plan*. A great deal has since
been built and verified live — this file is the honest, current snapshot, so nobody reads the earlier
"document only" / "not started" labels as still accurate. Where this file and an earlier document disagree,
this file is newer and correct.

**Live app:** https://investigateiq-app-production.up.railway.app/
**Repo:** https://github.com/swetadminc/CapstoneProject

---

## What's built and verified live (not just planned)

| Capability | Status | Where |
|---|---|---|
| GitHub ↔ Railway auto-deploy pipeline | ✅ Built & verified | Every push to `main` auto-deploys |
| CI sanity check on every push | ✅ Built & verified | `.github/workflows/ci.yml` |
| SQLite database, auto-rebuilt from source on every deploy | ✅ Built & verified | `data/build_database.py` |
| Synthetic dataset (551 customers, ~9,940 transactions, 41 alerts across 4 typologies) | ✅ Built & verified | `Product Docs/dataset/` |
| RAG knowledge base — real SQLite FTS5 index (chunking + BM25 keyword search, no vector DB needed at this scale) | ✅ Built & verified | 22 documents, 52 chunks — covers all four alert scenarios (rapid-movement-of-funds, amount-anomaly, velocity, structuring) |
| Admin Knowledge Base inspector (proves chunking/indexing to an evaluator live) | ✅ Built & verified | `/Admin_Knowledge_Base`, passcode `IQ-Demo-2026` |
| Gemini API integration | ✅ Built & verified | Model: `gemini-flash-lite-latest` (found `gemini-flash-latest` deprecated during testing) |
| **Investigation Agent — six-agent split** (Alert Triage, Customer/KYC, Transaction Investigation, Relationship, Evidence, Investigation Summary), plus a separate Grounding Validator layer, orchestrated end to end | ✅ Built & verified live | `agents/orchestrator.py`, one file per agent — see below |
| **Chat Agent** — grounded, cited, multi-turn Q&A | ✅ Built & verified live | `agents/chat_agent.py` |
| Cached-report fallback (zero-cost rehearsal, zero live dependency) | ✅ Built & verified | `data/cached_reports/` — one case per typology (CASE-001, CASE-002, CASE-003, CASE-006, CASE-041), toggle on the demo page |
| Prompt-injection guardrail | ✅ Verified against the live model | `scripts/test_prompt_injection.py` — model flagged the injection attempt itself |
| **Human Decision panel** — accept/reject findings, mandatory rationale (BR4), investigator name | ✅ Built & verified live | On `/Investigation_Demo` |
| **Persistent Audit Log** — every AI action + human decision, survives redeploys via a mounted Railway volume | ✅ Built & verified live | `data/runtime_db.py`, confirmed via SSH into the production container |
| **Case Queue Dashboard** — all 41 alerts, filters, KPIs, live decision status, one-click into the workspace | ✅ Built & verified live | `/Case_Queue` |
| **Login / shared session identity** — name + role captured once, attributed on every decision and audit event | ✅ Built & verified live | `ui_common.py`, all 5 pages |
| **Compliance / Escalation Queue** — separate role screen listing escalated cases, with its own decision workflow (acknowledge / return / refer) | ✅ Built & verified live | `/Compliance_Queue` |
| **Admin Rule Configuration** — adjust R1/R2 thresholds, live preview of impact against real transaction data before saving, change history | ✅ Built & verified live | `/Admin_Rule_Config` |
| **Second alert typology (structuring)** — a genuinely different trigger pattern from the frozen C1/C2 rapid-movement scenario, with its own RAG-grounded playbook | ✅ Built & verified live | CASE-041, `PB-AML-STR-01/02` |
| **2-panel workspace layout** matching the original wireframe (Evidence & Findings / Ask the Copilot as real side-by-side columns) | ✅ Built & verified live | `/Investigation_Demo` |
| **Shared design system** — one CSS module instead of six duplicated banner blocks; severity/status badges, KPI cards, dark-mode-aware colors | ✅ Built & verified live | `ui_common.py` |
| **Dark mode** — real in-app toggle (not just an OS media query, which Streamlit's locked custom theme can't respond to) | ✅ Built & verified live | Sidebar toggle, all 8 pages |
| **Analytics dashboard** — severity/typology/status mix, alert volume trend, decision throughput by investigator, all live queries | ✅ Built & verified live | `/Analytics` |
| **Global Search** — find a customer, account, or transaction across the full dataset by name, ID, or reference text | ✅ Built & verified live | `/Global_Search` |
| **PDF export** — download an investigation report (findings, citations, validator result, human decision) as a real PDF | ✅ Built & verified live | `report_pdf.py`, "Download PDF report" on `/Investigation_Demo` |
| **Landing page redesign** — dashboard home with live KPI cards and card-based navigation, not a plain link list | ✅ Built & verified live | `app.py` |
| Audit-log write overhead reduced | ✅ Built & verified | `data/runtime_db.py` — `init_runtime_db()` now runs its DDL once per process instead of on every single audit event (was re-running on every one of the 8 events per investigation after the multi-agent split) |

## What's still genuinely open

| Gap | Detail |
|---|---|
| Chat history across cases | Each case's chat history is independent (by design — a fresh case shouldn't inherit another case's conversation) |
| Cached reports | Only 5 of 41 cases have a pre-generated cached report (one per typology); the rest fall back to a live Gemini call if selected in cached mode with no fixture on file |
| Dataset labeling (see below) | `alert_type` (display text) and `scenario_id` (the field that actually drives RAG retrieval and trigger logic) are inconsistently paired across the original 40-alert dataset — cosmetic, not a correctness bug, not yet cleaned up |
| Chart theming in dark mode | `st.bar_chart`/`st.area_chart` render via Vega-Lite, which keeps its own white plot background regardless of app theme — readable in both modes, just not fully re-skinned |

## UI overhaul: optimization, features, and design system — 29 September 2026

Beyond the original 7-item pending list, three more things were added: a real code-level optimization, three
new features (Analytics, PDF export, Global Search), and a full visual design-system pass including dark mode.

**Optimization.** `data/runtime_db.py`'s `init_runtime_db()` was being called — and re-running its full DDL
(4 CREATE TABLE + 2 CREATE INDEX statements plus a connect/commit/close cycle) — on every single read/write
function in that file, including `log_audit_event()`. The multi-agent split had already taken audit events
from 3 to 8 per investigation, nearly tripling this overhead. Fixed with a process-lifetime guard flag; the
DDL is idempotent either way, so this changes nothing about correctness, only how often the no-op statements
re-run. Verified directly (`_initialized` flips True after the first call, stays True) and live through a full
orchestrator run (8 audit events recorded correctly).

**New features:**
- **Analytics** (`/Analytics`) — severity/typology/status distribution, high-severity share by typology, weekly
  alert volume trend, and decisions-recorded-by-investigator, all live queries against the same two databases
  every other page reads from.
- **PDF export** (`report_pdf.py`, via `fpdf2`) — a "Download PDF report" button on the Investigation Demo page
  renders the same findings/citations/next-steps/narrative/validator-result/human-decision shown on screen into
  a real downloadable PDF. Found and fixed a real bug during testing: fpdf2's `multi_cell()` with `w=0` leaves
  the cursor at the right margin by default (the deprecated `ln=True` shortcut used to paper over this), so
  every call after the first raised `FPDFException("Not enough horizontal space")` — fixed by passing
  `new_x=XPos.LMARGIN, new_y=YPos.NEXT` explicitly on every cell/multi_cell call. Verified by generating and
  text-extracting real PDFs from two different cached reports, and by clicking the actual button in the
  running app (network request confirmed 200 OK, correct binary PDF response).
- **Global Search** (`/Global_Search`) — searches customers, accounts, transactions, and cases by name, ID, or
  reference text in one box, with parameterized queries only (the search term is never string-formatted into
  SQL). Verified live: searching "Coastal" correctly returns all 8 real "Coastal *" businesses in the dataset
  plus the CASE-041 structuring case, with a working "Investigate →" link straight into the workspace.

**Design system.** All six `.iq-banner` CSS blocks (hand-duplicated across every page) were pulled into one
shared module (`ui_common.py`): a banner component, severity/status badge helpers, KPI cards, and a consistent
navy/blue palette via CSS custom properties. The landing page (`app.py`) was rebuilt as a real dashboard home
with live KPI cards and card-based navigation instead of a plain list of links. Case Queue got matching badge
and KPI-card styling in place of its own local CSS classes.

**Dark mode.** Genuinely harder than it looks in Streamlit: `prefers-color-scheme: dark` CSS does nothing for
Streamlit's own chrome, and Streamlit removes its native Settings > Theme switcher entirely as soon as
`.streamlit/config.toml` sets *any* `[theme]` key (confirmed empirically) — which this app needs, to keep the
custom navy `primaryColor`. Built as a real in-app toggle instead (sidebar, all pages): Python decides which of
two CSS blocks to emit based on `st.session_state`, with `!important` overrides on Streamlit's stable
`data-testid` hooks for its own containers. Two real bugs found and fixed during verification, not just
assumed away:
1. A blanket `* { color: ... !important }` rule (needed to re-color Streamlit's own text) was also clobbering
   the severity/status badges' own red/amber/green text, making them invisible (light text on a light tint).
   Fixed with higher-specificity two-class selectors that win regardless of source order.
2. Streamlit's native backtick-code spans (`` `CASE-001` ``) keep their own light background regardless of app
   theme, so the same blanket text-color rule made that text invisible too (light text on near-white). Fixed
   with a dedicated `code { }` override.
3. The toggle's value didn't persist across page navigation at first — a freshly-instantiated
   `st.toggle(key=...)` on a new page (each page in a classic `pages/`-directory app is a separate script) does
   not reliably pick up a same-named `session_state` entry last written by a different page. Fixed by passing
   `value=st.session_state.get(...)` explicitly instead of relying on `key=` binding alone. Verified by toggling
   dark mode on the home page and confirming it held across three further page navigations.

Also surfaced and fixed, unrelated to the code itself: two zombie local test-server processes from earlier in
this session (ports 8550 and 8560) were still running and racing on the same shared local runtime-database
file path, causing one intermittent `no such table` error during final verification. Not a production issue —
Railway serves one process per deploy — but a reminder to kill background test servers between rounds.

## The multi-agent split (pending item #5), built 29 September 2026

Technical Architecture §5 documented this as roadmap-only: "split into six specialist agents — Alert Triage,
Transaction Investigation, Relationship, Customer/KYC, Evidence, Investigation Summary — as originally proposed
by the team." It's now built, not just documented:

- `agents/alert_triage_agent.py` — `AlertTriageAgent`: pulls the triggering alert, the one place the alerts
  table is read from directly.
- `agents/customer_kyc_agent.py` — `CustomerKYCAgent`: customer + account identity, risk rating, KYC status,
  and prior-case history for that customer.
- `agents/transaction_investigation_agent.py` — `TransactionInvestigationAgent`: the deterministic arithmetic
  (baseline average, review-window transactions, deviation ratio) — the one thing the LLM is never trusted to
  compute itself.
- `agents/relationship_agent.py` — `RelationshipAgent`: counterparty relationship lookups for every account
  seen in the transaction window.
- `agents/evidence_agent.py` — `EvidenceAgent`: RAG playbook retrieval (FTS5/BM25) and case documents on file.
- `agents/investigation_summary_agent.py` — `InvestigationSummaryAgent`: the only agent that calls the LLM;
  drafts the structured report from everything the other five produced.
- `agents/grounding_validator.py` — `GroundingValidator`: deliberately **not** one of the six — Technical
  Architecture §2 lists it as its own validation layer, and it still runs after Investigation Summary, checking
  every citation before a report reaches a human.
- `agents/orchestrator.py` — `InvestigationOrchestrator`: wires all six agents plus the validator in sequence,
  and now logs each agent's completion as its own audit-log entry (8 entries per investigation instead of the
  original 3), so the six-agent pipeline is visible in the Audit Log UI, not just in the code.
- `agents/llm_client.py` — the Gemini HTTP call, pulled out so it's one shared place, used by both the
  Investigation Summary Agent and the Chat Agent, instead of duplicated.

`agents/investigation_agent.py` is now a thin compatibility facade over this pipeline — every function it used
to define (`gather_context`, `discover_evidence`, `retrieve_guidance`, `build_prompt`, `call_gemini`,
`validate_report`, `investigate`) still exists with the exact same signature, delegating to the real agent that
now owns that responsibility, so nothing that already depended on it (the Investigation Demo page, the Chat
Agent, `generate_cached_reports.py`, and critically `scripts/test_prompt_injection.py`, a safety test) needed
to change.

**Verified before shipping:** the deterministic agents (Transaction Investigation, Relationship, Customer/KYC)
produce byte-identical output to the pre-split code for CASE-001, CASE-002, CASE-041, CASE-006, and CASE-004;
`scripts/ci_check.py` passes; `scripts/test_prompt_injection.py` passes through the new pipeline (the safety
guardrail is intact); the orchestrator was run live against all 4 typologies with zero exceptions; the cached
report fixtures were regenerated through the new code path; and the live UI was checked end to end — the
Investigation Demo page, the Ask-the-Copilot chat panel, and the Audit Log all render correctly, with the audit
log now showing all 6 named agents plus the Grounding Validator as distinct, attributed pipeline stages.

## Dataset-quality findings from broader per-case verification (29 Sep 2026)

Pending item #6 asked for broader verification across cases, not just the two frozen hero cases. Running the
live agent against a wider sample surfaced two real, pre-existing issues in the original 40-alert dataset
(inherited — not introduced by the structuring-case addition, and not present in CASE-041):

1. **24 of 41 alerts have zero transactions inside the agent's 10-day evidence window.** Most of the original
   alerts were generated without a real anchoring `trigger_transaction_id`, so `alert_date` doesn't reliably
   line up with actual account activity. Previously this silently produced an empty evidence set and the LLM
   had nothing to reason about but "MISSING." **Fixed**: `agents/investigation_agent.py` now falls back to the
   5 real transactions nearest `alert_date` when the strict window is empty, clearly labeled to the model (and
   in the UI) as background context, not the trigger event — verified live across 9 previously-empty cases
   spanning all three affected typologies (amount-anomaly, velocity, rapid-movement-of-funds); the model
   consistently reports the empty window honestly rather than fabricating a trigger. This never touches a case
   that already has real in-window evidence (the frozen C1/C2 hero cases and CASE-041 are all unaffected).
2. **`alert_type` (the human-readable label shown in the UI) and `scenario_id` (the field that actually drives
   RAG retrieval and the trigger-rule logic) are not reliably paired** — e.g. CASE-006 displays as "Velocity
   anomaly" but its `scenario_id` is `amount-anomaly`, and the agent correctly retrieves amount-anomaly
   playbook guidance for it. The AI's analysis is correct (it uses `scenario_id`, not the display label); the
   *label shown to a human investigator* can be misleading. Not fixed — no dataset generator script is
   committed to this repo (see below), so correcting it would mean hand-editing labels across the original 40
   alerts, which is a real data-quality task, not a code fix. Documented here rather than silently left for
   someone to discover later.

Both were found by actually running the live agent against a broad sample (13 distinct cases this session,
covering all 4 typologies and both the empty- and non-empty-evidence paths), not by inspection alone.

## Correcting the CEO Playbook specifically

Section 9 ("Requirements Coverage — What We Will and Won't Cover") listed several items as "Document only."
These are now **Build**, not document-only:
- AI agents — built as the full six-agent split (Alert Triage, Customer/KYC, Transaction Investigation,
  Relationship, Evidence, Investigation Summary) plus a separate Grounding Validator layer, per Technical
  Architecture §5's roadmap design, not the single-orchestrator prototype scope originally planned for the
  capstone
- RAG over the OKF knowledge base — built, with real chunking and a real FTS5 index, covering all four
  scenarios in the dataset
- Human decision panel + audit log — built and persisted
- Case queue dashboard — built, covering all 41 alerts, not a mock
- Login/role-based access — built (shared session identity, not real authentication — matches documented NFR)
- Escalation/compliance screen — built
- Admin rule-configuration UI — built, with live threshold-impact preview

Nothing from that table remains "Document only" as of this build. No generator script for the source dataset
(`Product Docs/dataset/InvestigateIQ - Synthetic Bank Dataset.xlsx`) is committed to this repo — all additive
changes to it this session were made via one-off scripts kept outside version control, appending new rows only,
never reordering or regenerating existing ones.
