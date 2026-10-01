# Course source evidence register — InvestigateIQ

**Status:** research notes, 30 September 2026.
**Private source location:** `C:\D\IIT Mumbai` (outside this Git repository).
**Use:** trace each project claim to course material and to implementation evidence. Page numbers below refer to PDF page order, starting at 1. They are navigation aids; the presentation should paraphrase the concepts, not reproduce licensed slides or cases.

## Verification rule

Use three labels when discussing a course topic:

- **Implemented:** an exact code, data, or UI path demonstrates it.
- **Design principle:** a case offers an analogy or rationale, but does not prove our result.
- **Future validation:** a sensible next step with no present outcome data.

An attractive case-study analogy is not evidence that InvestigateIQ is accurate, fast, compliant, or adopted. Those require our own tests and measurements.

## A. The course materials that most directly govern our design

| Source | Pages to use | Course point | Project evidence / status |
|---|---:|---|---|
| `Leadership_with_AI_IITB_Sept2026 v5.pdf` | 17, 23, 26–27, 42–45, 51, 64 | Banking AI has high consequences; measure outcomes; assign autonomy level; verify agents; control data and decisions; redesign work. | **Implemented partly:** human decision, evidence references, audit trail, fictional data. **Future validation:** time saved, decision quality, bank risk approval. |
| `Module 1 Session 1 The Digital Enterprise Context for AI_version 2 (1).pdf` | 2, 4, 50 | AI needs a usable data and workflow foundation. | **Implemented partly:** source workbook, SQLite tables, connected investigation page. **Future validation:** real data ownership, APIs, access controls. |
| `Module 1 Session 2 Integration, Automation and Security foundations.pdf` | 2, 11, 14, 16 | End-to-end work goes from trigger through decision, routing, execution, and audit; human and security controls cut across it. | **Implemented partly:** case alert, sequential pipeline, human action, audit log. **Future validation:** bank-grade identity, external integration, resilience. |
| `Module 2 Session 1 Understanding AI, intelligence and problem solving (1).pdf` | 2, 14, 40 | Choose the type of intelligence deliberately; model entities and metadata; recognize nondeterminism and explainability risk. | **Implemented:** customer/account/transaction/case IDs and narrow AI duties. **Gap:** source data quality remains imperfect. |
| `Module 2 Session 2 Generic problems and applications, core AIML techniques n algorithms.pdf` | 2, 18, 60, 80 | Rules, knowledge reasoning, and model comparison solve different classes of problems. | **Implemented partly:** deterministic analysis and retrieved playbooks. **Not implemented:** a trained fraud classifier or quantified confusion matrix. |
| `Module 2 Session 3 Neural networks, DL and Generative AI.pdf` | 2, 55 | GenAI needs context and verification; RAG and fine tuning serve different needs. | **Implemented:** Gemini produces a structured draft using retrieved playbook chunks. **Not implemented:** model fine tuning or a custom neural network. |
| `Module 2 Session 4 Agentic AI and Combining AI Approaches.pdf` | 2, 13, 17, 20 | An agent needs a multistep goal, tools, state, and potentially an adaptive path; fixed steps may simply be workflow automation. | **Implemented partly:** six specialist components and a fixed orchestrator with tool/data access. **Gap:** no independent dynamic planning or runtime tool selection. |
| `Module 3 Session 1 Personal and Professional Productivity.pdf` | 2, 12, 20, 30, 40 | Combine document retrieval with structured data and human approval; give the model context, task, constraints, format, and a quality check. | **Implemented partly:** playbook retrieval, SQLite evidence, JSON report schema, human decision. **Gap:** no MCP, enterprise SSO, or ERP integration. |
| `Module 4 Chapter 1 - Identifying AI Opportunities and Designing Strategy - vF.pdf` | 13, 19, 21, 27 | Rank opportunities by value and feasibility, embed AI into workflows, treat data quality and controlled autonomy as strategic constraints. | **Implemented partly:** narrow case workflow and guardrails. **Gap:** only an academic use-case hypothesis, no bank integration or measured value. |
| `Module 4 Session 2 - Leading AI-Driven Organizational Change - vF.pdf` | 18, 25, 28, 30, 37 | Leaders need data readiness, ownership, model-limit literacy, and clear AI/human decision boundaries; judge outcome measures. | **Implemented partly:** human decision boundary and documentation. **Gap:** no real user adoption, training, organizational owner, or outcome study. |
| `Module 4 Session 3 - Business Models, Build-vs-Buy and Execution -vF.pdf` | 17, 19–20, 26–27, 32, 34 | Keep prototype, pilot, and scale distinct; decide build/buy layer by layer; measure cost per decision and baseline improvement. | **Implemented:** prototype with chosen commodity tools and built workflow. **Gap:** no pilot baseline, cost per case, or three-year operating model. |
| `AI_Initiative_Leadership_Templates_Steps.xlsx` | Sheets `Step1_Problem_Framing` through `Step10_Monitor_Improve` | Ten-step leadership method: frame the problem, test AI fit, value, policy/data, options, economics, risks, pilot, decision, monitoring. | **Implemented partly:** vision, PRD, risks, architecture, demo. **Future validation:** populate evidence-backed AI-fit score, KPI baseline, pilot plan, and go/no-go decision after team review. Do not copy the workbook's sample HR figures as AML results. |
| `PDFs to JSON Why.pdf` | 1–2, 4–6 | Separate structured facts/tables from unstructured text to improve retrieval, calculation, and token efficiency. | **Design principle:** we keep transactional facts in SQLite and small playbook documents in searchable chunks. **Not implemented:** PDF-to-JSON conversion. |

