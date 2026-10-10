/* Concise 15-minute submission deck: 5:35 core slides + live demo; FAQ appendix only when asked. */
const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");
const JSZip = require("jszip");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType } = require("docx");

const root = path.resolve(__dirname, "..");
const images = path.join(root, "assets", "walkthrough_screens");
const out = path.join(root, "Product Docs");
const deckFile = path.join(out, "InvestigateIQ_Product_Presentation.pptx");
const guideFile = path.join(out, "InvestigateIQ_Deck_Presenter_Guide.docx");
const C = { navy: "0B1F3A", indigo: "173C78", blue: "2E65C5", teal: "00A79D", pale: "F6F9FE", white: "FFFFFF", ink: "12233F", grey: "63738D", mint: "E6F8F6", ice: "EAF2FF", gold: "B97800" };
const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Capstone Group 7";
pptx.company = "IIT Bombay";
pptx.subject = "InvestigateIQ concise product presentation";
pptx.title = "InvestigateIQ: concise product presentation and live demo";
pptx.lang = "en-IN";
pptx.theme = { headFontFace: "Arial", bodyFontFace: "Arial", lang: "en-IN" };

function text(s, value, x, y, w, h, o = {}) { s.addText(value, { x, y, w, h, fontFace: "Arial", fontSize: o.size || 18, color: o.color || C.ink, bold: !!o.bold, italic: !!o.italic, margin: 0, fit: "shrink", valign: o.valign || "mid", align: o.align || "left", isTextBox: true }); }
function box(s, x, y, w, h, fill = C.white, line = fill) { s.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: line, transparency: line === fill ? 100 : 0, width: 1 } }); }
function footer(s, n, dark = false) { text(s, `InvestigateIQ  |  Capstone Group 7  |  ${n} of 12`, 0.55, 7.12, 4.0, 0.16, { size: 8.5, color: dark ? "AFC9EC" : C.grey }); text(s, "Fictional AML investigation learning environment", 8.25, 7.12, 4.45, 0.16, { size: 8.5, color: dark ? "AFC9EC" : C.grey, align: "right" }); }
function title(s, kicker, heading, n, dark = false) { text(s, kicker.toUpperCase(), 0.68, 0.4, 6.0, 0.18, { size: 10, bold: true, color: dark ? "78DCD4" : C.teal }); text(s, heading, 0.68, 0.7, 12.0, 0.48, { size: 29, bold: true, color: dark ? C.white : C.navy }); footer(s, n, dark); }
function screen(s, file, x, y, w, h) { box(s, x - 0.04, y - 0.04, w + 0.08, h + 0.08, "D9E7FC"); s.addImage({ path: path.join(images, file), x, y, w, h }); }
function note(s, body) { s.addNotes(body); }
function pill(s, value, x, y, w, fill = C.blue) { box(s, x, y, w, 0.32, fill); text(s, value, x + 0.1, y + 0.05, w - 0.2, 0.15, { size: 10, bold: true, color: C.white, align: "center" }); }
function node(s, n, label, description, x, y, fill = C.blue) { s.addShape(pptx.ShapeType.ellipse, { x, y, w: 0.38, h: 0.38, fill: { color: fill }, line: { color: fill, transparency: 100 } }); text(s, String(n), x, y + 0.09, 0.38, 0.11, { size: 8.5, bold: true, color: C.white, align: "center" }); text(s, label, x + 0.56, y, 2.1, 0.18, { size: 13, bold: true }); text(s, description, x + 0.56, y + 0.25, 3.15, 0.28, { size: 10.5, color: C.grey, valign: "top" }); }

let s;
// 1. Opening
s = pptx.addSlide(); s.background = { color: C.navy };
s.addImage({ path: path.join(images, "2026_home_guest.png"), x: 7.1, y: 0, w: 6.23, h: 7.5, transparency: 21 });
s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 7.8, h: 7.5, fill: { color: C.navy, transparency: 1 }, line: { color: C.navy, transparency: 100 } });
pill(s, "CAPSTONE GROUP 7", 0.74, 0.76, 1.9, C.teal);
text(s, "InvestigateIQ", 0.74, 1.42, 5.6, 0.62, { size: 42, bold: true, color: C.white });
text(s, "Trace the evidence. Own the decision.", 0.77, 2.28, 5.4, 0.35, { size: 22, bold: true, color: "78DCD4" });
text(s, "A transparent, AI-assisted workflow for fictional AML case investigations.", 0.77, 2.92, 5.4, 0.62, { size: 18, color: "DDEBFF", valign: "top" });
text(s, "Soumya — presenter  |  Laxman — backup", 0.77, 5.82, 4.8, 0.2, { size: 13, bold: true, color: C.white });
text(s, "5:35 core slides  •  live demo and questions within the 15-minute session", 0.77, 6.25, 5.8, 0.2, { size: 12.5, color: "AFC9EC" });
footer(s, 1, true); note(s, "Soumya opens in 25 seconds. State that this is a fictional AML learning product. The deck uses 5 minutes 35 seconds, then the demo and questions share the remainder of the 15-minute session; FAQ slides are appendix material only when asked.");

