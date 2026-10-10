/* Build the standalone InvestigateIQ Product Blueprint (.docx).
   This document embeds fresh current-product captures so it can be shared
   independently of the local walkthrough-capture directory. */
const fs = require("fs");
const path = require("path");
const {
  AlignmentType, BorderStyle, Document, Footer, Header, HeadingLevel,
  ImageRun, Packer, PageBreak, PageNumber, Paragraph, ShadingType,
  Table, TableCell, TableRow, TextRun, WidthType,
} = require("docx");

const root = path.resolve(__dirname, "..");
const screens = path.join(root, "assets", "walkthrough_screens");
const output = path.join(root, "Product Docs", "InvestigateIQ_Product_Blueprint.docx");

const navy = "16335D";
const blue = "2E65C5";
const lightBlue = "EAF2FF";
const pale = "F6F9FE";
const teal = "0B8C88";
const gold = "B77900";
const red = "B4232C";
const grey = "63738D";
const pageWidth = 9360;
const thinBorder = { style: BorderStyle.SINGLE, size: 6, color: "B7CBEA" };

function text(value, options = {}) {
  return new TextRun({ text: value, font: "Aptos", size: options.size || 21,
    bold: !!options.bold, color: options.color || navy, italics: !!options.italics,
    break: options.break });
}
function p(children = [], options = {}) {
  return new Paragraph({ children: Array.isArray(children) ? children : [children],
    spacing: { before: options.before ?? 0, after: options.after ?? 140, line: options.line ?? 276 },
    alignment: options.alignment, style: options.style, numbering: options.numbering,
    border: options.border });
}
function h(value, level = 1) {
  return new Paragraph({ text: value,
    heading: level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
    spacing: { before: level === 1 ? 300 : 210, after: 130 },
  });
}
function bullet(value, level = 0) {
  return p(text(value), { numbering: { reference: "bullets", level }, after: 55 });
}
function codeLine(value) {
  return new Paragraph({ children: [new TextRun({ text: value, font: "Consolas", size: 17, color: "17365D" })],
    shading: { type: ShadingType.CLEAR, color: "EAF2FF", fill: "EAF2FF" },
    spacing: { before: 0, after: 0, line: 230 }, indent: { left: 220, right: 220 } });
}
function callout(title, body, color = blue) {
  return new Table({ width: { size: pageWidth, type: WidthType.DXA }, columnWidths: [pageWidth],
    rows: [new TableRow({ children: [new TableCell({ width: { size: pageWidth, type: WidthType.DXA },
      borders: { top: thinBorder, bottom: thinBorder, left: { ...thinBorder, color }, right: { ...thinBorder, color } },
      shading: { type: ShadingType.CLEAR, color: "F4F8FF", fill: "F4F8FF" },
      margins: { top: 130, bottom: 130, left: 180, right: 180 }, children: [
        p(text(title, { bold: true, color, size: 20 }), { after: 45 }),
        p(text(body, { size: 19, color: navy }), { after: 0, line: 254 }),
      ] })] })] });
}
function cell(value, width, opts = {}) {
  const children = Array.isArray(value) ? value : [p(text(value, { bold: !!opts.bold, color: opts.color || navy, size: opts.size || 18 }), { after: 0, line: 230 })];
  return new TableCell({ width: { size: width, type: WidthType.DXA }, children,
    shading: opts.shade ? { type: ShadingType.CLEAR, color: opts.shade, fill: opts.shade } : undefined,
    margins: { top: 90, bottom: 90, left: 110, right: 110 }, borders: { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder } });
}
function table(headers, rows, widths) {
  return new Table({ width: { size: pageWidth, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: headers.map((item, index) => cell(item, widths[index], { bold: true, color: "FFFFFF", shade: navy })) }),
      ...rows.map(row => new TableRow({ children: row.map((item, index) => cell(item, widths[index], { shade: row._shade })) }))] });
}
function image(name, caption, width = 640, height = 360) {
  const file = path.join(screens, name);
  if (!fs.existsSync(file)) throw new Error(`Missing Blueprint screenshot: ${name}`);
  return [
    new Paragraph({ children: [new ImageRun({ data: fs.readFileSync(file), type: path.extname(file).slice(1), transformation: { width, height } })], alignment: AlignmentType.CENTER, spacing: { before: 120, after: 55 } }),
    p(text(`Figure — ${caption}`, { size: 17, italics: true, color: grey }), { alignment: AlignmentType.CENTER, after: 180, line: 230 }),
  ];
}
function pageBreak() { return new Paragraph({ children: [new PageBreak()] }); }

