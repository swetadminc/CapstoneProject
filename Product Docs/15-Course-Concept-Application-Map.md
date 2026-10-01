# InvestigateIQ — Course Concept Application Map

**Course:** Leadership with AI, IIT Bombay
**Project:** InvestigateIQ — AI-Powered AML Investigation Copilot
**Team identity:** Capstone Group 7 *(provisional wording; confirm the official group name before final submission)*
**Purpose:** This working document shows how course concepts are applied in the prototype. It is not a claim that the prototype is a production banking system or certified compliant with Indian regulation. Source PDFs remain in the private course folder and are not included in this repository.

## Read this first — the five-minute version

You do **not** need to read the source register, repository audit, or all older blueprint files. Those are my evidence trail so we can answer questions accurately. For now, remember five points:

1. **Problem:** An AML alert leaves an investigator collecting evidence from several places. InvestigateIQ puts fictional case evidence in one workspace.
2. **Course application:** We use a hybrid approach—Python/SQLite for facts, keyword retrieval for a synthetic playbook, Gemini for a draft explanation, selected checks for obvious grounding problems, and a person for the final decision.
3. **Case-study reference:** DBS supports the principle of guided, human-supervised banking AI; BMW and Erica reinforce the human hand-off; the financial-crime PDF is a sample blueprint, not a deployed-bank result.
4. **What we can show:** A working synthetic-data prototype with 42 recorded alerts, 24 playbook documents, five cached demo reports, a case queue, investigation report, chat, human decision, and audit history. The current local test suite has 27 passing checks. These are *prototype results*, not measured time savings, detection accuracy, Indian regulatory compliance, or six autonomous planning agents.
5. **What comes next:** After the team meeting, choose the presenter and final narrative, then prepare a short code/database explanation and results section. Until then, the detailed tables below are reference material, not required reading.

---

## 1. The project in one sentence

InvestigateIQ is an academic prototype for an Indian-bank AML investigator: it brings alert, customer, transaction, relationship, document, and playbook evidence into one workflow; drafts a cited investigation report; and keeps every final case decision with a human.

## 2. The explanation pattern to use in class

For every topic, use this five-part answer:

1. **What we learned:** State the course concept in simple language.
2. **Our business problem:** State the specific AML-investigation difficulty it solves.
3. **How we applied it:** Point to the visible screen, database object, or Python component.
4. **Why this choice fits:** Explain why it is appropriate for this task.
5. **Boundary:** State what the prototype deliberately does *not* claim or do.

This matters because leadership with AI is not about using the maximum number of AI tools. It is about assigning each technology a suitable job, controlling risk, and measuring whether the workflow becomes better.

---

## 3. Course-topic-to-project map