// 2. Program and team
s = pptx.addSlide(); s.background = { color: C.pale }; title(s, "Program statement", "What this capstone will deliver—and what it will not", 2);
box(s, 0.72, 1.42, 11.9, 1.03, C.indigo); text(s, "Design and demonstrate a fictional AML review workflow where every report claim is traceable to supplied material, limitations stay visible, and workflow actions remain named human decisions.", 1.0, 1.7, 11.35, 0.46, { size: 18, bold: true, color: C.white, align: "center" });
[["Track", "Blueprint + Prototype + Detailed code + Final results"], ["Measures", "Traceability, visible gaps, clear states, and required rationale"], ["Non-goals", "No real data, autonomous decision, legal conclusion, or external filing"]].forEach((v, i) => { const x = 0.82 + i * 4.1; box(s, x, 2.86, 3.72, 1.05, i === 1 ? C.mint : C.white); text(s, v[0], x + 0.22, 3.08, 3.2, 0.18, { size: 13, bold: true, color: i === 1 ? C.teal : C.blue }); text(s, v[1], x + 0.22, 3.4, 3.2, 0.28, { size: 10.5, color: C.grey, valign: "top" }); });
text(s, "Team: Rahul Chainani · Pankaj Bharsakale · Lakshmi Dudgikar · Rahul Sharma · Laxman Singh · Soumya · Sweta Singh", 0.86, 4.66, 11.45, 0.22, { size: 13, bold: true, color: C.navy, align: "center" });
text(s, "Soumya presents the session; Laxman is the backup presenter.", 0.86, 5.13, 11.45, 0.2, { size: 12, italic: true, color: C.grey, align: "center" });
note(s, "Soumya uses 35 seconds. Read the statement, selected track, and non-goals. Introduce the team in the displayed order and say that Soumya presents while Laxman is the backup.");

// 3. Product flow
s = pptx.addSlide(); s.background = { color: C.pale }; title(s, "The product", "From a stored alert to an accountable human action", 3);
const flow = [["1", "Queue", "Find and filter the fictional alert"], ["2", "Workspace", "Build or replay the review"], ["3", "Evidence", "Read exact records and chunks"], ["4", "Decision", "Record a required rationale"], ["5", "Compliance", "Perform a second human review"]];
flow.forEach((v, i) => { const x = 0.56 + i * 2.56; box(s, x, 2.1, 2.18, 1.72, i === 2 ? C.mint : C.white); s.addShape(pptx.ShapeType.ellipse, { x: x + 0.18, y: 2.35, w: 0.44, h: 0.44, fill: { color: i === 2 ? C.teal : C.blue }, line: { color: C.white, transparency: 100 } }); text(s, v[0], x + 0.18, 2.46, 0.44, 0.1, { size: 8, bold: true, color: C.white, align: "center" }); text(s, v[1], x + 0.22, 3.0, 1.6, 0.22, { size: 16, bold: true }); text(s, v[2], x + 0.22, 3.39, 1.7, 0.32, { size: 10.6, color: C.grey, valign: "top" }); if (i < 4) s.addShape(pptx.ShapeType.line, { x: x + 2.2, y: 2.96, w: 0.27, h: 0, line: { color: C.teal, width: 2, endArrowType: "triangle" } }); });
text(s, "The application supports investigation. It never closes, escalates, refers, or files an action automatically.", 1.2, 5.35, 10.9, 0.3, { size: 17, bold: true, color: C.navy, align: "center" });
note(s, "Soumya uses 30 seconds. Move left to right through the flow. Emphasize human decision ownership and separate Compliance review.");

// 4. Responsible AI
s = pptx.addSlide(); s.background = { color: C.navy }; title(s, "Responsible AI", "Evidence confidence exposes support gaps—it does not predict wrongdoing", 4, true);
screen(s, "2026_workspace_confidence.png", 0.7, 1.4, 6.95, 3.91);
[["Coverage", "Supplied records and guidance that support the draft"], ["Limitations", "Known missing or unresolved evidence"], ["Boundary", "Not a crime, legality, or outcome probability"]].forEach((v, i) => { box(s, 8.08, 1.7 + i * 0.92, 4.1, 0.64, "173C78"); text(s, v[0], 8.3, 1.83 + i * 0.92, 1.02, 0.17, { size: 12, bold: true, color: "78DCD4" }); text(s, v[1], 9.42, 1.77 + i * 0.92, 2.5, 0.3, { size: 10.5, color: "DDEBFF", valign: "top" }); });
note(s, "Soumya uses 40 seconds. Define evidence confidence as deterministic support coverage. It is not a risk score, probability of crime, legality assessment, or recommended outcome.");

// 5. OKF / RAG
s = pptx.addSlide(); s.background = { color: C.pale }; title(s, "OKF, chunks, and RAG", "The coding logic keeps the source trail inspectable", 5);
screen(s, "2026_evidence_source_chunks_detail.png", 0.68, 1.38, 6.88, 3.87);
[["OKF source", "ID, scenario, title, criteria, body"], ["Chunk builder", "C0 metadata + two-sentence body chunks"], ["FTS5 + BM25", "Local keyword match and rank"], ["RAG context", "Retrieved IDs produce a cited, reviewable answer"]].forEach((v, i) => node(s, i + 1, v[0], v[1], 8.05, 1.45 + i * 0.84, i === 2 ? C.teal : C.blue));
box(s, 0.82, 5.75, 11.65, 0.42, C.mint); text(s, "OKF source  →  chunk builder  →  FTS5/BM25  →  retrieved IDs  →  cited response", 1.0, 5.88, 11.28, 0.13, { size: 11.5, bold: true, color: C.teal, align: "center" });
note(s, "Soumya uses 55 seconds. OKF is Open Knowledge Format: a source record with stable metadata and body text. Explain C0 metadata and two-sentence chunks, then local SQLite FTS5 keyword search and BM25 ranking. Say retrieval finds text; it does not prove truth.");

