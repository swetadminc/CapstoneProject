# InvestigateIQ — Build Status

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
| Synthetic dataset (550 customers, ~9,900 transactions) | ✅ Built & verified | `Product Docs/dataset/` |
| RAG knowledge base — real SQLite FTS5 index (chunking + BM25 keyword search, no vector DB needed at this scale) | ✅ Built & verified | 20 documents, 47 chunks — **now covers all three alert scenarios** (rapid-movement-of-funds, amount-anomaly, velocity), not just the frozen demo scenario |
| Admin Knowledge Base inspector (proves chunking/indexing to an evaluator live) | ✅ Built & verified | `/Admin_Knowledge_Base`, passcode `IQ-Demo-2026` |
| Gemini API integration | ✅ Built & verified | Model: `gemini-flash-lite-latest` (found `gemini-flash-latest` deprecated during testing) |
| **Investigation Agent** — DB → deterministic analysis → RAG retrieval → Gemini (JSON-schema constrained) → Grounding Validator | ✅ Built & verified live | `agents/investigation_agent.py` |
| **Chat Agent** — grounded, cited, multi-turn Q&A | ✅ Built & verified live | `agents/chat_agent.py` |
| Cached-report fallback (zero-cost rehearsal, zero live dependency) | ✅ Built & verified | `data/cached_reports/`, toggle on the demo page |
| Prompt-injection guardrail | ✅ Verified against the live model | `scripts/test_prompt_injection.py` — model flagged the injection attempt itself |
| **Human Decision panel** — accept/reject findings, mandatory rationale (BR4), investigator name | ✅ Built & verified live | On `/Investigation_Demo` |
| **Persistent Audit Log** — every AI action + human decision, survives redeploys via a mounted Railway volume | ✅ Built & verified live | `data/runtime_db.py`, confirmed via SSH into the production container |
| **Case Queue Dashboard** — all 40 alerts, filters, KPIs, live decision status, one-click into the workspace | ✅ Built & verified live | `/Case_Queue` |

## What's still genuinely open

| Gap | Detail |
|---|---|
| Layout | Still one long page per case, not the polished 3-panel side-by-side layout from the original wireframe (evidence / chat / decision as separate visual columns) |
| Login / roles | No real authentication — mock passcode gate on the admin page only, matches the documented NFR scope |
| Escalation queue screen | Escalation is logged as a decision; there's no separate Compliance-role screen to review escalated cases |
| Multi-agent split | Prototype runs as one orchestrating agent with five internal stages, not five separate agents — documented as the next phase, not a gap in behavior |
| Chat history across cases | Each case's chat history is independent (by design — a fresh case shouldn't inherit another case's conversation) |

## Correcting the CEO Playbook specifically

Section 9 ("Requirements Coverage — What We Will and Won't Cover") listed several items as "Document only."
These are now **Build**, not document-only:
- AI agents (Context/Discovery/Evidence/Conclusion/Grounding Validator stages) — built as one orchestrating
  agent, per the documented prototype-scope decision, not five separate agents
- RAG over the OKF knowledge base — built, with real chunking and a real FTS5 index, and now covers all
  three scenarios in the dataset
- Human decision panel + audit log — built and persisted
- Case queue dashboard — built, covering all 40 alerts, not a mock

Still accurately "Document only" per that table: login/role-based access, a separate escalation/compliance
screen, admin rule-configuration UI, and the full five-agent split.