const content = [];
content.push(
  new Paragraph({ children: [text("INVESTIGATEIQ", { bold: true, color: blue, size: 34 })], alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 180 } }),
  new Paragraph({ children: [text("Product Blueprint", { bold: true, size: 54, color: navy })], alignment: AlignmentType.CENTER, spacing: { after: 180 } }),
  new Paragraph({ children: [text("Evidence-to-decision workflow for fictional AML investigations", { size: 25, color: grey })], alignment: AlignmentType.CENTER, spacing: { after: 560 } }),
  callout("Blueprint purpose", "This document explains what InvestigateIQ does, how a user moves through the product, how evidence and retrieval are represented, and where human accountability remains required. It is a product and technical blueprint for a fictional teaching environment—not a deployment or regulatory filing design."),
  new Paragraph({ children: [text("Prepared for Capstone Group 7 · Leadership with AI, IIT Bombay", { size: 19, color: grey })], alignment: AlignmentType.CENTER, spacing: { before: 460, after: 70 } }),
  new Paragraph({ children: [text("Version 1.2 · 10 October 2026", { size: 18, color: grey })], alignment: AlignmentType.CENTER }),
  pageBreak(),
  h("Document guide", 1),
  p(text("The blueprint is organized for a reviewer who wants both the product story and the implementation logic.")),
  table(["Section", "What it answers"], [
    ["1. Product intent", "What problem the product demonstrates and what it deliberately does not claim."],
    ["2. User journey", "How one fictional case moves from the queue to a human decision and, if needed, Compliance."],
    ["3. Screen blueprint", "What each current page, tab, accordion, and action is for."],
    ["4. Evidence and RAG", "How source records, chunks, keyword search, citations, and the confidence score work."],
    ["5. Technical design", "The Streamlit router, SQLite stores, major calculations, safeguards, and deployment model."],
    ["6. Implementation logic", "The actual flow for OKF ingestion, chunking, FTS5/BM25 retrieval, RAG citation checks, confidence, and audit states."],
    ["7. Responsible AI", "Why the system assists review but never decides, closes, escalates, or files automatically."],
    ["8. FAQ and demo preparation", "Detailed answers for faculty questions plus a safe two-case demonstration sequence."],
  ], [2300, 7060]),
  h("Scope note", 2),
  ...[bullet("All customers, alerts, transactions, documents, and source material are fictional course data."), bullet("The product does not authenticate real users, connect to a bank, verify outside-bank records, or file a report with a regulator."), bullet("A record, citation, retrieval result, rule match, or confidence score is an aid to review—not proof that money is lawful, unlawful, fraudulent, or laundered.")],
  h("Lecturer submission alignment", 2),
  p(text("Selected submission track: Blueprint + Prototype + Detailed code + Final results. The submission includes this detailed blueprint, the working prototype and live walkthrough, the documented Streamlit/SQLite/OKF/RAG implementation logic, current screen evidence, validation results, and the 15-minute presentation materials.")),
  table(["Requirement", "How this submission addresses it"], [
    ["Detailed blueprint", "Documents the program statement, user workflow, evidence model, coding logic, responsible-AI limits, ROI measurement plan, and future roadmap."],
    ["Prototype and detailed code", "The working Streamlit prototype is demonstrated live; the Blueprint maps its router, page modules, SQLite stores, OKF ingestion, chunking, FTS5/BM25 retrieval, confidence checks, and audit-state logic."],
    ["Final results", "Provides current product captures, validation/deployment evidence, a rebuilt walkthrough plan, and measurable pilot success criteria rather than unsupported performance claims."],
    ["15-minute presentation", "Soumya is the presenter and Laxman is the backup. The concise core deck is timed for 5 minutes 35 seconds, followed by an approximately five-minute live demonstration. Questions are handled within the same 15-minute session; the three FAQ slides are an appendix used only when asked."],
  ], [2450, 6910]),
  h("Project contributors", 2),
  table(["Contributor", "Project focus"], [
    ["Rahul Chainani", "Application development and integration."],
    ["Pankaj Bharsakale", "AI workflow and evidence review."],
    ["Lakshmi Dudgikar", "Requirements and case-study mapping."],
    ["Rahul Sharma", "Quality assurance and edge cases."],
    ["Laxman Singh", "User experience and product walkthrough."],
    ["Soumya", "Team coordination and presentation."],
    ["Sweta Singh", "Course linkage and project explanation."],
  ], [2650, 6710]),
  pageBreak(),
  h("1. Product intent and design principles", 1),
  callout("Program statement", "InvestigateIQ is a capstone program to design and demonstrate a transparent, AI-assisted workflow for fictional AML case review. The program connects a stored alert to inspectable case material, source chunks, bounded assistance, evidence-confidence limitations, a named human rationale, and a separate Compliance review. Its success is measured by traceability, review clarity, and responsible human oversight—not by autonomous decisions, legal conclusions, or external filing.", teal),
  table(["Program element", "Defined commitment"], [
    ["Problem", "A monitoring alert alone does not show the supporting material, missing evidence, or accountable next step."],
    ["Primary users", "Investigators, Team Leads, Compliance Officers, and Admin reviewers in a fictional learning environment."],
    ["Delivered capability", "Queue, workspace, evidence/RAG, bounded Copilot, confidence signal, audit trail, Compliance outcomes, analytics, and protected Admin inspection."],
    ["Success measures", "A reviewer can trace a report claim to stored material, identify evidence gaps, distinguish workflow states, and record a rationale without an automated decision."],
    ["Non-goals", "No real customer data, real authentication, autonomous escalation/closure/referral, legal finding, or regulatory filing."],
  ], [2400, 6960]),
  p(text("InvestigateIQ is an AI-assisted case-investigation copilot. It turns a stored fictional alert into a transparent review workspace: the investigator can inspect the underlying case material, ask a bounded question, trace the source text behind a response, and then record an accountable human action.")),
  table(["Design principle", "Implementation consequence"], [
    ["Traceability", "Evidence & RAG exposes the source record, exact indexed chunk, retrieval method, and stated evidence gaps."],
    ["Human accountability", "Only a named investigator or Compliance Officer can submit an action, and a written rationale is required."],
    ["Bounded assistance", "The Copilot answers from stored fictional rows and chunks. It cannot independently verify documents or take workflow actions."],
    ["Clear states", "Open, escalated, source-closed, simulated closure, Compliance return, acknowledged, and referred outcomes are kept distinct."],
    ["Responsible presentation", "Evidence confidence measures support coverage for a draft, not risk, guilt, legality, or a recommended case outcome."],
  ], [2850, 6510]),
  ...image("2026_home_guest.png", "Current Home screen and reordered navigation. The workspace-entry panel establishes a display identity for the fictional session."),
  pageBreak(),
  h("2. End-to-end user journey", 1),
  p(text("A complete review follows the path below. The system preserves the difference between an alert, a drafted explanation, supporting material, a human choice, and a second human review.")),
  table(["Step", "User action", "What the system provides", "Boundary"], [
    ["1. Find work", "Use Case Queue filters or Global Search.", "Stored alert metadata, status, severity, rule labels.", "An alert is not a finding."],
    ["2. Review case", "Open Investigation Workspace and choose saved or calculated mode.", "Case context, report, validator notes, confidence, cited material.", "The AI/report does not submit a decision."],
    ["3. Inspect proof", "Open Evidence & RAG and exact chunks.", "Case records, source guidance, chunks, retrieval results, method notes.", "Citations point to supplied text; they do not authenticate it."],
    ["4. Decide", "Record request-for-information or escalation with a rationale.", "Locked recorded-action state and append-only audit history.", "Only a human can act; completed actions cannot be edited in place."],
    ["5. Second review", "A Compliance Officer acknowledges, returns, or records an onward referral.", "Outcome mapping back to the queue and audit history.", "The tool never files externally."],
  ], [850, 2250, 3500, 2760]),
  h("Case Queue: the operational starting point", 2),
  p(text("Queue cards summarize the fictional workload. Filters narrow by severity, status, scenario, and customer name. A row’s status explains where it is in the workflow; its action opens the appropriate context. Completed cases expose Evidence rather than an invitation to alter a submitted decision.")),
  ...image("2026_case_queue_table.png", "Queue filters and case table. The search field, current status, rule metadata, and action are separate controls."),
  pageBreak(),
  h("3. Investigation Workspace", 1),
  p(text("The Investigation Workspace is the main review surface. A case selector and mode control make the source of the displayed report explicit.")),
  table(["Mode", "Purpose", "Safety boundary"], [
    ["Saved report", "Replays a historical saved snapshot for a repeatable demonstration.", "It must not be confused with current index contents or a fresh model call."],
    ["Calculated", "Recomputes the review from current stored fictional rows without a model call.", "A calculation still depends on supplied data and does not verify external facts."],
    ["AI draft", "Optional live drafting mode when configured.", "A draft is subject to evidence checks and remains advisory; a human action is still required."],
  ], [1900, 4000, 3460]),
  ...image("2026_workspace_current_report.png", "Workspace report controls and validator result. Run investigation builds or replays a review; it does not record a decision."),
  h("Evidence confidence", 2),
  p(text("The evidence-confidence card is the visible responsible-AI control. It brings uncertainty into the case report instead of hiding it behind a confident sounding narrative.")),
  ...[bullet("Evidence support score: deterministic summary of how much of the draft is supported by the supplied evidence and guidance."), bullet("Evidence support: an interpretable label such as Low, paired with the count of known limitations."), bullet("Explicit prohibition: it is not a probability of crime, money laundering, legality, or the correct workflow outcome.")],
  ...image("2026_workspace_confidence.png", "Evidence confidence is shown after report generation, with score, label, limitations, and a visible human-review requirement."),
  ...image("2026_workspace_findings.png", "Case context and Evidence & Findings retain source-data warnings alongside the report material."),
  pageBreak(),
  h("4. Evidence & RAG architecture", 1),
  p(text("Evidence & RAG makes the source trail inspectable. The product uses retrieval-augmented generation in a narrow, transparent form: it finds relevant stored passages first, then lets the user inspect the passages that informed a draft or answer.")),
  table(["Tab", "Primary purpose", "Reviewer takeaway"], [
    ["Case records", "Inspect the selected case’s records, evidence gaps, indexed passages, and transaction scope.", "Know what is present, what is illustrative, and what is missing."],
    ["Rule Lab", "Explain calculated signals and preview logic.", "A rule match calls for review; it is not a verdict."],
    ["Fictional Intake", "Show the separate generated packet and its calculated evidence boundary.", "Generated data is labeled separately from imported alert data."],
    ["Source & chunks", "Open source guidance and exact chunk boundaries.", "A citation can be traced to exact text."],
    ["Search the index", "Run a keyword query against stored chunks.", "Search results are inspectable leads, not automatically true answers."],
    ["Method & code", "Explain ingestion, chunking, retrieval, context gathering, and checks.", "The implementation is visible and its limits are stated."],
  ], [1750, 3800, 3810]),
  ...image("2026_evidence_case_records.png", "Evidence & RAG overview and its four-step evidence-review flow."),
  ...image("2026_evidence_source_chunks_detail.png", "Source & chunks shows exact stored chunk boundaries and labels instead of only an AI summary."),
  h("Retrieval logic in plain language", 2),
  p(text("Guidance documents are stored as synthetic source records. The builder creates metadata chunks and body chunks, indexes their text in SQLite FTS5, and uses BM25 ranking for a keyword query. Case records are also indexed in their own scope. A retrieved identifier can be checked against the selected source set before a cited report element is accepted.")),
  codeLine("source document  →  metadata/body chunks  →  SQLite FTS5 index"),
  codeLine("case scenario + question  →  scoped keyword search  →  BM25-ranked passages"),
  codeLine("retrieved passage IDs  →  draft/answer citations  →  human opens exact text"),
  pageBreak(),
  h("5. The Copilot and human decision boundary", 1),
  p(text("The floating InvestigateIQ Copilot gives a page-aware entry point to bounded case questions. It is intentionally separate from the decision form: a useful answer is not the same thing as a workflow action.")),
  ...image("2026_evidence_copilot_open.png", "The floating Copilot opens over the current page while retaining the selected case context."),
  table(["Can do", "Cannot do"], [
    ["Summarize stored fictional records and retrieved source chunks.", "Verify a source document, counterparty, KYC record, or outside-bank fact."],
    ["Point the user to exact IDs, chunks, and evidence gaps.", "Conclude that funds are lawful, unlawful, fraudulent, or laundered."],
    ["Help the user frame a question or understand a result.", "Close, escalate, refer, submit, or file anything on the user’s behalf."],
  ], [4680, 4680]),
  h("Human decision logic", 2),
  p(text("Decision controls are enabled only while the case has no final investigator action, or after Compliance returns the case for further information. On submission, the action, investigator display name, rationale, and timestamp are appended to the audit history and the form is replaced by its recorded state.")),
  codeLine("if latest_action is None or latest_action == 'compliance_return':"),
  codeLine("    require(investigator_name and rationale)"),
  codeLine("    append_human_action(case_id, selected_action, rationale)"),
  codeLine("else: show_recorded_action_and_disable_form()"),
  callout("Why the form locks", "A human decision is an accountable audit event, not a chat preference. Locking the completed form prevents a user from silently changing a recorded decision. A new permitted workflow state, such as a Compliance return, creates a new auditable action rather than overwriting the original.", teal),
  pageBreak(),
  h("6. Compliance outcomes and state mapping", 1),
  p(text("Compliance is a separate human review of investigator escalations. Its three actions have different operational meaning and need distinct queue labels.")),
  table(["Compliance action", "Queue indication", "Meaning"], [
    ["Acknowledge — no further action", "Compliance reviewed — no further action", "The escalation was reviewed; no additional action is needed in this fictional workflow."],
    ["Return to investigator", "Compliance returned — information needed", "The case goes back for more evidence or explanation before Compliance can decide."],
    ["Referred onward", "Compliance referred onward — recorded", "A human recorded an onward referral. The tool itself does not file anything with a regulator."],
  ], [2600, 3150, 3610]),
  ...image("2026_compliance_queue_detail.png", "Compliance Queue makes the separate second-review boundary visible."),
  pageBreak(),
  h("7. Analytics and Global Search", 1),
  p(text("Analytics is descriptive and uses carefully named axes. The graphs show counts and proportions in the stored fictional dataset; they are not model-quality statistics or probability estimates.")),
  table(["Graph", "X-axis / measure", "Interpretation guardrail"], [
    ["Alerts by severity", "Number of stored alerts", "Counts High, Medium, and Low labels."],
    ["Alerts by typology", "Number of stored alerts", "Counts categories such as velocity or structuring."],
    ["Alerts by current status", "Number of cases", "Counts current workflow states; source status and human state are distinct."],
    ["High-severity share", "Percentage", "Share labeled High within a typology; not probability of crime."],
    ["Stored records by month", "Number of alerts per time bucket", "Describes fictional source dates; not a risk forecast."],
    ["Recorded decisions/actions", "Saved action count", "Counts workflow events; not productivity, accuracy, or outcome quality."],
  ], [2700, 3000, 3660]),
  ...image("2026_analytics_charts.png", "Analytics graphs with readable axes and explanatory units."),
  ...image("2026_global_search.png", "Global Search returns linked fictional customers, accounts, transactions, and cases as a context-finding tool."),
  pageBreak(),
  h("8. Project roles and protected administration", 1),
  p(text("Project & Team makes responsibilities visible and keeps names separate from email addresses. The selected UI role is a display/workflow label; it is not identity authentication or an authorization grant.")),
  ...image("2026_project_team_roles.png", "The role guide: Investigator, Team Lead, Compliance Officer, and Admin."),
  h("Admin boundaries", 2),
  p(text("Knowledge Base and Rule Config are gated by a separate masked passcode. The passcode is never included in this Blueprint or automated capture. The locked screen makes the boundary apparent without turning a coursework environment into an authentication claim.")),
  ...image("2026_admin_knowledge_locked.png", "Knowledge Base locked state. The protected source-inspection area remains visibly separate from ordinary workflow pages."),
  pageBreak(),
  h("9. Technical architecture and code map", 1),
  p(text("The current product is a Streamlit application with an explicit navigation router, page modules, shared UI helpers, SQLite-backed fictional stores, and static assets. The structure favors transparent page-level logic that can be inspected during a demonstration.")),
  table(["Layer", "Representative responsibility", "Examples"], [
    ["App router", "Defines the visible order and labels of the left navigation.", "Home; Project & Team; Case Queue; Investigation Workspace; Evidence & RAG; Compliance; Analytics; Search; Admin."],
    ["Page modules", "Render the task-specific controls, tables, charts, and bounded workflow actions.", "0_Case_Queue.py, 2_Investigation_Demo.py, 8_Evidence_RAG.py, 5_Analytics.py."],
    ["Shared UI", "Banners, compact flows, status badges, help text, role behavior, theme styling, and the Copilot launcher.", "ui_common helpers and shared CSS."],
    ["Data and search", "Fictional case records, audit actions, documents, chunks, retrieval index, and calculated metrics.", "SQLite, FTS5 keyword search, BM25 ranking, deterministic calculations."],
    ["Assets and release", "Walkthrough media, screenshots, captions, deployment configuration, and reproducible builders.", "assets/, scripts/, Procfile, GitHub main branch → Railway."],
  ], [1900, 4250, 3210]),
  h("9.1 Detailed architecture: where technology and AI are used", 2),
  p(text("The architecture intentionally separates evidence retrieval, deterministic calculations, optional drafting, validation, and human workflow. This makes it possible to show what is computed from stored fictional data, what may be drafted with a model, and what remains a human responsibility.")),
  table(["Stage", "Actual component / logic", "Output and control"], [
    ["1. Stored fictional data and index", "SQLite stores the fictional case, alert, evidence, audit, OKF-source, and chunk records. FTS5 performs lexical keyword matching and BM25 ranks matching passages; no vector embedding index is used.", "A case-scoped set of inspectable rows and chunks. Retrieval finds supplied text; it does not verify truth."],
    ["2. Evidence-gathering specialists", "Alert Triage, Customer/KYC, Transaction Investigation, Relationship, and Evidence specialists read the active case and calculate or collect structured findings.", "Structured evidence and limitation inputs. These are specialist components, not CEO/CFO persona agents."],
    ["3. Investigation Summary Agent", "Combines the structured specialist outputs into a report. In optional model mode it can call Gemini; in calculated mode it creates the report without a model call.", "A clearly labelled advisory draft, never an automatic case action or final outcome."],
    ["4. Grounding Validator", "Checks known citation IDs, selected ratio claims, forbidden verdict wording, and obvious prompt-like text in supplied fields. It can downgrade unsupported verified language or remove unsafe output elements.", "Visible validation notes and safer wording. It reduces selected failure modes; it cannot guarantee factual truth or completeness."],
    ["5. Human action and audit", "A person supplies a display name and required rationale before a permitted decision is appended. Compliance can acknowledge, return, or record an onward referral as a separate human step.", "Recorded workflow state and auditable history. The display name is not authenticated identity or production RBAC."],
  ], [1850, 4850, 3660]),
  ...image("2026_data_flow_diagram_v2.svg", "Data flow: selected case evidence and retrieved knowledge converge in a validated advisory report before a named human records the next step."),
  h("9.2 Architecture execution path", 2),
  p(text("The code-level path below is the most important explanation for a faculty reviewer: specialist outputs are assembled first; an optional model can draft a summary; a validator checks the draft against controlled rules; and only then does the UI present the material for a human decision.")),
  codeLine("triage → kyc → transactions → relationships → evidence → structured_inputs"),
  codeLine("raw_report = summary_agent(structured_inputs)  # optional Gemini, or calculated mode"),
  codeLine("validated_report = grounding_validator(raw_report, known_ids, ratios, safe_text_rules)"),
  codeLine("show(validated_report, evidence_confidence, limitations); human_records_rationale()"),
  h("Navigation router", 2),
  codeLine("st.navigation([Home, Project & Team, Case Queue, Investigation Workspace,"),
  codeLine("               Evidence & RAG, Compliance Queue, Analytics, Global Search,"),
  codeLine("               Admin: Knowledge Base, Admin: Rule Config]).run()"),
  h("Confidence-score concept", 2),
  p(text("The score is calculated after a report is available. It uses deterministic support and limitation checks over the draft, supplied evidence, and retrieved guidance. Its job is to surface coverage gaps before the decision—not to rank people or forecast misconduct.")),
  codeLine("confidence = calculate_evidence_confidence(report, evidence, guidance)"),
  codeLine("display(score, support_label, known_limitations, explanation)"),
  codeLine("never interpret confidence as crime_probability or recommended_outcome"),
  pageBreak(),
  h("10. Implementation logic: from source to auditable action", 1),
  p(text("This section describes the product logic at code level. The intent is not to claim a production AML control; it is to make the demo’s data flow, retrieval logic, and workflow safeguards inspectable.")),
  h("10.1 Page routing and session context", 2),
  p(text("app.py declares the left-navigation pages and runs the selected page module. The workspace entry page stores a display name and role in Streamlit session state so an audit entry can be attributed during the fictional demo. This is a UI/session convenience, not sign-in or authorization.")),
  codeLine("selected_page = st.navigation(page_definitions).run()"),
  codeLine("st.session_state['display_name'] = entered_name     # display attribution only"),
  codeLine("st.session_state['active_case_id'] = selected_case_id"),
  h("10.2 Data model and case scoping", 2),
  table(["Store / entity", "What is kept", "How it is used"], [
    ["Case and alert rows", "Fictional case ID, customer label, status, severity, rules, and scenario.", "Drives Case Queue filters and determines the active case context."],
    ["Case evidence", "Fictional customer, account, transaction, document, and evidence-gap rows.", "Supplies the visible report and the supporting / missing-evidence checks."],
    ["Knowledge sources", "OKF source metadata plus chunk text and chunk IDs.", "Feeds Evidence & RAG and scoped keyword retrieval."],
    ["Audit actions", "Named human action, rationale, timestamp, and preceding workflow state.", "Creates the recorded decision state and Compliance history."],
  ], [2000, 3700, 3660]),
  p(text("Every relevant query carries the active case ID or source scope. That prevents a case report from silently borrowing a different case’s row or a citation from a non-retrieved source.")),
  codeLine("case_rows = load_case_rows(active_case_id)"),
  codeLine("guidance = search_chunks(question, scenario=case.scenario, case_id=active_case_id)"),
  h("10.3 OKF ingestion and chunk construction", 2),
  p(text("OKF means Open Knowledge Format in this product: a human-readable synthetic source record with stable metadata such as source ID, scenario, title, escalation criteria, version, and body text. The ingestion builder retains that metadata in a dedicated C0 chunk, then divides the body into reviewable groups of approximately two sentences. Chunk IDs preserve the parent source relationship, so a reviewer can move from a result back to the original source.")),
  codeLine("okf_source = {source_id, scenario, title, criteria, version, body}"),
  codeLine("chunks = [metadata_chunk(okf_source)] + two_sentence_chunks(okf_source.body)"),
  codeLine("save_chunk(chunk_id, source_id, scenario, chunk_text, chunk_type)"),
  h("10.4 RAG retrieval, citation, and review", 2),
  p(text("RAG means retrieval-augmented generation. InvestigateIQ uses a deliberately narrow implementation: it retrieves stored text first, ranks it with SQLite FTS5 and BM25, provides the resulting chunk IDs as context, and then displays citations that can be opened by a person. The product does not treat retrieval as verification, and it does not use a citation from outside the retrieved set.")),
  codeLine("matches = fts5_search(query_terms, scope=scenario_or_case)"),
  codeLine("ranked = bm25_rank(matches); context = top_chunks(ranked)"),
  codeLine("answer = build_bounded_answer(question, case_rows, context)"),
  codeLine("assert set(answer.cited_chunk_ids).issubset(set(context.chunk_ids))"),
  callout("Why FTS5 and BM25 are shown", "FTS5 performs full-text keyword matching inside the local SQLite index. BM25 orders the matching passages by textual relevance. They help the user locate material; they do not measure truth, legal relevance, or the probability that an alert represents wrongdoing.", teal),
  h("10.5 Report modes and evidence confidence", 2),
  p(text("The Workspace labels whether a report was replayed from a saved snapshot, calculated from current fictional rows, or drafted by an optional AI configuration. After a report exists, deterministic support and limitation checks calculate the evidence-confidence card. The display deliberately pairs the score with support label, known limitations, explanation, and a human-review instruction.")),
  codeLine("report = load_saved_snapshot(case_id)  # or calculate_from_rows(case_rows)"),
  codeLine("confidence = calculate_evidence_confidence(report, evidence, guidance)"),
  codeLine("show(score, support_label, limitations, 'Human review required')"),
  h("10.6 Human and Compliance state machine", 2),
  p(text("A decision is only persisted after the named person selects an allowed action and provides a rationale. The system appends a new audit event rather than editing an old one. The primary form then renders its recorded state. If Compliance returns the case, the next permitted investigator action becomes available as a new auditable step; the original action remains visible.")),
  codeLine("if decision_allowed(case_id): require(name and rationale); append_action(...)"),
  codeLine("else: render_recorded_state_and_disable_form()"),
  codeLine("if compliance_action == 'return': set_queue_state('information needed')"),
  h("10.7 UI, tests, and release wiring", 2),
  p(text("Shared UI helpers keep page banners, compact workflow flows, badges, tooltip treatments, theme colors, and the floating Copilot consistent. Local checks exercise the changed path before release; the repository’s intended changes are committed and pushed; Railway serves the selected main-branch revision. The deployed product is then checked by visiting the affected page rather than relying only on a successful build log.")),
  codeLine("render_page_banner(...); render_compact_flow(...); render_tooltip(...)"),
  codeLine("local_test_changed_path()  →  git push main  →  Railway health/page verification"),
  pageBreak(),
  h("11. Testing, deployment, and operational checklist", 1),
  p(text("The blueprint assumes local validation before release and a clear separation between read-only demonstration actions and persistent workflow actions.")),
  table(["Check", "Expected result"], [
    ["UI state", "Completed human decisions render as recorded and disabled; returned cases allow the next human action."],
    ["Evidence trace", "A cited source or chunk opens to exact stored material with scope and limitation context."],
    ["Confidence", "The score, support label, limitation count, and non-probability disclaimer appear together."],
    ["Accessibility/theme", "Tooltip icons and tab text remain legible in both light and dark modes."],
    ["Analytics", "Each graph has a clear title, axis/measure, and explanation of what it does not imply."],
    ["Release", "Run the application locally, validate the changed path, commit only intended files, push main, and verify the deployed response."],
  ], [2300, 7060]),
  h("Future enhancements", 2),
  ...[bullet("Add repeatable test fixtures for every state shown in the Case Queue and Compliance outcome mapping."), bullet("Add automated visual regression checks for dark mode, tooltips, responsive tables, and the full walkthrough captures."), bullet("Version evidence-confidence rules and show a score-history explanation when a report is regenerated."), bullet("Introduce real authentication and authorization only if the product moves beyond a fictional learning environment.")],
  h("12. Value realization, ROI framework, and roadmap", 1),
  p(text("The project does not claim a financial return from the fictional dataset. Instead, it provides a measurable ROI framework that a real sponsor could populate only after a governed pilot establishes baselines, costs, and observed reviewer outcomes.")),
  h("ROI measurement framework", 2),
  table(["Value lever", "Baseline and outcome to measure", "Why InvestigateIQ may help"], [
    ["Review efficiency", "Median minutes from opening an alert to locating the relevant case record and source passage.", "Queue filters, Global Search, scoped records, and exact chunk links reduce navigation and lookup time."],
    ["Rework reduction", "Number of Compliance returns or repeated evidence requests per completed review.", "Visible gaps, cited support, and required rationale make missing information explicit before an action is recorded."],
    ["Audit readiness", "Time to reconstruct the alert, cited text, decision, actor, rationale, and Compliance outcome for a sampled case.", "Append-only audit events and source/chunk traceability preserve the review path."],
    ["Quality and safety", "Rate of unsupported claims, broken citations, unclear state labels, or inaccessible controls found in review.", "Bounded Copilot behavior, deterministic confidence limits, validators, and visual QA expose issues earlier."],
  ], [2100, 3700, 3560]),
  codeLine("annual_benefit = (cases × verified_minutes_saved × loaded_hourly_rate / 60)"),
  codeLine("               + avoided_rework_cost + measurable_audit_preparation_savings"),
  codeLine("ROI % = ((annual_benefit - implementation_and_run_cost) / implementation_and_run_cost) × 100"),
  codeLine("payback_months = implementation_and_run_cost / monthly_verified_benefit"),
  callout("ROI guardrail", "These formulas are a planning model, not a reported result. The program must collect a baseline, define the cost boundary, run a pilot, and verify the observed benefit before presenting any financial ROI figure.", gold),
  h("Future roadmap", 2),
  table(["Horizon", "Priority capability", "Responsible delivery condition"], [
    ["Next iteration", "Golden-question evaluation set, citation-quality tests, and additional repeatable fixtures for every queue and Compliance state.", "Keep results tied to fictional test cases and publish failure cases alongside scores."],
    ["Pilot readiness", "Role-based authentication, authorization, evidence-lineage versioning, and confidence-rule version history.", "Use approved identity, privacy, and access-control requirements before any real data connection."],
    ["Scale with governance", "Document ingestion controls, monitored retrieval evaluation, approved integrations, and reviewer-feedback analytics.", "Establish data governance, human review protocols, model-risk assessment, and operational ownership first."],
  ], [1900, 4200, 3260]),
  h("13. Detailed FAQ", 1),
  p(text("The following answers are prepared from the implemented demo, not from hypothetical features. They are intended for faculty questions during the same 15-minute presentation session. The FAQ appendix in the deck is deliberately short; this Blueprint retains the detailed version.")),
  table(["Likely question", "Prepared answer"], [
    ["Where does the data come from?", "All customers, cases, alerts, transactions, documents, and knowledge sources are fictional course material stored locally for this demonstration. The prototype is not connected to a bank feed, a live customer system, or an external regulator."],
    ["Why is a retrieved passage relevant?", "The selected case and scenario scope the available material. SQLite FTS5 matches keywords in local text and BM25 ranks matching passages. The reviewer can open the source record or exact chunk. Relevance ranking is not truth verification."],
    ["Where is AI actually used?", "Five specialist components gather and calculate evidence inputs. The Investigation Summary Agent may make the optional Gemini call to draft a structured report. Calculated mode makes no model call. The implementation does not use CEO/CFO persona agents."],
    ["How do you reduce hallucination or unsafe output?", "The product uses supplied evidence and known source IDs, requires cited material, applies grounded wording rules, detects obvious prompt-like text, checks selected ratios and forbidden verdict language, and surfaces an evidence-confidence score with limitations. These controls reduce specific risks; they do not guarantee truth or eliminate hallucination."],
    ["Does a citation or confidence score prove that a case is legitimate or suspicious?", "No. A citation is a pointer to supplied text and the confidence score is deterministic support coverage for a draft. Neither is a probability of crime, legality assessment, or recommended workflow outcome. A named human must interpret the evidence and record the decision."],
    ["Is the demo role selector real role-based access control?", "No. It is a display/workflow label. Admin views use a limited passcode gate, but this is not production authentication or authorization. The passcode is not shown in the presentation, demo, Blueprint, or video."],
    ["What is recorded in the audit trail?", "System, AI, and human workflow events retain the active case context. A human decision requires a name and written rationale and creates a new recorded state. Compliance review creates an additional auditable step rather than overwriting the earlier decision."],
    ["What is the business value or ROI?", "The prototype does not claim savings from fictional data. A governed pilot would measure lookup time, avoided rework, audit-reconstruction time, and safety issues against an approved cost baseline before calculating financial ROI."],
  ], [3050, 7050]),
  h("Who prepares which topic", 2),
  table(["Team member", "Preparation topic", "Live-session rule"], [
    ["Soumya", "Primary presentation, product flow, and final delivery rehearsal.", "Sole presenter unless unavailable."],
    ["Laxman Singh", "Backup rehearsal, navigation, and demo safety checks.", "Presents only if Soumya is unavailable."],
    ["Rahul Chainani", "Application architecture, deployment, and integration facts.", "Prepares answers; does not create a second presenter."],
    ["Pankaj Bharsakale", "AI/RAG, model boundary, validator, and responsible-AI facts.", "Prepares answers; does not create a second presenter."],
    ["Lakshmi Dudgikar", "Requirements, cases, and user workflow mapping.", "Prepares answers; does not create a second presenter."],
    ["Rahul Sharma", "Testing, edge cases, and quality checks.", "Prepares answers; does not create a second presenter."],
    ["Sweta Singh", "Program statement, scope boundaries, and ROI framework.", "Prepares answers; does not create a second presenter."],
  ], [2050, 4250, 3800]),
  callout("Final product position", "InvestigateIQ demonstrates a transparent evidence-to-decision workflow. It helps a reviewer find, inspect, and question supplied material; it does not turn a record or model response into a legal, regulatory, or factual conclusion. The human reviewer remains responsible for the next step.", blue),
);

const document = new Document({
  creator: "Capstone Group 7",
  title: "InvestigateIQ Product Blueprint",
  description: "Product, workflow, evidence, and technical blueprint for the InvestigateIQ fictional AML investigation copilot.",
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: "bullet", text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 180 } } } }] }] },
  sections: [{ properties: { page: { margin: { top: 720, right: 720, bottom: 720, left: 720 } } },
    headers: { default: new Header({ children: [p([text("InvestigateIQ Product Blueprint", { bold: true, color: blue, size: 17 }), text("  |  Capstone Group 7", { color: grey, size: 17 })], { border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: "B7CBEA", space: 4 } }, after: 90 })] }) },
    footers: { default: new Footer({ children: [p([text("Fictional learning environment · Evidence-to-decision workflow", { size: 16, color: grey }), text("     Page ", { size: 16, color: grey }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: grey })], { alignment: AlignmentType.CENTER, before: 80, after: 0 })] }) },
    children: content }],
});

fs.mkdirSync(path.dirname(output), { recursive: true });
Packer.toBuffer(document).then(buffer => {
  fs.writeFileSync(output, buffer);
  console.log(output);
}).catch(error => { console.error(error); process.exit(1); });