// 6. Data-flow architecture
s = pptx.addSlide(); s.background = { color: C.pale }; s.addImage({ path: path.join(images, "2026_data_flow_diagram_v2.svg"), x: 0.58, y: 0.24, w: 12.17, h: 6.85 }); footer(s, 6);
note(s, "Soumya uses 55 seconds. Point to the upper row first: a selected case loads stored fictional evidence, the specialist components build structured inputs, the Summary Agent optionally drafts, the validator checks selected claims, and a human records the action. Then point to the lower row: OKF guidance is chunked, FTS5/BM25 retrieves lexical matches, and exact cited chunks return to the report. Say clearly that retrieval is not proof, the validator reduces selected risks but cannot guarantee truth, and no action is automated.");

// 7. Live demo flow
s = pptx.addSlide(); s.background = { color: C.navy }; title(s, "Live demonstration flow", "Two cases: documented closure, then an open/escalated investigation", 7, true);
const demo = [["0:00–0:35", "Case A — documented closure", "From Queue, open Evidence only. Show why the closed outcome has recorded support; do not alter it."], ["0:35–1:15", "Case B — open/escalated", "Open the default review case; distinguish Status, Rule(s), and Action."], ["1:15–2:05", "Workspace", "Run saved/calculated review; show validator and evidence-confidence limitations."], ["2:05–2:55", "Evidence & RAG", "Open Source & chunks; explain FTS5/BM25 lexical retrieval—not vectors. Admin view is optional if already unlocked; never show the passcode."], ["2:55–3:40", "Ask InvestigateIQ", "Ask one bounded case question; show the response, citations, and limits."], ["3:40–4:50", "Human decision / audit", "Show Close, Request more information, and Escalate options plus required rationale; do not submit or close any case."]];
demo.forEach((v, i) => { const y = 1.43 + i * 0.78; box(s, 0.8, y, 11.72, 0.56, i === 2 ? "173C78" : "102B51"); text(s, v[0], 1.03, y + 0.18, 1.1, 0.16, { size: 11.5, bold: true, color: "78DCD4" }); text(s, v[1], 2.35, y + 0.18, 2.05, 0.16, { size: 12.5, bold: true, color: C.white }); text(s, v[2], 4.4, y + 0.13, 7.76, 0.26, { size: 10.6, color: "DDEBFF", valign: "top" }); });
note(s, "Soumya uses 45 seconds to explain the demo plan, then performs it. Start with a documented closed case to show evidence access, then use the open/escalated case for the investigation. Do not submit an investigator or Compliance action, create intake data, reset decisions, or reveal an Admin passcode. Speak only about what is under the pointer.");

// 8. ROI
s = pptx.addSlide(); s.background = { color: C.pale }; title(s, "Value realization and roadmap", "Measure the benefit before claiming ROI", 8);
[["Efficiency", "Verified minutes saved locating case records and source passages"], ["Rework", "Avoided evidence requests and Compliance returns"], ["Audit readiness", "Time to reconstruct evidence, rationale, and outcome"], ["Safety", "Unsupported claims, broken citations, unclear states found in review"]].forEach((v, i) => { const col = i % 2, row = Math.floor(i / 2), x = 0.82 + col * 6.02, y = 1.55 + row * 1.1; box(s, x, y, 5.47, 0.82, i === 3 ? C.mint : C.white); text(s, v[0], x + 0.22, y + 0.18, 1.3, 0.18, { size: 13, bold: true, color: i === 3 ? C.teal : C.blue }); text(s, v[1], x + 1.52, y + 0.14, 3.65, 0.3, { size: 10.5, color: C.grey, valign: "top" }); });
box(s, 0.82, 4.27, 11.48, 0.54, C.indigo); text(s, "ROI % = (verified annual benefit − implementation and run cost) ÷ implementation and run cost × 100", 1.04, 4.46, 11.05, 0.16, { size: 12.5, bold: true, color: C.white, align: "center" });
text(s, "Roadmap: test fixtures + citation evaluation  →  authentication + lineage versioning  →  governed ingestion + approved integrations", 0.92, 5.35, 11.38, 0.36, { size: 15, bold: true, color: C.navy, align: "center" });
text(s, "Planning model only: calculate ROI only after a baseline, approved cost boundary, and verified pilot outcomes.", 0.92, 5.87, 11.38, 0.18, { size: 11, italic: true, color: C.grey, align: "center" });
note(s, "Soumya uses 50 seconds. Say this is an ROI measurement framework, not an invented financial result. Name the four value levers and future sequence. A real ROI needs a baseline, approved costs, and verified pilot results.");