| Course concept | What it means in simple English | How InvestigateIQ applies it | Evidence in this repository | Why this was the appropriate choice | What we must not claim |
|---|---|---|---|---|---|
| **AI opportunity identification and strategy** | Start from a high-value business decision, not from a fashionable AI tool. | The project targets one narrow, high-friction task: assembling an AML investigation after an alert. | [Project vision](01-Project-Vision-and-Business-Case.md), [PRD](02-Product-Requirements-Document.md), `pages/2_Investigation_Demo.py` | An investigator spends time gathering evidence from many records; a copilot can reduce preparation work while preserving professional judgment. | That all AML work is automated or that the prototype is ready for a bank-wide rollout. |
| **Value versus feasibility prioritisation** | A good first AI use case has meaningful value but is small enough to validate safely. | The scope is deliberately one investigation workflow with fictional data, not a replacement for transaction-monitoring or core banking systems. | [Scope and non-goals](02-Product-Requirements-Document.md), [Build status](BUILD-STATUS.md) | It is feasible within a capstone and lets the team demonstrate a complete workflow instead of many incomplete features. | That a prototype proves enterprise-scale ROI. |
| **Digital enterprise and data foundations** | AI needs reliable data, connected systems, and a workflow around it; it cannot work as an isolated chat screen. | Customer, account, transaction, alert, relationship, case, and document data are modelled together before AI produces a report. | `Product Docs/dataset/InvestigateIQ - Synthetic Bank Dataset.xlsx`; `data/build_database.py`; `data/investigateiq.db` | The model can only reason over the evidence supplied to it. A structured data layer lets a reviewer trace cited findings to source records; it does not itself prove the interpretation is correct. | That the fictional workbook is real bank data or has production data quality. |
| **Metadata and generic-entity modelling** | Entities such as customer, account, transaction, document, and case need stable identifiers and relationships. | The database links `customer_id`, `account_id`, `txn_id`, `case_id`, and document IDs across the investigation. | [Data requirements](07-Data-Requirements.md); SQLite tables in `data/investigateiq.db`; `data/build_database.py` | IDs allow the app to cite evidence precisely and let a reviewer trace a finding back to a record. | That this is a complete enterprise data model, customer master, or data-governance program. |
| **Hybrid AI: rules, retrieval, generation, and human judgment** | Different problems need different AI approaches; one LLM should not do every job. | Python/SQLite calculate transaction facts; FTS5 retrieves playbook guidance; Gemini drafts the narrative; a human decides the outcome. | `agents/transaction_investigation_agent.py`; `data/knowledge_search.py`; `agents/investigation_summary_agent.py`; `data/runtime_db.py` | Arithmetic and filters are repeatable; policy retrieval grounds recommendations; language generation is useful for a readable summary; accountability stays human. | That the LLM independently calculates, approves, or files a regulatory report. |
| **Knowledge-based systems and RAG** | A system should retrieve relevant domain knowledge when it needs guidance, rather than relying on the model's memory alone. | The copilot retrieves scenario-specific fictional AML playbook chunks and cites them in recommended next steps. | `Product Docs/dataset/knowledge_base/`; `data/build_database.py`; `data/knowledge_search.py`; Admin Knowledge Base page | It gives the investigator a visible, inspectable basis for next steps and limits unsupported generic advice. | That these synthetic playbooks are bank-approved policies, legal authorities, or a complete regulatory knowledge system. |
| **Generative AI, prompt/context engineering, and verification** | Generative AI is useful for contextual synthesis, but its output needs constraints and review. | The summary agent receives structured context, evidence, guidance, response schema, and explicit limits. The validator checks selected citations and ratio claims, removes specified verdict-like wording from report/chat text, and marks issues for review. | `agents/investigation_summary_agent.py`; `agents/grounding_validator.py`; `agents/chat_agent.py`; `tests/` | It uses GenAI for what it does well—turning evidence into a structured explanation—while adding controls for known failure modes. | That validation guarantees zero hallucinations, verifies every factual claim, or makes the system legally compliant. |
| **Agentic AI and orchestration — partial application** | Course material distinguishes fixed workflow automation from agents that choose and adapt actions. | Six named specialist components run in a fixed sequence: triage, KYC, transaction analysis, relationship analysis, evidence retrieval, and summary; a validator runs afterward. The summary and chat components make LLM calls. | `agents/orchestrator.py` and the specialist files in `agents/` | The decomposition mirrors the investigation workflow, gives each step a narrow responsibility, and makes the audit trail understandable. | That all six components are independent reasoning agents, dynamically plan, or autonomously change the workflow. |
| **Human-in-the-loop and controlled autonomy** | In high-stakes decisions, AI recommends; accountable people decide. | Investigators can accept/reject findings and must give a rationale for close, request-information, or escalate actions. | `pages/2_Investigation_Demo.py`; `data/runtime_db.py`; [Acceptance criteria](11-Acceptance-Criteria-and-Definition-of-Done.md) | AML decisions can affect customers, reporting, and bank risk; the correct role for this prototype is decision support. | That the copilot determines guilt, labels someone a criminal, or autonomously files an STR. |
| **Explainability, provenance, and auditability** | Leaders need to know why an AI output exists and be able to review what happened. | Findings carry evidence status and source IDs; pipeline stages and human actions are written to a SQLite audit log. | `agents/grounding_validator.py`; `data/runtime_db.py`; `pages/2_Investigation_Demo.py` | This directly addresses the trust problem in high-stakes financial decision support. | That the log is tamper-proof in the legal/forensic sense or that it meets a bank's records-retention standard. |
| **Security, privacy, and responsible-AI boundaries** | Risk controls should be designed into the system, not added only in a slide. | The project uses fictional data, parameterized database queries, environment-based API keys, a limited admin gate, and a narrow check that withholds obvious instruction-like transaction notes from the model prompt while logging their IDs. | [NFRs](10-Non-Functional-Requirements.md); `agents/investigation_summary_agent.py`; `agents/orchestrator.py`; `tests/test_prompt_boundary.py` | A course prototype can show the direction of responsible design without pretending to provide production security. | That mock login/passcodes, SQLite, or a few prompt tests are production-grade IAM, comprehensive prompt-injection resistance, or compliance controls. |
| **Prototype, pilot, and scale are different stages** | A prototype tests whether the workflow and value proposition are credible; it is not a pilot or scaled product. | InvestigateIQ uses a working end-to-end prototype with fictional data, cached reports, and a small set of scenarios. | [Build status](BUILD-STATUS.md); `data/cached_reports/`; `railway.json` | This is the right capstone stage: demonstrate workflow feasibility and learning before expensive integration or model training. | That the current result is a bank pilot, an operational deployment, or proof of customer adoption. |
| **Outcome measurement rather than activity measurement** | Do not measure success by “how many AI tools were built”; measure the operational result. | The app can report alert/case mix, decision throughput, report completion, evidence status, and audit events. | `pages/5_Analytics.py`; [Data requirements](07-Data-Requirements.md) | These measures relate to investigation workflow visibility and consistency. | That they prove real time savings, true-positive rate, or financial return without a controlled real-world study. |
| **Build, buy, and partner choices** | Select technology layer by layer based on differentiation, speed, control, cost, and risk. | The team built the workflow, database model, retrieval layer, UI, and guardrails; it uses Streamlit, SQLite, Railway, and Gemini as commodity components. | `requirements.txt`; `railway.json`; `agents/llm_client.py`; [Technical architecture](06-Technical-Architecture.md) | Building the domain workflow shows learning and control; using managed/common components keeps a small capstone affordable and deliverable. | That this exact technical stack is the only correct production architecture for an Indian bank. |
| **AI initiative leadership steps** | Frame the problem, compare AI options, define value, assess data policy and risk, choose capabilities, test, decide, and monitor. | The vision, PRD, risks, architecture, acceptance criteria, and demo cover parts of the ten-step template. | Course workbook `AI_Initiative_Leadership_Templates_Steps.xlsx`; [Vision](01-Project-Vision-and-Business-Case.md); [Risks](13-Risks-Assumptions-Dependencies-Constraints.md) | It gives the team a transparent management decision path instead of relying on an impressive demo alone. | That the workbook's sample HR scores, ROI figures, or pilot outcomes are InvestigateIQ results. |
| **AI economics and selective use** | Each model call has a variable cost; retrieve concise context and use a model only where generation adds value. | Deterministic stages and FTS search run without a model; the summary and chat use Gemini; five demo reports have cached replay. | `agents/orchestrator.py`; `agents/llm_client.py`; `data/cached_reports/`; `pages/2_Investigation_Demo.py` | It makes the academic demo more reliable and avoids a model call for simple arithmetic or lookup. | That cost per case or annual ROI has been measured. |

