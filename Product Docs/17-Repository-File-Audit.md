# InvestigateIQ — repository file audit

**Date:** 30 September 2026. **Scope:** 106 files visible before this audit was added, plus this file and six new unit-test files (113 currently), excluding `.git` and generated Python caches. This is a navigation and evidence audit, not a claim that every line of a large blueprint or every pixel of an image was reviewed. Python roles were checked from signatures and key flows; Markdown documents from headings and relevant content; workbook sheets, PDF page counts, playbook metadata, and cached-report structure were checked separately. The 40 supplied course files outside this repository are inventoried in [16-Course-Source-Evidence-Register.md](16-Course-Source-Evidence-Register.md).

**How to read “worth”:** priority for the capstone, not a monetary valuation. **Core** means required to demonstrate or explain the submitted prototype; **Support** means useful evidence or context; **Archive** means historical or duplicated material that should not be treated as current truth. “Done” below means the file exists and its stated function is present, not that the whole product is bank-ready.

## What the repository is exactly

It is a small Streamlit/Python academic AML-investigation prototype plus a much larger documentation pack. It uses a fictional Excel dataset loaded into SQLite, keyword-based playbook retrieval, a fixed six-step investigation workflow, Gemini for report drafting and chat, selected grounding checks, a human decision screen, and a runtime audit database. It is not a real bank integration, an autonomous financial-crime decision system, or evidence of measured business results.

## Core application and test files — 36 Python files

