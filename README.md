# InvestigateIQ — AI-Powered AML Investigation Copilot

Capstone project — *Leadership with AI*, IIT Bombay · Capstone Group 7 (group name pending team confirmation).

An AI copilot that brings an AML alert and its available evidence into one investigator
workspace. Reports carry evidence labels and source IDs, recommended next steps cite a
synthetic playbook, and a human records the decision. All data used across this project is **fictional**, generated for
demonstration purposes only.

**Live app:** https://investigateiq-app-production.up.railway.app/
→ Case Queue (landing page) · Investigation Demo · Admin Knowledge Base (passcode `IQ-Demo-2026`)

## Where to start

| I want to... | Go to |
|---|---|
| See the build history (some dataset counts are from an earlier snapshot) | [`Product Docs/BUILD-STATUS.md`](Product%20Docs/BUILD-STATUS.md) |
| Read the five-minute course-to-project explanation | [`Product Docs/15-Course-Concept-Application-Map.md`](Product%20Docs/15-Course-Concept-Application-Map.md) — start with “Read this first”; the longer tables are optional reference |
| Read the earlier product vision and 15-min demo script (some architecture claims are historical, not current implementation proof) | [`Product Docs/InvestigateIQ - CEO Playbook.docx`](Product%20Docs/InvestigateIQ%20-%20CEO%20Playbook.docx) |
| See the diagrams (workflow, architecture, UI mockup, RAG pipeline, team flow) | [`Product Docs/diagrams/`](Product%20Docs/diagrams/) |
| Read the full merged blueprint (single PDF) | [`Product Docs/Sentinel-AML-Document.pdf`](Product%20Docs/Sentinel-AML-Document.pdf) |
| See the individual blueprint sections (PRD, data model, NFRs, etc.) | [`Product Docs/`](Product%20Docs/) — start at `00-README-Index.md` |
| Get the synthetic demo dataset (9,950 transactions, 552 fictional customers) | [`Product Docs/dataset/`](Product%20Docs/dataset/) |
| Get the fictional playbook knowledge base (24 documents across 5 alert scenarios) | [`Product Docs/dataset/knowledge_base.zip`](Product%20Docs/dataset/knowledge_base.zip) |
| Read the teammate-shared reference document that shaped this direction | [`Product Docs/InvestigateIQ - GIT.pdf`](Product%20Docs/InvestigateIQ%20-%20GIT.pdf) |
| See the team task-split / ownership workbook | [`Capstone Team Plan.xlsx`](Capstone%20Team%20Plan.xlsx) |
| Read the original analysis of the AML prototype ask | [`AML Prototype - Analysis and Proposal.md`](AML%20Prototype%20-%20Analysis%20and%20Proposal.md) |

## Status

**Working academic prototype.** The public app may lag this repository during deployment; verify
the public URL before presenting a newly released feature. This repository has a Case Queue, a fixed six-step
investigation workflow, playbook retrieval, Gemini-assisted report drafting and chat, selected
grounding checks, a human decision panel, a Compliance review screen, and an audit history.
The UI uses a two-panel investigation workspace by design. Real authentication/roles, bank data
integration, verified Indian-bank policy, and measured outcome results are not implemented.
[`Product Docs/BUILD-STATUS.md`](Product%20Docs/BUILD-STATUS.md) is a historical build snapshot;
see the [course map](Product%20Docs/15-Course-Concept-Application-Map.md) for current boundaries.

## Running locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The tracked demo database is already included. Run `python data/build_database.py` only when
the source workbook or playbooks change; it rebuilds that tracked file. Cached-mode rehearsal
does not need an API key. Live report/chat mode needs `GEMINI_API_KEY` in the environment;
never put the key in Git.

## Repository layout

```
app.py                  — Streamlit page router
pages/
  0_Case_Queue.py        — 42 fictional alerts, filters, KPIs, routes into the workspace
  1_Admin_Knowledge_Base.py — RAG transparency: documents, chunks, live search
  2_Investigation_Demo.py   — evidence panel, chat panel, human decision panel, audit log
agents/
  orchestrator.py        — fixed six-step workflow -> Gemini draft -> selected checks
  investigation_agent.py — compatibility interface for the investigation workflow
  chat_agent.py           — grounded, cited, multi-turn Q&A over a case's evidence
data/
  build_database.py      — builds investigateiq.db from the Excel dataset + OKF knowledge base
  knowledge_search.py     — FTS5 keyword search + autosuggest over the knowledge base
  runtime_db.py           — persistent audit log + human decisions (separate DB, survives redeploys)
  cached_reports/         — five stored demo reports, rechecked by the current validator on replay
scripts/
  generate_cached_reports.py, test_prompt_injection.py, ci_check.py, test_llm_connection.py
tests/                     — model-free unit tests for decisions/audit and grounding guardrails
requirements.txt, Procfile, railway.json, .streamlit/config.toml — deploy config
Product Docs/             — the full documentation pack (blueprint, PRD, architecture, etc.)
  BUILD-STATUS.md          — historical 29 September build snapshot
  diagrams/                — workflow, architecture, UI, RAG/OKF, team-flow diagrams (PNG)
  dataset/                 — source Excel dataset + OKF knowledge base (RAG)
Capstone Team Plan.xlsx  — team decisions, work split, timeline
AML Prototype - Analysis and Proposal.md — early scoping analysis
```