---

## 4. Case-study lessons we can legitimately use

The correct statement is: **“This case informed our design principle.”** Do not say: **“Our product is the same as this company’s system.”**

| Course case / source | Situation and decision in the case | Lesson applied to InvestigateIQ | Exact project parallel | Honest boundary |
|---|---|---|---|---|
| **AI Financial Crime Investigation Copilot — sample blueprint** | This course example lays out data, process, AI components, controls, and accountable human decision points for a banking investigation; it is not an empirical bank deployment. | Design the capstone as an alert-to-decision blueprint with data, AI, technology, governance, and execution layers. | The project has a similar structure: evidence assembly, synthetic playbook retrieval, report drafting, human decision, and audit trail. | Our project is a small academic prototype with synthetic data; it does not include screening, graph analytics, real bank case management, or banking integration. |
| **DBS’ AI Journey** | DBS shifted from unreliable open-ended bot responses to guided conversations (p. 4), consolidated data (p. 6), adopted a responsible-use review (pp. 8–9), and kept GenAI under human oversight for internal work (p. 11); it also used GenAI to support AML/KYC research (p. 12). | In banking, AI value depends on guided workflows, data readiness, and oversight. | Human decision points, cited evidence, audit logging, and explicit scope boundaries. | DBS is a large Singaporean bank; we use it as a governance reference, not as proof of Indian regulatory compliance. |
| **Inside Erica: Bank of America** | Erica started with bounded tasks and curated data (pp. 4–5), built trust through clear human hand-offs (p. 8), and faced new questions when expanding to higher-stakes wealth work (p. 12). | Begin with a bounded copilot use case and define the human hand-off. | InvestigateIQ has a defined investigator workflow and a human decision panel. | Erica is customer-facing at enterprise scale; InvestigateIQ supports internal investigators only. |
| **To Catch a Thief: Explainable AI in Insurance Fraud Detection** | Fraud screening depends on anomaly and network evidence, an investigator review funnel, and outputs that users can explain (pp. 4, 7–11). | A risk signal needs explanation and evidence; it is not itself a final accusation. | Evidence statuses, citations, grounding validation, and human case disposition. | Insurance fraud detection differs from AML; we borrow the explainability principle, not the algorithm or performance claims. |
| **McCormick AI product development** | McCormick combined fragmented expert knowledge and data with AI to speed work; AI augmented specialists rather than replacing them. | Use AI to make expert work faster while keeping the professional responsible for the final judgment. | The copilot assembles and summarises evidence; the investigator remains responsible for the decision. | The industry and task differ; the shared principle is augmentation of domain expertise. |
| **AI and Strategy: Lessons from Real-World Cases** | AI does not automatically create value; outcomes depend on a real problem, viable data, workflow fit, and execution choices. | Avoid “AI for AI’s sake”; choose one concrete workflow and define its evidence and limitations. | The narrow AML investigation scope, synthetic data, working workflow, and stated non-goals. | The case is a strategic lens, not a direct technology specification. |
| **BMW: Leading the Agentic Enterprise** | BMW's purchasing assistant extracted supplier information and prepared an assessment while the buyer remained responsible for review and the next ERP action (pp. 7–8); the case then asks whether speeding up tasks changes the overall operating model (pp. 9–10). | Show a useful internal copilot and keep the human decision step visible. | The report drafts findings; the investigator accepts/rejects them and records a decision. | No measured 20-minute-to-30-second gain exists for our prototype; BMW's setting and scale differ. |
| **Bairong: AI agent workforce** | Bairong describes role-specific agents, orchestration, performance feedback, and human exception handling (pp. 7–9, 12). | Give components explicit responsibilities and observe what each stage did. | Six named stages and audit events in `agents/orchestrator.py`. | Our fixed sequence has no autonomous staffing model, dynamic delegation, or agent KPIs. |
| **Module 4 strategy and change material** | AI fails when pilots lack business value, data readiness, ownership, governance, adoption planning, and outcome measurement. | Present the project as a successful *prototype* with a roadmap, not as a completed enterprise transformation. | Blueprint, delivery plan, risk log, acceptance criteria, analytics, and documented open gaps. | We have not conducted a real organizational change program or measured staff adoption. |