| File | Exactly what it does | Status / value / gap |
|---|---|---|
| `app.py` | Streamlit navigation router for eight pages. | **Done, Core.** Routes screens; no bank authentication. |
| `ui_common.py` | Shared styling, badges, prototype identity form, sidebar. | **Done, Core.** Group 7 appears provisionally; identity is not secure login. |
| `report_pdf.py` | Builds downloadable investigation report PDF. | **Done, Support.** Output is a draft record, not a regulatory filing. |
| `pages/home.py` | Landing page with product explanation, navigation and database counts. | **Done, Core.** Labels corrected for fictional data and fixed workflow; local smoke check passed. |
| `pages/0_Case_Queue.py` | Filters fictional alerts and opens an investigation. | **Done, Core.** Not a live transaction-monitoring feed. |
| `pages/1_Admin_Knowledge_Base.py` | Inspects playbook documents/chunks and retrieval. | **Done, Support.** Demonstrates the retrieval layer; admin gate is prototype-level. |
| `pages/2_Investigation_Demo.py` | Runs/replays a case, shows evidence/report/chat, records human action and audit history. | **Done, Core.** Five cached cases; live generation depends on Gemini. Validator notes now appear as warnings. |
| `pages/3_Compliance_Queue.py` | Second human review workflow for escalated cases. | **Done, Core.** Does not file an STR or connect to a regulator. |
| `pages/4_Admin_Rule_Config.py` | Previews and records changes to two illustrative trigger thresholds. | **Done, Support.** Preview uses fictional historical transactions; it does not regenerate alerts. |
| `pages/5_Analytics.py` | Counts cases, decisions, severity and trends from local databases. | **Done, Support.** Operational demo counts, not measured time savings/ROI. |
| `pages/6_Global_Search.py` | Searches customers, accounts and transactions in the fictional database. | **Done, Support.** Not enterprise search or production access control. |
| `agents/alert_triage_agent.py` | Loads and checks a case alert. | **Done, Core.** Deterministic specialist step, not adaptive LLM planning. |
| `agents/customer_kyc_agent.py` | Fetches customer/account context and prior cases. | **Done, Core.** Fictional KYC records only. |
| `agents/transaction_investigation_agent.py` | Computes transaction-window evidence and baseline comparisons. | **Done, Core.** Source-alert trigger linkage/data-window gaps remain. |
| `agents/relationship_agent.py` | Retrieves account/counterparty relationships. | **Done, Support.** No graph database or learned network model. |
| `agents/evidence_agent.py` | Retrieves playbook chunks and documents on file. | **Done, Core.** Guidance is synthetic, not approved Indian bank policy. |
| `agents/investigation_summary_agent.py` | Builds a structured evidence prompt and calls Gemini for a draft report. | **Done, Core.** Generated prose still needs human review. |
| `agents/orchestrator.py` | Calls the six specialist steps in a fixed order, then validation; logs stages. | **Done, Core.** Call it a six-step workflow, not six independently planning agents. |
| `agents/grounding_validator.py` | Checks selected IDs, evidence-status rules, playbook IDs, ratio wording and prohibited terms. | **Done, Core.** It does not prove every claim; some issues are flagged but not removed. |
| `agents/chat_agent.py` | Multi-turn Gemini question answering over case context. | **Done, Support.** Outputs still depend on supplied context and model behavior. |
| `agents/llm_client.py` | Gemini API request, model choice, response parsing/retries. | **Done, Core.** Live mode needs credentials/network; no model training. |
| `agents/investigation_agent.py` | Compatibility facade exposing older investigation function names. | **Done, Support.** Keep while callers depend on it; teach the orchestrator as the current flow. |
| `data/build_database.py` | Converts workbook and playbook files into SQLite tables/FTS index. | **Done, Core.** A rebuild replaces the tracked demo database; review before running. |
| `data/knowledge_search.py` | Keyword FTS5/BM25 search over playbook chunks. | **Done, Core.** Not embedding/vector or semantic retrieval. |
| `data/runtime_db.py` | Stores human actions, audit events and rule settings. | **Done, Core.** Decision and its audit record now share one SQLite transaction; identity remains mock-level and the log is not immutable. |
| `data/trigger_rules.py` | Illustrative R1/R2 threshold calculations and preview. | **Done, Support.** Not a bank monitoring engine. |
| `scripts/ci_check.py` | Rebuilds database and checks dataset/FTS invariants in CI. | **Done, Support.** Mutates tracked `data/investigateiq.db` if run locally. |
| `scripts/generate_cached_reports.py` | Generates demo report fixtures via the live pipeline. | **Done, Support.** Costs API calls and may overwrite fixtures; not part of every small edit. |
| `scripts/test_llm_connection.py` | Manual Gemini connection diagnostic. | **Done, Support.** Requires API/network; not a correctness benchmark. |
| `scripts/test_prompt_injection.py` | Manual prompt-injection probe. | **Done, Support.** One test does not establish comprehensive prompt-injection resistance. |
| `tests/test_runtime_db.py` | Isolated SQLite regression tests for human-decision/audit consistency. | **Done, Core test.** Covers success, rollback on audit failure, and required rationale. |
| `tests/test_grounding_validator.py` | Model-free tests for report guardrails. | **Done, Core test.** Covers clean pass, forbidden wording removal, bad citations, and ratio review. |
| `tests/test_prompt_boundary.py` | Checks that obvious instruction-like transaction notes are withheld from the model prompt without changing the evidence record. | **Done, Core test.** Narrow heuristic; not comprehensive injection resistance. |
| `tests/test_trigger_rules.py` | In-memory SQLite checks for illustrative trigger-preview arithmetic. | **Done, Core test.** Covers prior-credit baseline, same-day ISO timestamps, and two-debit minimum; not a full alert-engine test. |
| `tests/test_transaction_investigation.py` | Isolated transaction-evidence and cached-ratio provenance checks. | **Done, Core test.** Prevents deriving a deviation ratio from an arbitrary first window transaction. |
| `tests/test_chat_agent.py` | Mocked chat guardrail and prompt-boundary tests. | **Done, Core test.** Covers forbidden wording removal, invented citation filtering, and withholding obvious instruction-like transaction notes without an API call. |

## Product and management documents — 26 Markdown files