### Pre-reading and overview files

`Module 1 Session 1 The Digital Enterprise Context for AI Prereading.pdf`, `Module 1 Session 2 Integration, Automation and Security foundations Prereading.pdf`, and `Module 2 Session 3 Pre-reading.pdf` are reading lists and external pointers. The corresponding session PDFs above are the direct course anchors. `Case studies and articles on AI.pdf` and its `(1)` copy are catalogues of cases; use the actual case files below for detailed claims. `Leadership_with_AI_IITB_Sept2026 v5.pdf` is the cross-course executive overview. `Book-HBR's 10 Must Reads on Artificial Intelligence.pdf` is a 230-page anthology; its contents include employee adoption, human values, process change, agentic work, pilot discipline, and AI failure. It is useful background, but the specific module slides above support our main claims more directly.

`Case studies 1\Case studies` contains four exact duplicate PDFs (Adobe, AI and Strategy, HBR anthology, and DBS), confirmed by file hashes against the root folder. `Case studies 1.zip` packages that collection. They add no separate evidence. The two case-study catalogues are similar finding aids, but their file sizes differ; do not count them as independent case-study evidence.

The HBR anthology is particularly relevant on three specific points: employee involvement and autonomy (PDF pp. 18–20), explicit human/AI role handoffs (p. 90), and the argument for going deep on one AI workflow rather than spreading many shallow pilots (pp. 162–164). These reinforce the module material; they do not establish a measured result for InvestigateIQ.

### The ten-step leadership workbook applied to this project

| Workbook step | Present evidence | What remains a hypothesis or follow-up |
|---|---|---|
| 1. Problem framing | Vision and PRD identify manual AML evidence assembly. | Interviews with real investigators and a measured manual baseline. |
| 2. AI fit | Hybrid rules, retrieval, generation, and human decision have a clear rationale. | Score alternative approaches against the workbook criteria with team-agreed weights. |
| 3. KPI and value | Analytics tracks synthetic alert/decision activity. | Time saved, investigation quality, false-positive handling, and cost per case on a controlled evaluation. |
| 4. Policy and data | Fictional dataset and stated prototype boundaries. | Real bank data classification, access rights, retention, and India-specific legal review. |
| 5. Capability options | Streamlit, SQLite, FTS5, Gemini, Railway choices are documented. | Enterprise build/buy/partner decision with IT and compliance owners. |
| 6. Economics and value | Cached reports reduce demo API dependence. | Model/API and operations cost, savings, and ROI calculation. |
| 7. Risk and stakeholders | Personas and risk register exist. | Real stakeholder validation and risk owner sign-off. |
| 8. Pilot/PoC | Working academic prototype and test scenarios. | A controlled pilot charter with real users, data, success criteria, and approvals. |
| 9. Management decision | Capstone scope and acceptance criteria exist. | A formal proceed/modify/stop decision based on pilot evidence. |
| 10. Monitor and improve | Basic audit events and analytics exist. | Ongoing quality, drift, cost, incident, and user adoption monitoring. |

## B. Case studies: situation → choice → reason → project relevance