---

## 5. The strongest answer to “Why did you choose this approach?”

> We did not use one AI method for everything. We used a hybrid design because an AML investigation contains different kinds of work. SQLite and Python retrieve and calculate facts consistently. The knowledge base retrieves the relevant synthetic playbook guidance. Gemini turns the supplied evidence into a structured, readable draft. The grounding validator checks selected citations and claims, and flags issues for review. Finally, the human investigator makes the decision and records a reason. This was the best fit because AML is a high-stakes workflow where a fluent answer is not enough; the output must be explainable and reviewable.

## 6. The strongest answer to “Why not use only ChatGPT/Gemini?”

> A plain chatbot can write a convincing answer, but it may not know which customer record, transaction, document, or guidance supports that answer. We therefore give the model controlled context from our database and synthetic playbook, check cited IDs and selected claims, and leave the final decision to a human. The model is used for synthesis, not as an unrestricted decision-maker.

## 7. Topics that are in the course but are **not** claimed in this prototype

This honesty is a strength, not a weakness.

- We do **not** train a neural network or a custom machine-learning fraud model.
- We do **not** use a vector database, deep learning model, digital twin, IoT data stream, OCR pipeline, or graph database.
- We do **not** connect to a real core-banking system, regulator, sanction-screening provider, or customer data source.
- We do **not** perform real suspicious-transaction reporting, determine criminality, or claim RBI/FIU-IND certification.
- We do **not** claim measured reduction in investigation time, detection accuracy, or financial ROI; the dataset and outcomes are synthetic.