| File | What it is | Status / value / gap |
|---|---|---|
| `README.md` | Repository entry point and run/navigation guide. | **Done, Core.** Updated to point to current evidence map; do not treat old build counts as current. |
| `AML Prototype - Analysis and Proposal.md` | Early design critique and proposed scope. | **Archive/Support.** Useful rationale, but its “no build started” statement is historical. |
| `Product Docs/00-README-Index.md` | Index for the original 14-document Sentinel AML pack. | **Archive.** Old name/team-decision state; do not use as current product status. |
| `Product Docs/01-Project-Vision-and-Business-Case.md` | Problem, intended users, scope and value hypothesis. | **Support.** Strong “why”; value is not yet measured. |
| `Product Docs/02-Product-Requirements-Document.md` | Features, business rules, non-goals and release criteria. | **Core blueprint.** Compare with implementation rather than assuming every item is built. |
| `Product Docs/03-User-Personas-and-Stakeholders.md` | Investigator/manager/compliance personas and RACI. | **Support.** Roles are design assumptions, not interviewed users. |
| `Product Docs/04-Current-Process-and-Workflow.md` | As-is AML workflow, pains, handoffs and future state. | **Core blueprint.** Represents a conceptual process, not a measured bank process study. |
| `Product Docs/05-Functional-Requirements-and-Use-Case-Document.md` | Frozen twin-case scenario, triggers and edge cases. | **Core blueprint.** Some source alert fields/window evidence are imperfect. |
| `Product Docs/06-Technical-Architecture.md` | Layers, components, agent phases and deployment. | **Core blueprint.** Reconcile “agent” language with the fixed workflow in code. |
| `Product Docs/07-Data-Requirements.md` | Entity/field model, ownership, quality and sample footprint. | **Core blueprint.** Current data is synthetic; target-state owners/access are not implemented. |
| `Product Docs/08-Integration-and-API-Specifications.md` | Internal tool layer versus future external integrations. | **Support.** Only Gemini is a live external API; no bank APIs. |
| `Product Docs/09-UI-Wireframes-and-Screen-Designs.md` | Planned screens/layout/accessibility expectations. | **Support.** Useful for demo comparison, not proof of every accessibility requirement. |
| `Product Docs/10-Non-Functional-Requirements.md` | Performance, availability, accessibility, audit, security and scope. | **Core blueprint.** Production-grade security/retention remain future work. |
| `Product Docs/11-Acceptance-Criteria-and-Definition-of-Done.md` | Prototype, documentation and presentation acceptance lists. | **Core blueprint.** Verify each criterion against a test, not a checkbox alone. |
| `Product Docs/12-Meeting-Notes-and-Decisions.md` | Team decisions and unresolved questions. | **Support.** Confirm Saturday team choices before changing names/roles. |
| `Product Docs/13-Risks-Assumptions-Dependencies-Constraints.md` | Risk and assumption log. | **Core blueprint.** Refresh risk owners/status after team meeting. |
| `Product Docs/14-Delivery-Plan-and-Milestone-Roadmap.md` | Capstone milestones, future roadmap, illustrative KPIs/ROI. | **Core blueprint.** ROI figures are hypotheses, not results. |
| `Product Docs/15-Course-Concept-Application-Map.md` | Professor-facing topic → implementation → rationale → limit map. | **Done locally, Core.** Main teaching/presentation source; not committed yet. |
| `Product Docs/16-Course-Source-Evidence-Register.md` | Page anchors, 40-file course inventory, code proof and gaps. | **Done locally, Core.** Source audit; not committed yet. |
| `Product Docs/17-Repository-File-Audit.md` | This 106-file inventory and state/gap assessment. | **In progress, Support.** Keep concise and verify counts. |
| `Product Docs/BUILD-STATUS.md` | Detailed 29 September implementation snapshot. | **Support/Archive.** Historical counts (41 alerts) differ from current DB (42); update before citing as current. |
| `Product Docs/HANDOVER.md` | Running handover and current local-work record. | **Done locally, Core.** Update at each meaningful batch; older section remains historical. |
| `Product Docs/Flowchart-1-End-to-End-Data-Flow.md` | Mermaid target-state data-to-decision flow. | **Design history; warning added.** Shows automatic monitoring/case creation and immutable logging that the prototype does not provide. |
| `Product Docs/Flowchart-2-Investigation-Process-Flow.md` | Mermaid target-state investigator case flow. | **Design history; warning added.** Shows a document request/response loop, production case claiming, and system-of-record update that are not built. |
| `Product Docs/Sentinel-AML-Document.md` | Large merged original blueprint. | **Archive/Support.** Old product name and target-state sections; not the source of current implementation truth. |
| `Product Docs/dataset/README.md` | Dataset provenance/schema explanation. | **Core evidence.** Makes fictional-data boundary explicit; counts should be checked against current workbook/DB. |

## Synthetic playbook files — 24 Markdown files