// 9. Thank you (show after live demo)
s = pptx.addSlide(); s.background = { color: C.navy }; title(s, "Thank you", "Trace the evidence. Own the decision.", 9, true);
screen(s, "2026_workspace_current_report.png", 7.05, 1.28, 5.6, 3.15);
[["Traceable evidence", "Records, chunks, citations, and visible gaps"], ["Responsible AI", "Confidence limitations, not automated judgement"], ["Human accountability", "Named rationale and separate Compliance review"]].forEach((v, i) => { text(s, v[0], 0.85, 1.72 + i * 0.95, 4.0, 0.21, { size: 16, bold: true, color: i === 1 ? "78DCD4" : C.white }); text(s, v[1], 0.85, 2.08 + i * 0.95, 4.85, 0.25, { size: 11.5, color: "DDEBFF" }); });
text(s, "Thank you. The FAQ appendix is available for any follow-up question.", 0.85, 5.55, 5.75, 0.35, { size: 17, bold: true, color: "78DCD4", valign: "top" });
note(s, "Show this slide after the live demo. Soumya closes in 15 seconds and uses the FAQ appendix only if a relevant question is asked. Questions, demo, and slides all fit within the 15-minute session; no separate Q&A allocation is assumed.");

// 10. FAQ appendix: data and relevance
s = pptx.addSlide(); s.background = { color: C.pale }; title(s, "FAQ appendix 1", "Where does the data come from, and how is it relevant?", 10);
[["What is the data source?", "All cases, customers, transactions, documents, and guidance are fictional course material stored locally for this demonstration. The product is not connected to a bank feed or real customer records."], ["How is retrieval relevant to a case?", "The active case/scenario scopes the available evidence. SQLite FTS5 performs lexical keyword matching and BM25 ranks matching passages. The user can open the exact record or chunk behind a result."], ["Does a citation prove a claim?", "No. It is a pointer to inspect supplied text. The product labels evidence gaps and requires a human to interpret the material and record the next action."]].forEach((v, i) => { const y = 1.48 + i * 1.34; box(s, 0.82, y, 11.65, 1.03, i === 1 ? C.mint : C.white); text(s, v[0], 1.08, y + 0.18, 3.35, 0.19, { size: 14, bold: true, color: i === 1 ? C.teal : C.blue }); text(s, v[1], 4.56, y + 0.16, 7.47, 0.47, { size: 11.2, color: C.grey, valign: "top" }); });
note(s, "Appendix only—do not present unless asked. Soumya can state: the data is fictional; retrieval is lexical FTS5/BM25 over scoped local text; citations are review pointers, not proof.");

// 11. FAQ appendix: AI and hallucination
s = pptx.addSlide(); s.background = { color: C.navy }; title(s, "FAQ appendix 2", "Where is AI used, and how do we reduce hallucination risk?", 11, true);
[["Where is AI used?", "Five specialist components collect/compute evidence. The Investigation Summary Agent is the only component that makes an optional Gemini model call; calculated mode makes no model call."], ["What guardrails exist?", "Prompt rules require cited source IDs, avoid verdict language, and treat source fields as untrusted. The validator checks selected citations, ratios, and unsupported conclusion wording."], ["Can the system guarantee truth?", "No. These checks reduce specific failure modes only. Evidence confidence exposes limitations, and a named human—not the AI—decides whether to close, request information, or escalate."]].forEach((v, i) => { const y = 1.47 + i * 1.34; box(s, 0.82, y, 11.65, 1.03, "173C78"); text(s, v[0], 1.08, y + 0.18, 3.35, 0.19, { size: 14, bold: true, color: "78DCD4" }); text(s, v[1], 4.56, y + 0.16, 7.47, 0.47, { size: 11.2, color: "DDEBFF", valign: "top" }); });
note(s, "Appendix only—do not present unless asked. Do not say the validator eliminates hallucination. Say it reduces specific risks and cannot guarantee factual truth.");

// 12. FAQ appendix: access, audit, and value
s = pptx.addSlide(); s.background = { color: C.pale }; title(s, "FAQ appendix 3", "How are access, audit, and value handled?", 12);
[["Is this role-based access control?", "No. The visible role selector is a demo display label. Admin pages use a limited passcode gate, which is not production authentication or authorization; the code is not shown in the deck or Blueprint."], ["What is in the audit trail?", "System, AI, and human workflow events are recorded with case context. A human decision requires a name and rationale and becomes a recorded state; a Compliance return creates a new auditable step."], ["How much money or time does it save?", "No percentage or financial claim is made from fictional data. A real pilot would measure verified lookup time, rework, audit reconstruction time, and safety issues against an approved cost baseline."]].forEach((v, i) => { const y = 1.48 + i * 1.34; box(s, 0.82, y, 11.65, 1.03, i === 2 ? C.mint : C.white); text(s, v[0], 1.08, y + 0.18, 3.35, 0.19, { size: 14, bold: true, color: i === 2 ? C.teal : C.blue }); text(s, v[1], 4.56, y + 0.16, 7.47, 0.47, { size: 11.2, color: C.grey, valign: "top" }); });
note(s, "Appendix only—do not present unless asked. State clearly that the Admin passcode is not disclosed, the demo is not RBAC, and ROI is a pilot measurement framework rather than a financial result.");

