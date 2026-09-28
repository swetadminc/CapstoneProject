# InvestigateIQ — AI-Powered AML Investigation Copilot

Capstone project — *Leadership with AI*, IIT Mumbai.

An AI Copilot that turns an AML alert into an evidence-grounded conversation with the
investigator — every claim cited, every recommendation traced to a source, every decision
made by a human. All data used across this project is **fictional**, generated for
demonstration purposes only.

## Where to start

| I want to... | Go to |
|---|---|
| Understand the product, architecture, roles, RAG/OKF design, and the 15-min demo script | [`Product Docs/InvestigateIQ - CEO Playbook.docx`](Product%20Docs/InvestigateIQ%20-%20CEO%20Playbook.docx) |
| See the diagrams (workflow, architecture, UI mockup, RAG pipeline, team flow) | [`Product Docs/diagrams/`](Product%20Docs/diagrams/) |
| Read the full merged blueprint (single PDF) | [`Product Docs/Sentinel-AML-Document.pdf`](Product%20Docs/Sentinel-AML-Document.pdf) |
| See the individual blueprint sections (PRD, data model, NFRs, etc.) | [`Product Docs/`](Product%20Docs/) — start at `00-README-Index.md` |
| Get the synthetic demo dataset (~10,000 transactions, 550 fictional customers) | [`Product Docs/dataset/`](Product%20Docs/dataset/) |
| Get the RAG knowledge base (OKF-format playbook documents) | [`Product Docs/dataset/knowledge_base.zip`](Product%20Docs/dataset/knowledge_base.zip) |
| Read the teammate-shared reference document that shaped this direction | [`Product Docs/InvestigateIQ - GIT.pdf`](Product%20Docs/InvestigateIQ%20-%20GIT.pdf) |
| See the team task-split / ownership workbook | [`Capstone Team Plan.xlsx`](Capstone%20Team%20Plan.xlsx) |
| Read the original analysis of the AML prototype ask | [`AML Prototype - Analysis and Proposal.md`](AML%20Prototype%20-%20Analysis%20and%20Proposal.md) |

## Status

Draft — several decisions are still pending team confirmation (use case freeze, LLM
provider, presenter, workstream owners). See Section 16 of the merged blueprint or
`Product Docs/12-Meeting-Notes-and-Decisions.md` for the open-items log.

**Deployed:** a placeholder app is live on Railway (auto-deploys on every push to `main`)
to prove the pipeline and the database connection work end to end. It is **not** the
Investigation Copilot yet — that build is the next phase. See `app.py`.

## Running locally

```bash
pip install -r requirements.txt
python data/build_database.py   # rebuilds data/investigateiq.db from the Excel dataset
streamlit run app.py
```

## Repository layout

```
app.py                  — placeholder Streamlit app (proves DB connection + deploy pipeline)
requirements.txt        — Python dependencies
Procfile                — Railway/Railpack start command
.streamlit/config.toml  — app theme
data/
  build_database.py     — builds investigateiq.db from the Excel dataset (re-run after edits)
  investigateiq.db       — SQLite database the app queries (customers, accounts,
                           transactions, relationships, alerts, past_cases, documents)
Product Docs/            — the full documentation pack (blueprint, PRD, architecture, etc.)
  diagrams/               — workflow, architecture, UI, RAG/OKF, team-flow diagrams (PNG)
  dataset/                — source Excel dataset + OKF knowledge base (RAG)
Capstone Team Plan.xlsx — team decisions, work split, timeline
AML Prototype - Analysis and Proposal.md — early scoping analysis
```