Each is a fictional, versioned teaching document with an ID, scenario, title and body. All 24 have unique IDs and required metadata; none has an empty body. They are **Core evidence** for playbook retrieval, but **not** a substitute for RBI/FIU-IND sources or bank-approved procedures. The first code group retrieves and chunks them; the summary can cite their IDs. Pending: regulatory cross-check and approval only if the project later makes a real compliance claim.

| Scenario | Exact files and role |
|---|---|
| Rapid movement of funds | `pb-aml-07-01.md` KYC; `pb-aml-07-02.md` account relationship; `pb-aml-07-03.md` source of funds; `pb-aml-07-04.md` velocity/pass-through; `pb-aml-07-05.md` prior cases; `pb-aml-07-06.md` supporting documents; `pb-aml-07-07.md` escalation; `pb-aml-07-08.md` indicator versus conclusion; `pb-aml-07-09.md` external accounts; `pb-aml-07-10.md` closure documentation. |
| Amount anomaly | `pb-aml-aa-01.md` history comparison; `pb-aml-aa-02.md` source of funds; `pb-aml-aa-03.md` customer profile; `pb-aml-aa-04.md` escalation; `pb-aml-aa-05.md` closure documentation. |
| Dormant reactivation | `pb-aml-dar-01.md` activity pattern; `pb-aml-dar-02.md` escalation. |
| Structuring | `pb-aml-str-01.md` pattern; `pb-aml-str-02.md` escalation. |
| Velocity | `pb-aml-vel-01.md` frequency/clusters; `pb-aml-vel-02.md` business fit; `pb-aml-vel-03.md` structuring signs; `pb-aml-vel-04.md` escalation; `pb-aml-vel-05.md` closure documentation. |

All files in this table are under `Product Docs/dataset/knowledge_base/`.

## Data, cached examples, visuals and delivery configuration — 27 files