| Case and page anchors | Situation, choice, and why | Responsible application to InvestigateIQ | Strength |
|---|---|---|---|
| `AI Financial Crime Investigation Copilot_5.pdf`, pp. 1–5 | This is a **sample capstone blueprint**, not an operating bank case. It decomposes financial-crime investigation into business, data, AI, technology, governance, and execution blueprints with human review. | Closest structural reference for our alert-to-decision blueprint. Check that our smaller prototype can explain each layer and its omissions. | Direct academic template; not evidence of industry results. |
| `Vehicle Loan Agentic AI Capstone Blueprint.pdf`, pp. 1–4, 9–12 | Another **sample capstone blueprint** demonstrates process decomposition, data ownership, guardrails, human authority, and roadmap for loan processing. | Use its blueprint discipline and authority matrix; do not borrow vehicle-loan features such as OCR or underwriting. | Strong method reference; different process. |
| `DBS' AI Journey.pdf`, pp. 4, 6, 8–12 | DBS moved away from unreliable open-ended chatbot responses toward guided conversations; it consolidated fragmented data, developed responsible-use review, and kept GenAI under human oversight. The case explicitly mentions AML/KYC research support. | A bank-specific rationale for bounded employee-facing assistance, data foundations, human oversight, and measured value. | Very strong analogy, but Singapore governance is not Indian regulatory authority. |
| `Inside Erica The Making Of Bank.pdf`, pp. 4–5, 8, 12 | BofA built a constrained banking assistant around reliable data and trust, guided users to human service where appropriate, and faced new questions on moving into higher-stakes wealth work. | Define one clear internal user and a human handoff; make capability limits visible. | Strong design analogy, different users and scale. |
| `To Catch a Thief Explainable AI in Insurance Fraud.pdf`, pp. 2–4, 7–11 | Insurers needed fraud screening that investigators could understand and use. The case discusses anomaly detection, relationships, the fraud-review funnel, and explainability. | An AML alert is a lead for investigation; show evidence status and reasons before human escalation. | Strong high-stakes analogy; insurance fraud is a different legal domain. |
| `AI and Strategy- Lessons from Real-World Cases.pdf`, pp. 2–12 | The set includes successful and weak AI strategies; technology fit, customer demand, economics, and execution explain the differences. | Explain why a narrow investigator workflow and explicit validation matter more than adding features for their own sake. | Strong strategic lens; not a technology recipe. |
| `BMW Group (A).pdf`, pp. 6–10 | BMW's Offer Analyst shortened document handling while buyers retained review and ERP action; leadership then questioned whether isolated task gains redesigned the full process. | Use AI for evidence assembly and drafting, but show the full alert-to-decision workflow and human handoff. | Strong workflow and authority analogy; do not import BMW performance numbers. |
| `Bairong 1,200 Human and 200,000 AI Agent Employees.pdf`, pp. 4, 7–9, 12, 18 | Bairong used named agent roles, orchestration, feedback, and human exception handling at scale. | Name each component's job and log its output; discuss monitoring and ownership. | Useful conceptual analogy; our system is fixed-sequence and has no agent workforce or KPI management. |
| `McCormick & Co.pdf`, pp. 7–10; `Abstract_McCormick_AI_Product_Development_Case_study  published by HBR (1).pdf`, pp. 1–4 | Product developers had fragmented knowledge and too many formulation options; AI suggested possibilities, while expert trust and validation remained management challenges. | AI can organize evidence and draft hypotheses that experts inspect. | Broad human-augmentation analogy; industry differs. The abstract is secondary to the full case. |
| `AI at Scale PepsiCo's Balancing Act of Growth.pdf`, pp. 3, 7–10 | PepsiCo invested in unified data, governance, multiple AI use cases, and explicit value choices while balancing cost and risk. | Data quality and outcome measurement should come before any scale claim. | Good leadership analogy; no direct AML method. |
| `Adobe-GenAI Opportunity or Threat.pdf`, pp. 8–12 | Adobe weighed generative AI opportunities against content rights, customer trust, product fit, and how to build responsibly. | Use approved/synthetic content in a bounded prototype; explain vendor/data choices. | General strategic and rights-management analogy. |
| `Persistent Systems Creating Value.pdf`, pp. 2–9 | Talent fulfilment faced volatile skill demand and regulatory change; agentic tools coordinated work while role design and governance mattered. | A future operating model would need named owners, exception handling, and change management. | Future-stage analogy; do not claim our prototype has its operational results. |
| `THE YES Reimagining the Future.pdf`, pp. 1–5, 9–11 | The retail AI product needed to prove user experience and recommendation value before scaling acquisition. | Validate investigator usefulness before claiming adoption. | General validation lesson; retail recommendation differs from AML. |
| `The strategic transformation of John Deere.pdf`, pp. 1–2, 7–8 | Deere's AI transformation required customer data and raised ownership/privacy concerns. | Treat bank data access and governance as a production prerequisite. | General data-governance lesson; no IoT use in our prototype. |
| `The Trillion-dollar Reinvention.pdf`, pp. 1–3, 8–10 | Walmart transformed processes, data, and channels over years rather than depending on one new tool. | Position InvestigateIQ as one bounded workflow in a longer transformation roadmap. | Broad operating-model analogy. |
| `Ashok_Leyland_Digital_Twin_Operational_Excellence_Summary.pdf`, pp. 1–3; `Ashoka leyland  Case study.pptx`, slides 1–11 | Connected vehicle data and digital twins helped Ashok Leyland improve service and explore lifecycle value. | The transferable lesson is to begin with a specific operational pain and data flow. | Peripheral analogy. We do not use a digital twin, IoT, telematics, or its revenue model. |
| `Tata  steel  digital twin blog.docx`, sections “Digital Foundation Behind AI” and “Inhouse Generative AI Design” | Tata Steel described its data/AI backbone and restrictions around exporting sensitive operational data. | Reminds us to treat real bank data and model deployment as future governance decisions. | Peripheral analogy. This is a copied article, not a professor-authored case or authority for banking law. |
| `AI and ML enabled  Smart Manufacturing (1).pdf`, pp. 1, 79–90 | The lecture uses manufacturing cases to show stepwise AI implementation and human-centred transformation. | Apply the stage-gate and human-workflow lesson only. | Peripheral domain material; no smart-manufacturing technology is in this app. |