## 8. Source material reviewed for this map

### Primary course modules

- `Leadership_with_AI_IITB_Sept2026 v5.pdf`
- `Module 1 Session 1 The Digital Enterprise Context for AI_version 2 (1).pdf`
- `Module 1 Session 2 Integration, Automation and Security foundations.pdf`
- `Module 2 Session 1 Understanding AI, intelligence and problem solving (1).pdf`
- `Module 2 Session 2 Generic problems and applications, core AIML techniques n algorithms.pdf`
- `Module 2 Session 3 Neural networks, DL and Generative AI.pdf`
- `Module 2 Session 4 Agentic AI and Combining AI Approaches.pdf`
- `Module 3 Session 1 Personal and Professional Productivity.pdf`
- `Module 4 Chapter 1 - Identifying AI Opportunities and Designing Strategy - vF.pdf`
- `Module 4 Session 2 - Leading AI-Driven Organizational Change - vF.pdf`
- `Module 4 Session 3 - Business Models, Build-vs-Buy and Execution -vF.pdf`
- `PDFs to JSON Why.pdf`

### Most relevant cases

- `AI Financial Crime Investigation Copilot_5.pdf`
- `Vehicle Loan Agentic AI Capstone Blueprint.pdf`
- `DBS' AI Journey.pdf`
- `Inside Erica The Making Of Bank.pdf`
- `To Catch a Thief Explainable AI in Insurance Fraud.pdf`
- `AI and Strategy- Lessons from Real-World Cases.pdf`
- `Abstract_McCormick_AI_Product_Development_Case_study  published by HBR (1).pdf`
- `BMW Group (A).pdf`
- `Bairong 1,200 Human and 200,000 AI Agent Employees.pdf`

Other supplied cases are useful as broad strategy references. They will not be used as direct evidence unless a specific slide or answer needs them.

See [16-Course-Source-Evidence-Register.md](16-Course-Source-Evidence-Register.md) for page anchors, the full case-study screening, exact implementation checks, and gaps. The case PDFs stay in the private course folder, outside GitHub.

---

## 9. Next use of this document

After the team meeting, turn the applicable rows above into:

1. a one-page presentation map;
2. simple speaking notes for the chosen presenter;
3. a code-and-database explanation guide; and
4. a final “results, limitations, and next steps” section.