| File(s) | Exactly what it is | Status / value / gap |
|---|---|---|
| `Product Docs/dataset/InvestigateIQ - Synthetic Bank Dataset.xlsx` | Seven-sheet fictional source workbook: customers, accounts, transactions, relationships, alerts, past cases, documents. | **Done, Core.** Current loaded DB: 552 customers, 654 accounts, 9,950 transactions, 42 alerts. Not real bank data. |
| `data/investigateiq.db` | Tracked SQLite demo database built from workbook and playbooks. | **Done, Core.** Read-only checks found 24 playbook documents, 57 chunks and five covered alert scenarios. A local rebuild changes this tracked file. |
| `data/cached_reports/CASE-001.json` | Pre-generated report/context/evidence/guidance for first twin case. | **Done, Support.** Rehearsal fixture, not a measured investigation outcome. |
| `data/cached_reports/CASE-002.json` | Pre-generated report for second twin case. | **Done, Support.** Same limitation. |
| `data/cached_reports/CASE-003.json` | Pre-generated report for another alert scenario. | **Done, Support.** Same limitation. |
| `data/cached_reports/CASE-006.json` | Pre-generated report for another alert scenario. | **Done, Support.** Same limitation. |
| `data/cached_reports/CASE-041.json` | Pre-generated report for structuring demo case. | **Done, Support.** Same limitation. |
| `Capstone Team Plan.xlsx` | Four-sheet decisions, roles/strengths and timeline workbook. | **Support.** Team identity/assignments must be reconfirmed; do not publish names prematurely. |
| `Product Docs/InvestigateIQ - CEO Playbook.docx` | 127-paragraph, 12-table early presenter/leadership playbook. | **Design history; do not present as-is.** It says every claim is cited, uses embeddings/FAISS-or-Chroma vector search, calls the audit log immutable, and marks the Compliance screen “document only.” Current code contradicts those points. |
| `Product Docs/Sentinel-AML-Document.pdf` | 21-page PDF rendering of earlier Sentinel blueprint. | **Archive.** Old name and target-state content; avoid as current product proof. |
| `Product Docs/InvestigateIQ - GIT.pdf` | 13-page InvestigateIQ presentation/reference PDF. | **Support as a concept deck, not results.** Page 1 says the tool makes investigation faster without our measured baseline; pp. 12–13 show an illustrative ₹8M case rather than a verified current UI/database screenshot. Pages on human control and non-goals are useful. |
| `Product Docs/dataset/knowledge_base.zip` | Packaged copy of synthetic playbook source files. | **Support/Archive.** Avoid treating zip and extracted Markdown as independent evidence. |
| `Product Docs/diagrams/1-workflow-flowchart.png` | Conceptual alert-to-decision flow. | **Design history; do not show as-is.** It says the validator checks every finding, a missing-evidence loop returns to discovery, and the audit log is immutable. Those are not established by current code. |
| `Product Docs/diagrams/2-architecture-diagram.png` | Layered architecture concept. | **Design history; do not show as-is.** It depicts a vector index, LLM tool-calling, and an older single-agent/roadmap state. Current retrieval is FTS5 and the fixed six-step pipeline has one summary LLM call. |
| `Product Docs/diagrams/3-ui-mockup.png` | Example investigation workspace layout with invented case text. | **Support as mockup only.** Its ₹8M example, three-panel layout and example “verified” findings are illustrative, not current UI/data proof. |
| `Product Docs/diagrams/4-build-responsibility-flow.png` | Seven-day role-by-day staffing plan. | **Design history.** Team roles, owners and schedule need Saturday confirmation; do not assign real people from this image. |
| `Product Docs/diagrams/5-rag-okf-pipeline.png` | Planned knowledge-retrieval pipeline. | **Design history; do not show as-is.** It says embeddings, FAISS/Chroma vector storage, and similarity search. Current code uses sentence chunks in SQLite FTS5/BM25 with no embedding calls. |
| `Product Docs/diagrams/6-simple-flowchart-for-team.png` | Simplified six-box alert-to-decision story. | **Support with caveat.** “Bank system flags” is fictional source data here, and “everything is logged/full auditable trail” overstates the current prototype controls. Human final decision is the valid core idea. |
| `assets/logo_full.svg` | Full logo for light background. | **Done, Support.** Current product branding. |
| `assets/logo_full_dark.svg` | Full logo for dark background. | **Done, Support.** Current product branding. |
| `assets/logo_icon.svg` | Compact logo/icon. | **Done, Support.** Current product branding. |
| `requirements.txt` | Pinned Python dependencies. | **Done, Core.** Reproducible prototype install, not a security audit. |
| `Procfile` | Alternative Streamlit start command. | **Done, Support.** Railway config is the main deployment route. |
| `railway.json` | Railway build, predeploy DB rebuild and app start configuration. | **Done, Core.** Deploy only in agreed daily batch; confirm build status afterward. |
| `.github/workflows/ci.yml` | CI job running the DB rebuild/sanity script on pushes/PRs. | **Done, Support.** Covers basic data/index invariants, not complete app behavior. |
| `.streamlit/config.toml` | UI theme and server CORS/XSRF flags. | **Done, Core configuration.** Local Streamlit warned about disabled CORS; not production-security proof. |
| `.gitignore` | Excludes local runtime DB and temporary/platform files. | **Done, Support.** Confirm no secrets are staged before GitHub push. |

## Overall judgment and next actions

**What is done:** a demonstrable academic prototype, synthetic data/knowledge base, a broad blueprint pack, and a source-based course mapping. **What it is worth:** strong capstone evidence of a bounded AI workflow and explainable design choices; no defensible monetary valuation yet. **Main gap:** real Indian-bank data, verified regulation/policy, investigator testing, outcome baseline, production controls and current team decisions. The README and source evidence register should lead the explanation; the older Sentinel pack and 29 September build report should be used as design history, not unquestioned current fact.

**Presentation safety:** the six PNG diagrams were visually checked. In particular, diagrams 1, 2 and 5 conflict with the implemented system and should be corrected or omitted from the final deck. This is a higher-priority gap than visual polish because the professor can compare these pictures with the code.

The existing CEO playbook is also out of date in consequential ways: it describes vector retrieval and immutable logging that do not exist. The 13-page InvestigateIQ PDF is a better strategic narrative, but its “faster” and case example statements are hypotheses/illustrations, not measured results. Do not submit either unchanged as proof of the final prototype.

**Next within the agreed scope:** reconcile the key diagrams/presenter material with the verified six-step, fictional-data story; keep the handover current; make one reviewed Git/deploy batch at 9 p.m. New York time. The later product improvements, member assignments and detailed code-teaching guide await the team discussion.