## C. Exact technical claims checked against the repository

| Claim we may make | Observed proof | Limit |
|---|---|
| There is a real database behind the app. | `data/build_database.py` loads the Excel sheets into `data/investigateiq.db`; current SQLite inspection found 552 customers, 654 accounts, 9,950 transactions, 42 alerts, 24 playbook documents, and 57 playbook chunks. | The data is synthetic and some alert dates/trigger links are incomplete. |
| The project uses retrieval-augmented generation. | `data/knowledge_search.py` searches an FTS5 index; `agents/evidence_agent.py` retrieves scenario-specific chunks; `agents/investigation_summary_agent.py` includes them in the model prompt. | Retrieval is keyword/BM25, not semantic vector search. The playbooks are synthetic. |
| The model drafts a structured report. | `agents/investigation_summary_agent.py` defines the response schema and calls `agents/llm_client.py`. | The LLM can still err. |
| The report is checked. | `agents/grounding_validator.py` checks cited transaction IDs, presence of citations on Verified findings, playbook IDs for next steps, and selected ratio patterns. It removes specified verdict-like wording, downgrades Verified findings when only out-of-window background transactions are available, and returns `REVIEW_REQUIRED` when notes exist; cached reports are rechecked on replay. Chat uses the same wording guardrail. | It does not prove every sentence true or that a cited transaction directly supports a claim. Mismatched ratio prose is flagged and the affected Verified finding is downgraded, but human review is still required. |
| Humans keep final case disposition. | `pages/2_Investigation_Demo.py` displays the decision panel; `data/runtime_db.py` requires rationale and now commits the action and its audit event in one SQLite transaction; `tests/test_runtime_db.py` exercises success and rollback. | Identity and roles are mock-level; this is not a bank-grade approval chain or immutable ledger. |
| Six specialist components are orchestrated. | `agents/orchestrator.py` calls six classes sequentially and logs their stages. | Most stages are deterministic data-gathering functions, not independent LLM agents with adaptive planning. |

## D. Current gaps that course material makes visible

1. **Baseline and results:** Course sources require outcome measures. Current counts, reports, and working screens prove technical operation, but not faster investigations or better detection. A timed comparison with a manual synthetic-case workflow is a future evaluation task.
2. **Data quality:** Most source alerts lack a trigger transaction ID, and some have no transaction inside the review window. The fallback is labelled, but this is a data-readiness gap that should be candidly shown.
3. **India-specific policy:** Synthetic playbooks are teaching material. Any RBI/FIU-IND claim needs a separately verified official source and a human compliance review before being shown as bank policy.
4. **Real users and integration:** This is an academic prototype. There is no bank data feed, production access control, operational investigator trial, or regulatory filing connection.
5. **Agent language:** The course's agentic-fit test (Module 2 Session 4, p. 17) argues for precise wording: specialist components with sequential orchestration, with limited LLM reasoning in the summary and chat.
6. **Prototype web security and upkeep:** A local Streamlit smoke test succeeded, but the installed runtime warned that `.streamlit/config.toml` disables CORS and that older UI calls are deprecated. These need a deliberate security/configuration review before any production-security claim; they are not a reason to add a regulatory-compliance claim now.

