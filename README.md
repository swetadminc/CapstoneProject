# InvestigateIQ — AI-Powered AML Investigation Copilot

Capstone project — *Leadership with AI*, IIT Mumbai.

An AI Copilot that turns an AML alert into an evidence-grounded conversation with the
investigator — every claim cited, every recommendation traced to a source, every decision
made by a human. All data used across this project is **fictional**, generated for
demonstration purposes only.

**Live app:** https://investigateiq-app-production.up.railway.app/
→ Case Queue (landing page) · Investigation Demo · Admin Knowledge Base (passcode `IQ-Demo-2026`)

## Where to start

| I want to... | Go to |
|---|---|
| See what's actually built vs. still planned (read this first — the docs below describe the plan, this is the current reality) | [`Product Docs/BUILD-STATUS.md`](Product%20Docs/BUILD-STATUS.md) |
| Understand the product, architecture, roles, RAG/OKF design, and the 15-min demo script | [`Product Docs/InvestigateIQ - CEO Playbook.docx`](Product%20Docs/InvestigateIQ%20-%20CEO%20Playbook.docx) |
| See the diagrams (workflow, architecture, UI mockup, RAG pipeline, team flow) | [`Product Docs/diagrams/`](Product%20Docs/diagrams/) |
| Read the full merged blueprint (single PDF) | [`Product Docs/Sentinel-AML-Document.pdf`](Product%20Docs/Sentinel-AML-Document.pdf) |
| See the individual blueprint sections (PRD, data model, NFRs, etc.) | [`Product Docs/`](Product%20Docs/) — start at `00-README-Index.md` |
| Get the synthetic demo dataset (~10,000 transactions, 550 fictional customers) | [`Product Docs/dataset/`](Product%20Docs/dataset/) |
| Get the RAG knowledge base (OKF-format playbook documents, 20 docs covering all 3 alert scenarios) | [`Product Docs/dataset/knowledge_base.zip`](Product%20Docs/dataset/knowledge_base.zip) |
| Read the teammate-shared reference document that shaped this direction | [`Product Docs/InvestigateIQ - GIT.pdf`](Product%20Docs/InvestigateIQ%20-%20GIT.pdf) |
| See the team task-split / ownership workbook | [`Capstone Team Plan.xlsx`](Capstone%20Team%20Plan.xlsx) |
| Read the original analysis of the AML prototype ask | [`AML Prototype - Analysis and Proposal.md`](AML%20Prototype%20-%20Analysis%20and%20Proposal.md) |

## Status

**Working, deployed, and verified live** — not a placeholder. See
[`Product Docs/BUILD-STATUS.md`](Product%20Docs/BUILD-STATUS.md) for the full, honest breakdown of what's
built vs. still open. In short: the Case Queue, the Investigation Agent (real Gemini calls, RAG-grounded,
validated), the chat panel, the human decision panel, and a persistent audit log are all live and tested
end to end. Still open: the polished 3-panel workspace layout, real login/roles, and a separate
Compliance/escalation screen.

## Running locally

```bash
pip install -r requirements.txt
python data/build_database.py   # rebuilds data/investigateiq.db from the Excel dataset + knowledge base
export GEMINI_API_KEY=...       # required for live agent/chat calls (not needed for cached-mode demo)
streamlit run app.py
```

## Repository layout

```
app.py                  — landing/status page (proves DB connection + deploy pipeline)
pages/
  0_Case_Queue.py        — all 40 alerts, filters, KPIs, routes into the workspace
  1_Admin_Knowledge_Base.py — RAG transparency: documents, chunks, live search
  2_Investigation_Demo.py   — evidence panel, chat panel, human decision panel, audit log
agents/
  investigation_agent.py — DB -> deterministic analysis -> RAG -> Gemini -> Grounding Validator
  chat_agent.py           — grounded, cited, multi-turn Q&A over a case's evidence
data/
  build_database.py      — builds investigateiq.db from the Excel dataset + OKF knowledge base
  knowledge_search.py     — FTS5 keyword search + autosuggest over the knowledge base
  runtime_db.py           — persistent audit log + human decisions (separate DB, survives redeploys)
  cached_reports/         — pre-validated report fixtures for zero-cost demo rehearsal
scripts/
  generate_cached_reports.py, test_prompt_injection.py, ci_check.py, test_llm_connection.py
requirements.txt, Procfile, railway.json, .streamlit/config.toml — deploy config
Product Docs/             — the full documentation pack (blueprint, PRD, architecture, etc.)
  BUILD-STATUS.md          — current reality vs. the plan (read this first)
  diagrams/                — workflow, architecture, UI, RAG/OKF, team-flow diagrams (PNG)
  dataset/                 — source Excel dataset + OKF knowledge base (RAG)
Capstone Team Plan.xlsx  — team decisions, work split, timeline
AML Prototype - Analysis and Proposal.md — early scoping analysis
```