async function transitions(file) { const zip = await JSZip.loadAsync(fs.readFileSync(file)); for (const name of Object.keys(zip.files).filter(n => /^ppt\/slides\/slide\d+\.xml$/.test(n))) { let xml = await zip.file(name).async("string"); if (!xml.includes("<p:transition")) { const t = '<p:transition spd="med" advClick="1"><p:fade/></p:transition>'; xml = xml.includes("</p:clrMapOvr>") ? xml.replace("</p:clrMapOvr>", `</p:clrMapOvr>${t}`) : xml.replace("</p:sld>", `${t}</p:sld>`); zip.file(name, xml); } } fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" })); }
function run(value, o = {}) { return new TextRun({ text: value, font: "Arial", size: o.size || 20, bold: !!o.bold, color: o.color || C.ink }); }
function para(value, o = {}) { return new Paragraph({ children: [run(value, o)], heading: o.heading, spacing: { before: o.before || 0, after: o.after || 120, line: 270 } }); }
function cell(value, width, shade) { return new TableCell({ width: { size: width, type: WidthType.DXA }, shading: shade ? { type: "clear", color: shade, fill: shade } : undefined, margins: { top: 80, bottom: 80, left: 100, right: 100 }, children: [para(value, { size: 17, bold: shade === C.navy, color: shade === C.navy ? C.white : C.ink, after: 0 })] }); }
function table(headers, rows, widths) { return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: widths, rows: [new TableRow({ children: headers.map((v, i) => cell(v, widths[i], C.navy)) }), ...rows.map(row => new TableRow({ children: row.map((v, i) => cell(v, widths[i])) }))] }); }
async function guide() {
  const slideRows = [
    ["1", "Opening", "0:25", "State the fictional-product boundary and the 15-minute flexible format."], ["2", "Program statement", "0:35", "State the selected track, success measures, non-goals, and presenter/backup."], ["3", "Product flow", "0:30", "Show the alert-to-human-action path."], ["4", "Responsible AI", "0:40", "Define evidence confidence and its boundary."], ["5", "OKF, chunks, RAG", "0:55", "Explain lexical retrieval and source traceability."], ["6", "Architecture, AI, guardrails", "0:55", "Explain the specialist workflow, optional model draft, validator, and human audit boundary."], ["7", "Live demo plan", "0:45", "Explain the two-case, read-only demonstration guardrails."], ["8", "ROI and roadmap", "0:50", "Present the measurable planning framework and roadmap."], ["9", "Thank you", "0:15", "Show after the demo; open the FAQ appendix only if asked."], ["10–12", "FAQ appendix", "On demand", "Data/relevance; AI/hallucination; access/audit/value."],
  ];
  const demoRows = [["0:00–0:35", "Case A — documented closure", "Open Evidence only; show documented support without changing the closed case."], ["0:35–1:15", "Case B — open/escalated", "Open the default case; distinguish Status, Rule(s), and Action."], ["1:15–2:05", "Workspace", "Run saved/calculated review; show validator and confidence limitations."], ["2:05–2:55", "Evidence & RAG", "Open source/chunks; explain lexical FTS5/BM25 retrieval, not vectors. Admin view only if already unlocked; never show the code."], ["2:55–3:40", "Ask InvestigateIQ", "Ask one bounded question; point to citations and limits."], ["3:40–4:50", "Human decision / audit", "Show the three choices and rationale requirement; do not submit, close, or reset any case."]];
  const foundationQuestions = [
    ["Why did you choose AML investigations?", "The use case makes the need for traceability, evidence gaps, controlled assistance, and accountable human actions easy to demonstrate. This is a fictional learning prototype, not a bank AML system."],
    ["What problem does InvestigateIQ solve?", "An alert by itself does not explain the supporting material, missing evidence, or accountable next step. InvestigateIQ connects the alert, cited material, limitations, and a human rationale in one review path."],
    ["Who are the intended users?", "The demo models Investigators, Team Leads, Compliance Officers, and Admin reviewers. The visible role selector is a workflow/display label, not production identity or permissions."],
    ["What is outside the scope?", "No real customer data, external bank feed, legal conclusion, autonomous closure/escalation/referral, or regulator filing. We state these boundaries rather than implying a production control."],
    ["Why use a prototype instead of slides only?", "The working prototype lets us demonstrate the evidence trail, retrieval, limitation signal, and human audit state. The deck is a concise explanation and fallback."],
  ];
  const workflowQuestions = [
    ["How does one case move through the system?", "A user selects an alert, opens the workspace, inspects records and retrieved chunks, asks a bounded question if needed, and then a named human records a rationale. Compliance is a separate human review step."],
    ["Does the alert mean the customer did something wrong?", "No. The alert is a review signal. The product deliberately avoids treating a rule match, a report, or a citation as proof of wrongdoing."],
    ["Why are completed cases still visible?", "A completed case remains available for evidence and audit review. It should not invite a presenter to overwrite a recorded state during the demo."],
    ["What distinguishes Close, Request more information, and Escalate?", "They are human workflow choices. Close records a reviewed outcome, Request more information identifies an evidence gap, and Escalate routes the case for further review. Each needs a rationale and is auditable."],
    ["What does Compliance add?", "Compliance provides a separate human review: acknowledge, return for more information, or record an onward referral. The tool records the action; it does not file externally."],
  ];
  const ragQuestions = [
    ["What is OKF?", "In this prototype, OKF means Open Knowledge Format: a readable synthetic source record with stable metadata, criteria, version information, and body text."],
    ["Why split documents into chunks?", "Chunking creates smaller inspectable passages. A C0 metadata chunk preserves context, while body chunks let a reviewer see the exact passage used in retrieval."],
    ["How does retrieval work?", "SQLite FTS5 performs local lexical keyword matching and BM25 orders the matching passages. The active case/scenario scope is kept with the query."],
    ["Do you use vector embeddings or semantic search?", "No. This implementation uses transparent lexical FTS5/BM25 retrieval, not a vector index. That choice is easier to inspect and reproduce for the course demonstration."],
    ["How do you know retrieved text is relevant or true?", "BM25 ranks textual matches; it does not prove truth, legal relevance, or correctness. The reviewer can open the source/chunk, see limitations, and make the decision."],
    ["What stops a citation from being fabricated?", "The validator checks known source/chunk IDs and the report is expected to cite retrieved context. This reduces selected citation failures but is not a guarantee that every statement is true."],
  ];
  const aiQuestions = [
    ["Where exactly is AI used?", "Five specialist components gather or calculate evidence inputs. The Investigation Summary Agent is the only component that may make an optional Gemini model call to draft a structured report. Calculated mode makes no model call."],
    ["Are these autonomous agents?", "No. They are bounded investigation-specialist components in a defined workflow. They do not set goals, access external systems, or take workflow actions on their own."],
    ["Do you have CEO or CFO agents?", "No. The implemented components are Alert Triage, Customer/KYC, Transaction Investigation, Relationship, Evidence, and the Investigation Summary Agent. We do not claim CEO/CFO persona agents."],
    ["Which model do you use?", "The optional drafting path is configured for Gemini. The product can also run in calculated mode without a model call; we do not claim a benchmark comparison between models."],
    ["How do you reduce hallucination?", "We retrieve supplied material first, keep source IDs, require inspectable citations, use grounded prompt rules, treat source fields as untrusted, and run the Grounding Validator. These measures reduce selected failure modes; they do not eliminate hallucination or guarantee truth."],
    ["What does the Grounding Validator check?", "It checks known IDs, selected ratio claims, forbidden verdict language, and obvious prompt-like text. It can downgrade unsupported verified wording or remove unsafe output elements before the human sees the draft."],
    ["How do you handle prompt injection in retrieved material?", "Source fields are treated as untrusted. The guardrail layer screens obvious prompt-like content and the model is not given authority to execute actions. This is a protective control, not a claim of perfect injection resistance."],
    ["What is evidence confidence?", "It is a deterministic support-and-limitations signal calculated after a report is available. It is not a fraud score, probability of crime, legality assessment, or recommended outcome."],
    ["How did you validate the AI output?", "The prototype validates selected structural properties—known citations, selected numerical wording, unsafe verdict language, and visible limitations. A production evaluation would additionally need a labelled test set, citation-quality metrics, failure analysis, and human review."],
    ["What happens if the model is unavailable or produces a poor draft?", "Calculated mode still produces a deterministic review from the fictional rows. A draft remains advisory, validation notes and limitations stay visible, and a human can decline to act on it."],
    ["How do you address bias or fairness?", "This fictional prototype does not claim bias testing or fairness certification. It avoids a score about a person, keeps evidence and limitations visible, and requires human accountability. A real deployment would require governance, data-quality review, and formal model-risk assessment."],
    ["Is the system explainable?", "It is designed for traceability, not a claim of full model interpretability. The user can inspect case rows, source chunks, retrieval method, citations, validator notes, confidence limitations, and the human rationale."],
    ["Does the AI make the final decision?", "No. Only a named person with a written rationale can create an investigator or Compliance action. The Copilot cannot submit a decision, close a case, escalate, or file anything."],
    ["What is the difference between RAG and the model?", "RAG is the retrieval step: it selects supplied source passages before an answer is drafted. The optional model turns bounded inputs into a structured summary. Retrieval provides context; it does not make the model's output automatically true."],
    ["Why use RAG instead of fine-tuning a model?", "The course prototype needs source-level traceability and inspectable updates. Retrieval allows a reviewer to see the current supplied passage. We do not claim that fine-tuning was performed or that it would remove the need for validation."],
    ["Are prompts or model settings the main safety control?", "No. Prompts are only one layer. The stronger prototype controls are bounded inputs, cited retrieval, deterministic specialist calculations, validation checks, visible limitations, and a mandatory human action. We do not claim to have optimized temperature or model parameters."],
    ["How do you test for hallucination?", "We do not claim a complete hallucination benchmark. We test selected structural failure modes such as unknown citations, prohibited verdict language, prompt-like retrieved text, and selected unsupported claims. A production test would require representative evaluation cases and human scoring."],
    ["How do you measure model accuracy?", "This prototype does not report model-accuracy percentages because it has no labelled, representative benchmark set. The displayed confidence is evidence support/limitations, not model accuracy. Future evaluation would separate factuality, citation precision, coverage, and reviewer agreement."],
    ["What data does the model see?", "Only the bounded fictional case inputs and retrieved context used for the selected prototype path. We make no claim about production data handling. A real deployment would require data minimisation, an approved processing agreement, retention controls, and access review."],
    ["Can the model leak data between cases?", "The intended design scopes retrieval to the active case/scenario and identifies the cited source. This demo has only fictional data. Cross-case isolation, tenancy, logging, and security testing would be mandatory production controls, not claims we make here."],
    ["What happens when retrieval finds no useful source?", "The correct response is to show an evidence gap or limitation, not invent an answer. The reviewer can request more information or escalate according to the workflow; the model cannot turn missing evidence into proof."],
    ["Why call this an agent?", "The term is used narrowly for a bounded component with a specialist purpose in a defined workflow. It is not a free-running autonomous agent: it has no independent authority, external execution, or final-decision power."],
    ["How would you monitor this in production?", "We would monitor retrieval quality, citation validity, validator flags, human overrides, latency, failures, drift in input patterns, and access events. Thresholds, ownership, review cadence, and incident response would need formal governance."],
    ["Can this system be scaled?", "The prototype demonstrates the logic, not a scalability benchmark. SQLite FTS5/BM25 is appropriate for the small local demonstration. Production scale would need measured load testing, a governed data platform, access controls, observability, and capacity design."],
    ["What responsible-AI principle is most visible here?", "Human oversight and contestability: users can inspect the evidence trail, see what is missing, challenge the draft, and record their own rationale. Confidence is presented as a limitation-aware signal rather than an automated decision."],
  ];
  const demoAndValueQuestions = [
    ["Why is the live demo read-only?", "A completed action is persistent in the demo store, so we protect the demonstration state. We show the available controls and audit trail without changing a case."],
    ["Why show a closed case and an open/escalated case?", "The closed case demonstrates evidence and audit access; the active case demonstrates investigation, retrieval, Copilot, confidence, and the human-decision boundary."],
    ["Why does the Admin area use a passcode?", "It is a limited teaching-demo gate for source/rule inspection, not production authentication or authorization. We never disclose the passcode in the deck, guide, or live session."],
    ["Is personal or sensitive data being sent to an AI model?", "No real customer information is used in this course prototype. All displayed data is fictional. A real deployment would need approved privacy, retention, access-control, and model-governance controls before any integration."],
    ["How would you measure business value?", "We do not claim savings from fictional data. A pilot would measure verified lookup time, avoided rework, audit-reconstruction time, and safety issues against an approved cost baseline before calculating ROI."],
    ["What are the next steps before real deployment?", "Authentication and authorization, governed ingestion, evidence-lineage versioning, test fixtures, retrieval/model evaluation, monitoring, privacy review, model-risk assessment, and clear operational ownership."],
    ["What should we say if a professor asks something we did not implement?", "Answer directly: ‘That is not implemented in this fictional prototype. We would treat it as a governed next-step requirement rather than claim it already works.’ Then connect it to the roadmap if relevant."],
  ];
  const doc = new Document({ creator: "Capstone Group 7", title: "InvestigateIQ Compact Presenter Guide", sections: [{ properties: { page: { margin: { top: 720, bottom: 720, left: 720, right: 720 } } }, children: [
    para("InvestigateIQ Compact Presenter Guide", { heading: HeadingLevel.TITLE, size: 36, bold: true, color: C.navy, after: 180 }),
    para("15-minute evaluation session: 5:35 core deck + approximately 5-minute live demo + questions handled within the same session", { size: 22, color: C.grey, after: 300 }),
    para("Presentation rule", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy }),
    para("Soumya is the presenter and Laxman is the backup. Only one person presents at a time. Questions, demo, and slides share the same 15-minute window; do not promise a separate Q&A block. Call every case, record, source, and chart fictional.", { size: 20 }),
    para("Slide plan", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy, before: 200 }),
    table(["#", "Slide", "Time", "Presenter says / does"], slideRows, [520, 2100, 950, 5790]),
    para("Live demo flow — approximately 5 minutes", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy, before: 240 }),
    para("Use two fictional cases: first a documented closed case to show evidence access; then the default open/escalated case for the review. Navigate, filter, open tabs, expand accordions, and ask one prepared bounded question. Do not submit an investigator decision, Compliance action, or fictional intake record; do not reset or close a case; do not reveal or enter an Admin passcode.", { size: 20 }),
    table(["Time", "Screen", "Action and narration"], demoRows, [1450, 1850, 6060]),
    para("FAQ appendix and question preparation", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy, before: 240 }),
    para("Use FAQ slides 10–12 only if asked. Soumya answers live questions; Laxman can present only if Soumya is unavailable. Technical preparation contacts: Rahul Chainani—application/deployment; Pankaj Bharsakale—AI/RAG; Lakshmi Dudgikar—requirements and case mapping; Rahul Sharma—testing and edge cases; Sweta Singh—program scope and ROI. Never claim real-data performance, a verified financial ROI, legal conclusions, role-based production security, or autonomous workflow decisions.", { size: 20 }),
    para("Demo narration cues", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy, before: 240 }),
    para("Case Queue: ‘Status shows workflow position; Action opens context.’  Workspace: ‘This report is advisory; the validator and confidence card expose its limits.’  Evidence & RAG: ‘This citation points to stored text; it is not proof.’  Copilot: ‘It summarizes available fictional material but cannot submit an action.’  Decision: ‘Only a named person with a rationale can create an audit event.’", { size: 20 }),
    para("Exact live-demo dialogue", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy, before: 240 }),
    para("Opening (0:00): ‘I will use two fictional cases. First, I will open a completed case only to show its recorded evidence. Then I will review an open or escalated case. I will not submit, close, reset, or alter any case during this demonstration.’", { size: 19 }),
    para("Case A — completed case (0:00–0:35): ‘In the Case Queue, this status means the workflow already has a recorded outcome. Instead of asking us to reopen it, the Evidence action lets us inspect the support behind that outcome. These links are evidence pointers; they are not a claim that the system has proved anything independently.’", { size: 19 }),
    para("Case B — active case (0:35–1:15): ‘For the active case, Status tells us where the workflow is, Rule(s) explains the monitoring signal, and Action opens the review context. The alert is a starting point for review, not a finding of wrongdoing.’", { size: 19 }),
    para("Workspace (1:15–2:05): ‘This report is advisory. The specialist components read the selected fictional case evidence; in calculated mode no model is called. If optional AI drafting is enabled, the Investigation Summary Agent drafts the report, then the Grounding Validator checks selected citations, ratios, wording, and prompt-like text. The evidence-confidence card shows support and limitations; it is not a risk score or a legal conclusion.’", { size: 19 }),
    para("Evidence & RAG (2:05–2:55): ‘Here is the source trail. An OKF knowledge source is stored with metadata and then split into C0 metadata and reviewable body chunks. SQLite FTS5 finds lexical keyword matches and BM25 ranks them. I can open the exact cited chunk, so the reviewer can inspect the text behind the report. Retrieval finds supplied text; it does not prove that text is true.’", { size: 19 }),
    para("Ask InvestigateIQ (2:55–3:40): ‘I will ask one bounded question about this selected case. The response uses available fictional material and returns citations for review. The Copilot cannot submit an investigator decision, Compliance action, or regulatory filing.’", { size: 19 }),
    para("Human decision and audit (3:40–4:50): ‘The final choice belongs to a named human. Close, Request more information, and Escalate require a written rationale and create an audit event. A Compliance Officer can then acknowledge, return, or record an onward referral. The system records the review path; it does not make the decision for the reviewer.’", { size: 19 }),
    para("Transition to questions: ‘This is how InvestigateIQ keeps the evidence trail, uncertainty, and human accountability visible from an alert to the next documented step.’", { size: 19, bold: true, color: C.teal }),
    para("Professor question bank", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy, before: 280 }),
    para("This is a preparation aid, not a script to read aloud. Use the concise answer first, then show the relevant screen, cited chunk, or diagram if a follow-up is needed. Keep every answer inside the factual prototype boundary.", { size: 20 }),
    para("Slides 1–2 — problem, scope, and project choices", { heading: HeadingLevel.HEADING_2, size: 24, bold: true, color: C.teal, before: 200 }),
    table(["Likely question", "Suggested answer"], foundationQuestions, [2850, 6510]),
    para("Slide 3 and workflow screens — case lifecycle and accountability", { heading: HeadingLevel.HEADING_2, size: 24, bold: true, color: C.teal, before: 220 }),
    table(["Likely question", "Suggested answer"], workflowQuestions, [2850, 6510]),
    para("Slide 5 and Evidence & RAG — OKF, chunks, retrieval, and citations", { heading: HeadingLevel.HEADING_2, size: 24, bold: true, color: C.teal, before: 220 }),
    table(["Likely question", "Suggested answer"], ragQuestions, [2850, 6510]),
    para("Slides 4 and 6 — AI, confidence, validation, and responsible use", { heading: HeadingLevel.HEADING_2, size: 24, bold: true, color: C.teal, before: 220 }),
    table(["Likely question", "Suggested answer"], aiQuestions, [2850, 6510]),
    para("Live demo, outcomes, and future-readiness questions", { heading: HeadingLevel.HEADING_2, size: 24, bold: true, color: C.teal, before: 220 }),
    table(["Likely question", "Suggested answer"], demoAndValueQuestions, [2850, 6510]),
    para("How to answer safely", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy, before: 260 }),
    para("1. State what this prototype actually does, and distinguish it from a production banking system.  2. Point to an inspectable artifact: a cited chunk, the data-flow diagram, a validation message, or an audit record.  3. Name the limitation before claiming the benefit: fictional data, lexical retrieval, optional model drafting, and no autonomous action.  4. If a requested capability is not implemented, say so plainly: ‘That is a planned production control, not a claim of this prototype.’", { size: 20 }),
  ] }] });
  fs.writeFileSync(guideFile, await Packer.toBuffer(doc));
}

(async () => { fs.mkdirSync(out, { recursive: true }); await pptx.writeFile({ fileName: deckFile }); await transitions(deckFile); await guide(); console.log(deckFile); console.log(guideFile); })().catch(err => { console.error(err); process.exit(1); });