## E. File-by-file inventory and relevance

This inventory covers each top-level item supplied in `C:\D\IIT Mumbai` as of 30 September 2026. “Focused reading” means the pages tied to this capstone were checked; it does **not** mean every page of a long book was read line by line. “Screened” means its topic and useful portions were assessed, but it is not a primary source for the demo. The source files remain private; these are original notes, not copies.

| Supplied file | What it is / review depth | Value to InvestigateIQ | Pending or limit |
|---|---|---|---|
| `Leadership_with_AI_IITB_Sept2026 v5.pdf` | Course overview; focused reading. | Core language for autonomy, high-stakes work, value and guardrails. | Use page-specific references in speaking notes. |
| `Module 1 Session 1 The Digital Enterprise Context for AI_version 2 (1).pdf` | Digital-enterprise module; focused reading. | Data foundation and workflow context. | Do not imply enterprise integration exists. |
| `Module 1 Session 1 The Digital Enterprise Context for AI Prereading.pdf` | Pre-reading pointers; screened. | Background for the module. | Follow cited external readings only if a final claim needs them. |
| `Module 1 Session 2 Integration, Automation and Security foundations.pdf` | Integration module; focused reading. | Alert-to-action workflow and audit/control pattern. | Production security and integration remain gaps. |
| `Module 1 Session 2 Integration, Automation and Security foundations Prereading.pdf` | Pre-reading pointers; screened. | Background only. | Not direct evidence that a control is implemented. |
| `Module 2 Session 1 Understanding AI, intelligence and problem solving (1).pdf` | AI foundations module; focused reading. | Entity modelling and deliberate choice of AI method. | Data-quality claims need our own checks. |
| `Module 2 Session 2 Generic problems and applications, core AIML techniques n algorithms.pdf` | AI-methods module; focused reading. | Explains when rules, knowledge, or learned models fit. | No trained fraud classifier here. |
| `Module 2 Session 3 Neural networks, DL and Generative AI.pdf` | GenAI module; focused reading. | RAG versus fine-tuning and constrained synthesis. | No custom neural network or fine-tuning here. |
| `Module 2 Session 3 Pre-reading.pdf` | Pre-reading pointers; screened. | Background only. | Do not treat references as course-proven implementation. |
| `Module 2 Session 4 Agentic AI and Combining AI Approaches.pdf` | Agentic-AI module; focused reading. | Most important terminology check: fixed workflow versus adaptive agent. | Correct “six AI agents” overclaim throughout final materials. |
| `Module 3 Session 1 Personal and Professional Productivity.pdf` | Productivity module; focused reading. | Structured context, retrieval, human approval. | Enterprise connectors shown in class are not built here. |
| `Module 4 Chapter 1 - Identifying AI Opportunities and Designing Strategy - vF.pdf` | Strategy module; focused reading. | Value–feasibility and narrow use-case choice. | Real-bank use-case scoring remains future work. |
| `Module 4 Session 2 - Leading AI-Driven Organizational Change - vF.pdf` | Change-leadership module; focused reading. | Human authority, adoption, outcome measurement. | No real investigator adoption evidence. |
| `Module 4 Session 3 - Business Models, Build-vs-Buy and Execution -vF.pdf` | Execution module; focused reading. | Prototype/pilot/scale distinction, layered build/buy. | Cost per case and pilot evidence remain open. |
| `AI_Initiative_Leadership_Templates_Steps.xlsx` | Ten-step leadership workbook; all 14 sheets inventoried, relevant steps read. | Management framework for problem, data, economics, risk, pilot and decision. | Sample HR numbers are not our results; complete an AML-specific version later if useful. |
| `PDFs to JSON Why.pdf` | Data-format explainer; focused reading. | Rationale for structured facts plus searchable text. | PDF-to-JSON conversion is not implemented. |
| `AI Financial Crime Investigation Copilot_5.pdf` | Sample capstone blueprint; focused reading. | Closest process/blueprint reference. | Not evidence that a bank has deployed this system. |
| `Vehicle Loan Agentic AI Capstone Blueprint.pdf` | Sample capstone blueprint; focused reading. | Useful scope, authority and execution structure. | Loan/OCR/underwriting features do not transfer directly. |
| `DBS' AI Journey.pdf` | Banking case; focused reading. | Guided conversation, data foundation, responsible-use oversight. | Singapore case, not Indian regulatory authority. |
| `Inside Erica The Making Of Bank.pdf` | Banking case; focused reading. | Bounded assistance and human handoff. | Customer-facing enterprise service, unlike our internal prototype. |
| `To Catch a Thief Explainable AI in Insurance Fraud.pdf` | Insurance-fraud case; focused reading. | Explanation, evidence and investigator review funnel. | Different industry and legal task from AML. |
| `BMW Group (A).pdf` | Industrial purchasing-agent case; focused reading. | AI prepares work; responsible buyer reviews and acts. | Its reported speed gains cannot be used as our results. |
| `Bairong 1,200 Human and 200,000 AI Agent Employees.pdf` | Agent-workforce case; focused reading. | Role separation, orchestration and exception handling. | Our workflow is fixed, not an autonomous agent workforce. |
| `McCormick & Co.pdf` | Product-development case; focused reading. | AI augmentation of experts and trust. | A broad analogy, not AML performance evidence. |
| `Abstract_McCormick_AI_Product_Development_Case_study  published by HBR (1).pdf` | Short case abstract; screened alongside full case. | Quick pointer to McCormick's AI/expert story. | Prefer the full case for factual claims. |
| `AI and Strategy- Lessons from Real-World Cases.pdf` | Multi-case strategy teaching material; focused reading. | Fit, economics and execution as criteria. | Strategic lens only, not product validation. |
| `AI at Scale PepsiCo's Balancing Act of Growth.pdf` | Enterprise AI case; screened relevant pages. | Data governance and value tradeoffs. | No direct AML method. |
| `Adobe-GenAI Opportunity or Threat.pdf` | GenAI strategy case; screened relevant pages. | Rights, trust and product-fit considerations. | No direct banking procedure or Indian policy. |
| `Persistent Systems Creating Value.pdf` | Workforce/agentic case; screened relevant pages. | Roles, exceptions and organizational governance. | Future operating-model analogy only. |
| `THE YES Reimagining the Future.pdf` | Retail recommendation case; screened relevant pages. | Validate user value before scale. | Recommendation algorithms are not used here. |
| `The strategic transformation of John Deere.pdf` | Digital transformation case; screened relevant pages. | Data rights and ownership questions. | No IoT/agriculture feature in this app. |
| `The Trillion-dollar Reinvention.pdf` | Walmart transformation case; screened relevant pages. | Workflow and operating-model change beyond a tool. | Broad strategy reference, not AML evidence. |
| `Ashok_Leyland_Digital_Twin_Operational_Excellence_Summary.pdf` | Digital-twin case summary; screened relevant pages. | Start from operational pain and available data. | Digital twins and telematics are out of scope. |
| `Ashoka leyland  Case study.pptx` | Eleven-slide Ashok Leyland deck; slides screened. | Cross-check of the operational case. | Peripheral; not a banking reference. |
| `Tata  steel  digital twin blog.docx` | Reproduced industry blog; relevant sections screened. | Data backbone and sensitive-data deployment choices. | Not a banking regulation or original course case. |
| `AI and ML enabled  Smart Manufacturing (1).pdf` | Manufacturing teaching deck; screened relevant portions. | Staged implementation and people/process design. | Smart-factory technologies are not built here. |
| `Book-HBR's 10 Must Reads on Artificial Intelligence.pdf` | 230-page anthology; table of contents and selected relevant pages checked. | Employee involvement, handoffs and narrow pilots. | Not a claim of complete line-by-line review. |
| `Case studies and articles on AI.pdf` | Case catalogue; screened. | Finding aid for the substantive cases. | The list itself is not independent case-study evidence. |
| `Case studies and articles on AI (1).pdf` | Second case catalogue; screened. | Cross-check of assigned readings. | Similar purpose, but not assumed to be a byte-identical duplicate. |
| `Case studies 1.zip` | Archive of the four case PDFs in its companion folder; contents checked against root copies. | No new substantive source. | Do not count duplicate files as extra evidence. |
