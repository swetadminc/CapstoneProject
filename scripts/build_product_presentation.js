/* Create the InvestigateIQ presentation deck and its companion presenter guide.
   The deck embeds the fresh current-product images and applies a subtle fade
   transition to every slide. */
const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");
const JSZip = require("jszip");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, AlignmentType } = require("docx");

const root = path.resolve(__dirname, "..");
const screenDir = path.join(root, "assets", "walkthrough_screens");
const outDir = path.join(root, "Product Docs");
const deckFile = path.join(outDir, "InvestigateIQ_Product_Presentation.pptx");
const guideFile = path.join(outDir, "InvestigateIQ_Deck_Presenter_Guide.docx");
const W = 13.333, H = 7.5;
const C = { navy: "0B1F3A", indigo: "173C78", blue: "2E65C5", teal: "00A79D", ice: "EAF2FF", mist: "F6F9FE", white: "FFFFFF", ink: "12233F", grey: "63738D", green: "16803C", gold: "B97800", red: "B4232C" };
const imagePath = n => path.join(screenDir, n);
const team = [
  ["Rahul Chainani", "Application development and integration"], ["Pankaj Bharsakale", "AI workflow and evidence review"],
  ["Lakshmi Dudgikar", "Requirements and case-study mapping"], ["Rahul Sharma", "Quality assurance and edge cases"],
  ["Laxman Singh", "User experience and product walkthrough"], ["Soumya", "Team coordination and presentation"],
  ["Sweta Singh", "Course linkage and project explanation"],
];

function addText(slide, value, x, y, w, h, opts = {}) {
  slide.addText(value, { x, y, w, h, fontFace: opts.fontFace || "Arial", fontSize: opts.fontSize || 18,
    color: opts.color || C.ink, bold: !!opts.bold, italic: !!opts.italic, margin: 0,
    breakLine: false, fit: "shrink", valign: opts.valign || "mid", align: opts.align || "left",
    isTextBox: true, paraSpaceAfterPt: opts.paraSpaceAfterPt || 0, bullet: opts.bullet, transparency: opts.transparency });
}
function bg(slide, color = C.mist) { slide.background = { color }; }
function addFooter(slide, number, dark = false) {
  addText(slide, `InvestigateIQ  |  Capstone Group 7  |  ${number}`, 0.55, 7.12, 5.0, 0.18, { fontSize: 8.5, color: dark ? "AFC9EC" : C.grey });
  addText(slide, "Fictional AML investigation learning environment", 8.0, 7.12, 4.75, 0.18, { fontSize: 8.5, color: dark ? "AFC9EC" : C.grey, align: "right" });
}
function rounded(slide, x, y, w, h, fill, radius = 0.16, line = fill) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h, rectRadius: radius, fill: { color: fill }, line: { color: line, transparency: 100 } });
}
function header(slide, kicker, title, number, dark = false) {
  addText(slide, kicker.toUpperCase(), 0.68, 0.42, 5.0, 0.23, { fontSize: 10, bold: true, color: dark ? "78DCD4" : C.teal });
  addText(slide, title, 0.68, 0.72, 11.9, 0.54, { fontSize: 31, bold: true, color: dark ? C.white : C.navy });
  addFooter(slide, number, dark);
}
function screen(slide, filename, x, y, w, h) {
  rounded(slide, x - 0.05, y - 0.05, w + 0.1, h + 0.1, "D9E7FC");
  slide.addImage({ path: imagePath(filename), x, y, w, h });
}
function note(slide, content) { slide.addNotes(content); }
function pill(slide, value, x, y, w, color = C.blue) {
  rounded(slide, x, y, w, 0.34, color);
  addText(slide, value, x + 0.12, y + 0.04, w - 0.24, 0.22, { fontSize: 10, bold: true, color: C.white, align: "center" });
}
function node(slide, label, x, y, color) {
  slide.addShape(pptx.ShapeType.ellipse, { x, y, w: 0.48, h: 0.48, fill: { color }, line: { color, transparency: 100 } });
  addText(slide, label, x + 0.75, y + 0.02, 2.0, 0.36, { fontSize: 15, bold: true, color: C.ink });
}
function arrow(slide, x1, y1, x2, y2, color = C.teal) { slide.addShape(pptx.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color, width: 2, beginArrowType: "none", endArrowType: "triangle" } }); }

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Capstone Group 7";
pptx.company = "IIT Bombay";
pptx.subject = "InvestigateIQ product presentation";
pptx.title = "InvestigateIQ: Product Blueprint and Demonstration";
pptx.lang = "en-IN";
pptx.theme = { headFontFace: "Arial", bodyFontFace: "Arial", lang: "en-IN" };

let s;
// 1. Cover
s = pptx.addSlide(); bg(s, C.navy);
s.addImage({ path: imagePath("2026_home_guest.png"), x: 6.35, y: 0, w: 6.983, h: 7.5, transparency: 19 });
s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 7.5, h: 7.5, fill: { color: C.navy, transparency: 3 }, line: { color: C.navy, transparency: 100 } });
pill(s, "CAPSTONE GROUP 7", 0.72, 0.75, 1.9, C.teal);
addText(s, "InvestigateIQ", 0.72, 1.42, 5.2, 0.65, { fontSize: 42, bold: true, color: C.white });
addText(s, "AI-assisted AML case investigation copilot", 0.75, 2.2, 5.05, 0.45, { fontSize: 20, color: "C8D9F3" });
addText(s, "Trace the evidence. Own the decision.", 0.75, 3.18, 4.8, 0.42, { fontSize: 22, bold: true, color: "78DCD4" });
addText(s, "A fictional, transparent evidence-to-decision workflow for a human investigator and Compliance reviewer.", 0.75, 3.8, 5.15, 0.74, { fontSize: 17, color: "D7E5F9", valign: "top" });
addText(s, "Leadership with AI · IIT Bombay", 0.75, 6.34, 3.7, 0.22, { fontSize: 12, color: "AFC9EC" });
note(s, "Opening: introduce InvestigateIQ as a fictional AML investigation copilot. Explain that the deck shows the complete product and its human-accountability boundary.");

// 2. Team
s = pptx.addSlide(); bg(s, C.mist); header(s, "The project team", "Who built and explains the product", 2);
addText(s, "Presentation lead: Pankaj Bharsakale · Technical preparation: Rahul Chainani", 0.7, 1.44, 7.2, 0.25, { fontSize: 15, color: C.grey });
team.forEach((member, i) => {
  const col = i % 2, row = Math.floor(i / 2); const x = 0.72 + col * 6.05, y = 1.95 + row * 1.16;
  rounded(s, x, y, 5.55, 0.9, col === 0 ? "EAF2FF" : "EAF9F7");
  s.addShape(pptx.ShapeType.ellipse, { x: x + 0.2, y: y + 0.2, w: 0.48, h: 0.48, fill: { color: col === 0 ? C.blue : C.teal }, line: { color: "FFFFFF", transparency: 100 } });
  addText(s, member[0], x + 0.85, y + 0.15, 3.95, 0.23, { fontSize: 15, bold: true });
  addText(s, member[1], x + 0.85, y + 0.45, 4.35, 0.25, { fontSize: 11.5, color: C.grey });
});
addText(s, "Contact details are intentionally excluded. Responsibilities describe planning and demonstration ownership, not system permissions.", 0.72, 6.67, 11.8, 0.23, { fontSize: 11, italic: true, color: C.grey });
note(s, "Pankaj introduces the group. State that Pankaj is the single presentation lead and Rahul Chainani supports technical preparation. Acknowledge the roster in the displayed order without reading every responsibility.");

// 3. Program statement
s = pptx.addSlide(); bg(s, C.navy); header(s, "Program statement", "A transparent evidence-to-decision capstone", 3, true);
rounded(s, 0.72, 1.48, 11.9, 1.08, "173C78");
addText(s, "Design and demonstrate a fictional AML investigation workflow where every report claim can be traced to supplied material, every limitation is visible, and every workflow action remains a named human decision.", 1.0, 1.75, 11.35, 0.55, { fontSize: 19, bold: true, color: C.white, align: "center", valign: "mid" });
[["Problem", "An alert alone lacks proof, context, and an accountable next step."], ["Program outcome", "Traceable evidence, bounded assistance, auditable human review."], ["Success measures", "Source traceability, visible gaps, clear workflow states, required rationale."], ["Non-goals", "No real data, autonomous decision, legal conclusion, or external filing."]].forEach((v, i) => { const col = i % 2, row = Math.floor(i / 2), x = 0.78 + col * 6.0, y = 3.05 + row * 1.35; rounded(s, x, y, 5.66, 0.98, row === 1 ? "173C78" : "102B51"); addText(s, v[0], x + 0.24, y + 0.18, 1.55, 0.19, { fontSize: 13, bold: true, color: "78DCD4" }); addText(s, v[1], x + 0.24, y + 0.48, 5.1, 0.26, { fontSize: 11.4, color: "DDEBFF", valign: "top" }); });
note(s, "Pankaj presents the program statement. Read the central statement slowly. The success measures are traceability, visible limits, clear states, and a human rationale. The program does not make a legal conclusion or automate a workflow action.");

// 4. Problem
s = pptx.addSlide(); bg(s, C.navy); header(s, "The problem", "An alert alone does not make a case", 4, true);
addText(s, "Investigators need to connect a monitoring signal with the source records, the missing evidence, the draft explanation, and the accountable next action.", 0.7, 1.55, 5.15, 1.12, { fontSize: 22, color: "DDEBFF", valign: "top" });
node(s, "Alert metadata", 0.92, 3.05, "447FE1"); node(s, "Source records", 0.92, 3.95, "00A79D"); node(s, "Human rationale", 0.92, 4.85, "C68600");
screen(s, "2026_case_queue_table.png", 6.05, 1.43, 6.56, 3.69);
addText(s, "InvestigateIQ keeps the queue, evidence, report, and human action connected on one product path.", 6.05, 5.45, 6.2, 0.5, { fontSize: 16, color: "C8D9F3" });
note(s, "Sweta explains the problem: source alerts help prioritize review but do not prove wrongdoing. Point out the queue fields and the difference between status, severity, rule label, and action.");

// 5. Workflow
s = pptx.addSlide(); bg(s, C.mist); header(s, "Product workflow", "One case follows a visible evidence trail", 5);
const flow = [["1", "Case Queue", "Find the fictional alert"], ["2", "Workspace", "Build or replay the review"], ["3", "Evidence & RAG", "Read exact source material"], ["4", "Human action", "Record a rationale"], ["5", "Compliance", "Perform separate review"]];
flow.forEach((item, i) => { const x = 0.55 + i * 2.55; rounded(s, x, 2.45, 2.15, 2.05, i === 2 ? "E6F8F6" : "FFFFFF"); s.addShape(pptx.ShapeType.ellipse, { x: x + 0.18, y: 2.68, w: 0.48, h: 0.48, fill: { color: i === 2 ? C.teal : C.blue }, line: { color: "FFFFFF", transparency: 100 } }); addText(s, item[0], x + 0.18, 2.77, 0.48, 0.16, { fontSize: 10, bold: true, color: C.white, align: "center" }); addText(s, item[1], x + 0.18, 3.38, 1.75, 0.28, { fontSize: 16, bold: true }); addText(s, item[2], x + 0.18, 3.82, 1.7, 0.4, { fontSize: 11.5, color: C.grey, valign: "top" }); if (i < 4) arrow(s, x + 2.18, 3.47, x + 2.46, 3.47, C.teal); });
addText(s, "The application supports investigation. It never submits, closes, escalates, or files an action automatically.", 1.35, 5.52, 10.65, 0.34, { fontSize: 18, bold: true, color: C.navy, align: "center" });
note(s, "Sweta walks the audience through the five steps. Use the fade transition and reveal each step in order. Emphasize that every workflow action belongs to a named human.");

// 6. Navigation
s = pptx.addSlide(); bg(s, C.mist); header(s, "Product navigation", "The left navigation matches the investigation sequence", 6);
screen(s, "2026_evidence_case_records.png", 0.67, 1.45, 7.1, 3.99);
addText(s, "Core workspaces", 8.25, 1.7, 3.4, 0.25, { fontSize: 18, bold: true });
[["Home", "Workspace entry and product overview"], ["Case Queue", "Find and filter fictional alerts"], ["Investigation Workspace", "Read evidence and record an action"], ["Evidence & RAG", "Inspect sources, chunks, and search"], ["Compliance / Analytics / Search", "Second review, descriptive charts, context lookup"]].forEach((v, i) => { node(s, v[0], 8.3, 2.2 + i * 0.7, i === 3 ? C.teal : C.blue); addText(s, v[1], 9.05, 2.57 + i * 0.7, 3.1, 0.18, { fontSize: 10.5, color: C.grey }); });
note(s, "Laxman explains the simplified left navigation. Show that the sequence follows user work: first find a case, then inspect it, then trace evidence, then complete a human review.");

// 7. Queue
s = pptx.addSlide(); bg(s, C.navy); header(s, "Case Queue", "Stored alerts become a reviewable workload", 7, true);
screen(s, "2026_case_queue_table.png", 0.67, 1.45, 7.3, 4.1);
addText(s, "What the queue separates", 8.42, 1.65, 3.65, 0.3, { fontSize: 19, bold: true, color: C.white });
[["Severity", "Priority label from the fictional source"], ["Status", "Current workflow state"], ["Rule(s)", "Stored trigger metadata"], ["Action", "Open a current case or inspect evidence"]].forEach((v, i) => { rounded(s, 8.42, 2.22 + i * 0.74, 3.92, 0.54, "173C78"); addText(s, v[0], 8.63, 2.34 + i * 0.74, 0.9, 0.17, { fontSize: 12.5, bold: true, color: "78DCD4" }); addText(s, v[1], 9.55, 2.31 + i * 0.74, 2.55, 0.22, { fontSize: 10.6, color: "DDEBFF" }); });
note(s, "Lakshmi explains queue filtering. Use a single case as the continuing example. Mention that a source-closed label differs from a recorded human closure, and evidence remains viewable after completion.");

// 8. Workspace
s = pptx.addSlide(); bg(s, C.mist); header(s, "Investigation Workspace", "The report stays connected to its evidence and limits", 8);
screen(s, "2026_workspace_current_report.png", 0.67, 1.42, 7.32, 4.12);
addText(s, "Report controls", 8.4, 1.62, 3.5, 0.25, { fontSize: 18, bold: true });
[["Saved report", "Repeatable historical snapshot"], ["Calculated mode", "Current stored fictional rows"], ["Validator", "Records notes before a decision"]].forEach((v, i) => { node(s, v[0], 8.44, 2.23 + i * 0.86, i === 2 ? C.gold : C.blue); addText(s, v[1], 9.18, 2.6 + i * 0.86, 2.9, 0.18, { fontSize: 11, color: C.grey }); });
note(s, "Pankaj explains the workspace. Show saved versus calculated mode and explain that the investigation runs or replays a review; it does not record a decision.");

// 9. Confidence
s = pptx.addSlide(); bg(s, C.navy); header(s, "Responsible AI", "Evidence confidence makes support gaps visible", 9, true);
screen(s, "2026_workspace_confidence.png", 0.67, 1.4, 7.35, 4.14);
addText(s, "45 / 100", 8.45, 1.77, 3.4, 0.62, { fontSize: 38, bold: true, color: "78DCD4" });
addText(s, "Example support score shown in the product", 8.47, 2.43, 3.65, 0.28, { fontSize: 12, color: "C8D9F3" });
[["Coverage", "How well the supplied records and guidance support the draft"], ["Limitations", "Known missing or unresolved evidence"], ["Boundary", "Never a probability of crime or a recommended outcome"]].forEach((v, i) => { rounded(s, 8.45, 3.0 + i * 0.67, 3.85, 0.51, "173C78"); addText(s, v[0], 8.62, 3.13 + i * 0.67, 0.88, 0.15, { fontSize: 11.5, bold: true, color: "78DCD4" }); addText(s, v[1], 9.52, 3.08 + i * 0.67, 2.52, 0.26, { fontSize: 9.8, color: "DDEBFF" }); });
note(s, "Pankaj explains the evidence confidence score. Say exactly what it measures: support coverage for the draft. Say exactly what it does not measure: crime likelihood, legality, or the correct decision.");

// 10. OKF / RAG
s = pptx.addSlide(); bg(s, C.mist); header(s, "OKF, chunks, and RAG", "A citation opens the exact stored passage", 10);
screen(s, "2026_evidence_source_chunks_detail.png", 0.67, 1.4, 6.95, 3.91);
addText(s, "Transparent retrieval path", 8.05, 1.6, 3.9, 0.28, { fontSize: 19, bold: true });
[["OKF source", "ID, scenario, title, criteria, and body"], ["Chunker", "C0 metadata + two-sentence passages"], ["Index", "SQLite FTS5 match + BM25 rank"], ["RAG review", "Retrieved IDs create cited, inspectable context"]].forEach((v, i) => { const y = 2.12 + i * 0.67; s.addShape(pptx.ShapeType.ellipse, { x: 8.06, y, w: 0.4, h: 0.4, fill: { color: i === 2 ? C.teal : C.blue }, line: { color: "FFFFFF", transparency: 100 } }); addText(s, `${i + 1}`, 8.06, y + 0.09, 0.4, 0.14, { fontSize: 9, bold: true, color: C.white, align: "center" }); addText(s, v[0], 8.65, y + 0.01, 1.05, 0.2, { fontSize: 12.5, bold: true }); addText(s, v[1], 9.72, y, 2.32, 0.28, { fontSize: 10, color: C.grey }); });
rounded(s, 0.72, 5.65, 11.9, 0.47, "EAF9F7"); addText(s, "OKF source  →  chunk builder  →  FTS5/BM25  →  retrieved IDs  →  cited response", 0.93, 5.78, 11.45, 0.16, { fontSize: 12, bold: true, color: C.teal, align: "center" });
note(s, "Pankaj explains the code path in plain language. OKF is the product's Open Knowledge Format source record. Point to the source chunks on the left. Explain FTS5 and BM25 as local keyword matching and ranking; retrieved IDs make a cited response inspectable, not proven true.");

// 10 Copilot
s = pptx.addSlide(); bg(s, C.navy); header(s, "InvestigateIQ Copilot", "Answers stay bounded by stored evidence", 11, true);
screen(s, "2026_evidence_copilot_open.png", 0.65, 1.42, 7.15, 4.02);
addText(s, "The Copilot can", 8.23, 1.67, 3.7, 0.25, { fontSize: 19, bold: true, color: C.white });
[["Summarize", "Stored fictional records and chunks"], ["Cite", "Source IDs and evidence gaps"], ["Explain", "The selected page and case context"]].forEach((v, i) => { node(s, v[0], 8.25, 2.25 + i * 0.76, i === 1 ? C.teal : C.blue); addText(s, v[1], 9.0, 2.61 + i * 0.76, 3.0, 0.18, { fontSize: 10.8, color: "DDEBFF" }); });
addText(s, "It cannot submit or alter a human decision.", 8.25, 5.14, 3.62, 0.34, { fontSize: 15, bold: true, color: "78DCD4" });
note(s, "Laxman demonstrates the floating Copilot. Explain that it stays inside the same case context. Do not imply that a response proves a fact or makes a workflow choice.");

// 11 Human and compliance
s = pptx.addSlide(); bg(s, C.mist); header(s, "Human decisions and Compliance", "Accountability belongs to named people", 12);
screen(s, "2026_compliance_queue_detail.png", 0.68, 1.42, 6.9, 3.88);
addText(s, "Investigator", 8.0, 1.7, 1.65, 0.26, { fontSize: 18, bold: true });
addText(s, "Records a required rationale for more information or escalation. A completed action appears as an immutable recorded state.", 8.0, 2.08, 4.3, 0.67, { fontSize: 14, color: C.grey, valign: "top" });
addText(s, "Compliance Officer", 8.0, 3.05, 2.2, 0.26, { fontSize: 18, bold: true });
addText(s, "Acknowledges, returns, or records an onward referral. These outcomes map back to distinct case statuses and audit events.", 8.0, 3.43, 4.35, 0.67, { fontSize: 14, color: C.grey, valign: "top" });
rounded(s, 8.0, 4.72, 4.35, 0.62, "EAF9F7"); addText(s, "No automated close, escalation, referral, or external filing", 8.25, 4.92, 3.85, 0.17, { fontSize: 12, bold: true, color: C.teal, align: "center" });
note(s, "Rahul Sharma explains the decision lock and separate Compliance review. State the three Compliance outcomes and their meaning: acknowledge, return, or referred onward. Emphasize that no external filing happens in this tool.");

// 12 Analytics
s = pptx.addSlide(); bg(s, C.navy); header(s, "Analytics", "Each graph names its measure and limitation", 13, true);
screen(s, "2026_analytics_charts.png", 0.67, 1.4, 7.4, 4.16);
addText(s, "What the charts describe", 8.48, 1.67, 3.65, 0.27, { fontSize: 19, bold: true, color: C.white });
[["Severity", "Stored labels"], ["Status", "Latest workflow state"], ["High share", "Percentage within a typology"], ["Monthly records", "Fictional source dates"], ["Actions", "Saved human events"]].forEach((v, i) => { rounded(s, 8.48, 2.12 + i * 0.55, 3.75, 0.38, "173C78"); addText(s, v[0], 8.65, 2.22 + i * 0.55, 1.1, 0.15, { fontSize: 10.5, bold: true, color: "78DCD4" }); addText(s, v[1], 9.8, 2.22 + i * 0.55, 2.15, 0.15, { fontSize: 10.5, color: "DDEBFF" }); });
addText(s, "Descriptive charts do not predict crime, assess staff productivity, or measure model accuracy.", 8.48, 5.1, 3.72, 0.42, { fontSize: 12.5, bold: true, color: "78DCD4", valign: "top" });
note(s, "Rahul Sharma explains each graph’s unit. Read axes before making any point about the chart. Make clear that the visuals summarize fictional stored data and workflow states.");

// 13 Search & team
s = pptx.addSlide(); bg(s, C.mist); header(s, "Context and ownership", "Search finds records; the team owns the explanation", 14);
screen(s, "2026_global_search.png", 0.68, 1.43, 5.85, 3.29);
screen(s, "2026_project_team_roles.png", 6.88, 1.43, 5.77, 3.25);
addText(s, "Global Search", 0.72, 5.0, 2.2, 0.27, { fontSize: 18, bold: true }); addText(s, "Find a fictional customer, account, transaction, or case, then return to the relevant context.", 0.72, 5.37, 5.65, 0.48, { fontSize: 13.5, color: C.grey, valign: "top" });
addText(s, "Role guide", 6.92, 5.0, 2.2, 0.27, { fontSize: 18, bold: true }); addText(s, "Workflow role labels explain responsibilities. They do not authenticate a person or grant protected Admin access.", 6.92, 5.37, 5.5, 0.48, { fontSize: 13.5, color: C.grey, valign: "top" });
note(s, "Soumya or Lakshmi covers this slide. Explain how Global Search shortens navigation, while Project and Team makes delivery ownership and role boundaries clear.");

// 15 Architecture
s = pptx.addSlide(); bg(s, C.mist); header(s, "Technical architecture and code logic", "A transparent Streamlit and SQLite implementation", 15);
const arch = [["Streamlit router", "Routes each left-navigation choice to a page module"], ["Page modules", "Read active case state; render queue, report, evidence, or review"], ["Shared UI", "Reusable banners, tooltips, themes, badges, and Copilot controls"], ["SQLite stores", "Fictional alerts, sources, chunks, audit events, and case scope"], ["Retrieval + checks", "FTS5/BM25, cited IDs, and deterministic evidence confidence"], ["Release assets", "Captures and builders; GitHub main to Railway verification"]];
arch.forEach((v, i) => { const col = i % 3, row = Math.floor(i / 3), x = 0.75 + col * 4.18, y = 1.65 + row * 2.13; rounded(s, x, y, 3.72, 1.38, i === 4 ? "E6F8F6" : "FFFFFF"); s.addShape(pptx.ShapeType.ellipse, { x: x + 0.22, y: y + 0.24, w: 0.45, h: 0.45, fill: { color: i === 4 ? C.teal : C.blue }, line: { color: "FFFFFF", transparency: 100 } }); addText(s, v[0], x + 0.85, y + 0.22, 2.6, 0.22, { fontSize: 14, bold: true }); addText(s, v[1], x + 0.23, y + 0.78, 3.12, 0.36, { fontSize: 11.2, color: C.grey, valign: "top" }); });
addText(s, "route → active case → SQLite / FTS5 → cited report → append-only human audit event", 1.13, 6.18, 11.0, 0.3, { fontSize: 16, bold: true, color: C.navy, align: "center" });
note(s, "Pankaj explains the technical design. Streamlit provides the pages and session context; SQLite stores the fictional material; FTS5 and BM25 retrieve inspectable chunks; a report is cited and any human decision becomes an append-only audit event. Rahul Chainani can answer a follow-up technical question after the presentation.");

// 16 Admin / controls
s = pptx.addSlide(); bg(s, C.navy); header(s, "Protected administration", "Admin tools remain visibly separate", 16, true);
screen(s, "2026_admin_knowledge_locked.png", 0.68, 1.42, 6.9, 3.88);
addText(s, "Knowledge Base", 8.02, 1.72, 3.45, 0.24, { fontSize: 19, bold: true, color: C.white });
addText(s, "Source and chunk inspection live behind a separate masked passcode. The Blueprint and demo never reveal or automate the passcode.", 8.02, 2.12, 4.08, 0.65, { fontSize: 15, color: "DDEBFF", valign: "top" });
addText(s, "Rule Config", 8.02, 3.25, 3.45, 0.24, { fontSize: 19, bold: true, color: C.white });
addText(s, "Rule previews explain fictional settings without silently regenerating case alerts. Restricted controls preserve a visible boundary in the demo.", 8.02, 3.64, 4.1, 0.65, { fontSize: 15, color: "DDEBFF", valign: "top" });
note(s, "Rahul Chainani explains the Admin boundary. Do not mention or enter a passcode. Explain that the restricted pages support source/rule inspection but do not claim production authentication.");

// 17 Testing/deploy
s = pptx.addSlide(); bg(s, C.mist); header(s, "Validation and deployment", "The product and walkthrough follow reproducible checks", 17);
const checks = [["Local validation", "Exercise the changed screen before release"], ["Workflow protection", "Avoid creating decisions, intake cases, or Compliance actions during a demo"], ["Visual QA", "Check light/dark contrast, tooltips, tables, charts, and pointer targets"], ["Release", "Commit intended files, push main, verify the Railway response" ]];
checks.forEach((v, i) => { const x = 0.85 + (i % 2) * 6.15, y = 1.72 + Math.floor(i / 2) * 1.82; rounded(s, x, y, 5.5, 1.26, i === 2 ? "E6F8F6" : "FFFFFF"); addText(s, `${i + 1}`, x + 0.25, y + 0.28, 0.42, 0.28, { fontSize: 20, bold: true, color: i === 2 ? C.teal : C.blue, align: "center" }); addText(s, v[0], x + 0.85, y + 0.23, 3.9, 0.25, { fontSize: 16, bold: true }); addText(s, v[1], x + 0.85, y + 0.64, 4.2, 0.3, { fontSize: 12, color: C.grey }); });
addText(s, "The current product walkthrough has been rebuilt from current native screens, captioned, and deployed with the updated navigation.", 1.05, 5.83, 11.15, 0.35, { fontSize: 16, bold: true, color: C.navy, align: "center" });
note(s, "Pankaj explains the validation and release approach. Mention that the video used current 1280 by 720 screens and that no production decision data was changed during capture.");

// 18. ROI and roadmap
s = pptx.addSlide(); bg(s, C.mist); header(s, "Value realization, ROI, and roadmap", "Measure the benefit first; do not claim it from fictional data", 18);
const roi = [["Efficiency", "Measure verified minutes saved locating a case record or exact source passage."], ["Rework", "Measure avoided Compliance returns and repeated evidence requests."], ["Audit readiness", "Measure time to reconstruct evidence, rationale, and outcome."], ["Safety", "Measure unsupported claims, broken citations, and unclear states found in review."]];
roi.forEach((v, i) => { const x = 0.75 + (i % 2) * 6.08, y = 1.55 + Math.floor(i / 2) * 1.23; rounded(s, x, y, 5.5, 0.95, i === 3 ? "E6F8F6" : "FFFFFF"); addText(s, v[0], x + 0.22, y + 0.18, 1.45, 0.2, { fontSize: 14, bold: true, color: i === 3 ? C.teal : C.blue }); addText(s, v[1], x + 1.55, y + 0.15, 3.65, 0.45, { fontSize: 11.2, color: C.grey, valign: "top" }); });
rounded(s, 0.75, 4.28, 11.8, 0.58, "173C78"); addText(s, "ROI % = (verified annual benefit − implementation and run cost) ÷ implementation and run cost × 100", 0.98, 4.47, 11.34, 0.18, { fontSize: 13, bold: true, color: C.white, align: "center" });
addText(s, "Next: 1) test fixtures and citation evaluation, 2) authentication and lineage versioning, 3) governed ingestion and approved integrations.", 0.9, 5.36, 11.5, 0.35, { fontSize: 16, bold: true, color: C.navy, align: "center" });
addText(s, "Planning model only: a real ROI requires a baseline, approved cost boundary, pilot evidence, and verified outcomes.", 0.9, 5.86, 11.5, 0.24, { fontSize: 11.5, italic: true, color: C.grey, align: "center" });
note(s, "Pankaj explains that ROI is a measurement framework, not a financial claim from fictional records. Name the four value levers, read the formula as a planning model, and then present the three-stage roadmap: evaluation first, governance controls next, and integrations only after approval.");

// 19 Closing
s = pptx.addSlide(); bg(s, C.navy);
addText(s, "InvestigateIQ", 0.78, 0.84, 5.2, 0.55, { fontSize: 35, bold: true, color: C.white });
addText(s, "A transparent review workflow for fictional AML investigations", 0.8, 1.6, 5.8, 0.36, { fontSize: 18, color: "C8D9F3" });
screen(s, "2026_workspace_confidence.png", 6.75, 0.9, 5.88, 3.31);
addText(s, "What we demonstrate", 0.8, 2.55, 4.2, 0.26, { fontSize: 18, bold: true, color: "78DCD4" });
[["Evidence traceability", "Sources, chunks, searches, and visible gaps"], ["Responsible AI", "Evidence confidence and explicit limitations"], ["Human accountability", "Named rationale, recorded actions, separate Compliance review"]].forEach((v, i) => { node(s, v[0], 0.82, 3.05 + i * 0.75, i === 1 ? C.teal : C.blue); addText(s, v[1], 1.56, 3.42 + i * 0.75, 4.7, 0.2, { fontSize: 11.5, color: "DDEBFF" }); });
addText(s, "Trace the evidence. Own the decision.", 0.8, 6.22, 7.25, 0.4, { fontSize: 24, bold: true, color: C.white }); addFooter(s, 19, true);
note(s, "Pankaj closes. Restate the narrow claim: the product helps people inspect supplied fictional evidence and document their reasoning. It does not prove guilt or legality, replace a human, or file a report.");

async function addFadeTransitions(file) {
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const names = Object.keys(zip.files).filter(name => /^ppt\/slides\/slide\d+\.xml$/.test(name));
  for (const name of names) {
    let xml = await zip.file(name).async("string");
    if (!xml.includes("<p:transition")) {
      const transition = '<p:transition spd="med" advClick="1"><p:fade/></p:transition>';
      if (xml.includes("</p:clrMapOvr>")) xml = xml.replace("</p:clrMapOvr>", `</p:clrMapOvr>${transition}`);
      else xml = xml.replace("</p:sld>", `${transition}</p:sld>`);
      zip.file(name, xml);
    }
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

function gtext(value, options = {}) { return new TextRun({ text: value, font: "Arial", size: options.size || 21, bold: !!options.bold, color: options.color || C.ink }); }
function gp(value, options = {}) { return new Paragraph({ children: [gtext(value, options)], heading: options.heading, spacing: { before: options.before || 0, after: options.after || 130, line: 276 } }); }
function gcell(value, width, shade) { return new TableCell({ width: { size: width, type: WidthType.DXA }, shading: shade ? { type: "clear", color: shade, fill: shade } : undefined, margins: { top: 80, bottom: 80, left: 100, right: 100 }, children: [gp(value, { size: 18, bold: shade === C.navy, color: shade === C.navy ? "FFFFFF" : C.ink, after: 0 })] }); }
async function buildGuide() {
  const rows = [
    { n: "1", title: "InvestigateIQ", time: "0:40", aim: "Set the fictional-product boundary and the core evidence-to-decision promise.", pointer: "Keep the pointer on the product name, then the words ‘Trace the evidence. Own the decision.’", script: "Good morning. We are presenting InvestigateIQ, an AI-assisted copilot for fictional AML case investigations. Its purpose is to keep the alert, the supporting material, the explanation, and the human decision connected. It assists a reviewer; it does not make legal or regulatory conclusions.", prep: "Confirm the cover is displayed at full slide size. Rahul Chainani is technical support for questions after the presentation; he does not need to speak during the 15-minute delivery." },
    { n: "2", title: "Project team", time: "0:45", aim: "Introduce the group in the agreed order and establish Pankaj as the single presenter.", pointer: "Move slowly down the roster from Rahul Chainani to Sweta Singh; do not point to an email address because none are shown.", script: "This is our project team. Rahul Chainani led application development and integration. I, Pankaj Bharsakale, led the AI workflow and evidence review. Lakshmi Dudgikar mapped requirements and the case study. Rahul Sharma covered quality and edge cases, Laxman Singh focused on user experience, Soumya coordinated the team and presentation, and Sweta Singh supported the course linkage and project explanation. I will present the product today.", prep: "Use the roster exactly as shown: Rahul Chainani, Pankaj Bharsakale, Lakshmi Dudgikar, Rahul Sharma, Laxman Singh, Soumya, then Sweta Singh last." },
    { n: "3", title: "The problem", time: "0:45", aim: "Explain why a monitoring alert is not a conclusion.", pointer: "Point first to the alert metadata items, then to the Case Queue image.", script: "A monitoring alert can prioritize a review, but it does not by itself prove wrongdoing. An investigator still needs the underlying records, a clear view of missing evidence, and a reasoned next action. InvestigateIQ connects those pieces instead of presenting an alert as a verdict.", prep: "Do not call any fictional alert suspicious, illegal, or confirmed. Say ‘needs review’ or ‘requires human assessment.’" },
    { n: "4", title: "Product workflow", time: "0:55", aim: "Walk through the one-case journey end to end.", pointer: "Reveal or point to the five steps from left to right, pausing briefly on Evidence & RAG and Human action.", script: "We follow one visible workflow. First, an investigator finds a case in the queue. Next, the workspace builds or replays a report. Then Evidence and RAG opens the exact stored material behind the report. A named person records a rationale, and Compliance can perform a separate second review. The system never closes, escalates, refers, or files an action automatically.", prep: "Let the fade transition complete before speaking to each stage. Keep the pointer on the stage being named." },
    { n: "5", title: "Product navigation", time: "0:40", aim: "Show that the left navigation follows the same work sequence.", pointer: "Trace only the core workspaces on the right-side list; do not wave across the screenshot.", script: "The reordered navigation mirrors the investigation sequence. We begin with the Home and Case Queue pages, move into the Investigation Workspace, then use Evidence and RAG to inspect support. Compliance, Analytics, and Global Search serve the later review and context steps. This reduces unnecessary navigation during an investigation.", prep: "Mention that Admin screens are deliberately separated from normal review work." },
    { n: "6", title: "Case Queue", time: "1:05", aim: "Explain filters and distinguish status, rules, and the action button.", pointer: "Point to the filters, then follow one row across Severity, Status, Rule(s), and Action.", script: "The Case Queue turns stored fictional alerts into a manageable workload. Filters narrow the queue by customer, status, severity, and scenario. In each row, severity is a priority label, status shows where the case is in the workflow, and Rule(s) records the trigger metadata. The action opens a current case or, for a completed case, lets us inspect the supporting evidence rather than reopening a decision.", prep: "Use one row only. State that ‘source closed’ is not the same as a human closure or a Compliance outcome." },
    { n: "7", title: "Investigation Workspace", time: "1:10", aim: "Explain the report modes, validator, and decision boundary.", pointer: "Point to Saved report, Calculated mode, and Validator in that order.", script: "The Investigation Workspace is where the reviewer reads the case report. A saved report replays a historical snapshot for a repeatable demonstration. Calculated mode recomputes from the current stored fictional rows. The validator surfaces notes before a decision, but running or replaying a report never records a decision by itself. The human remains responsible for the next action.", prep: "Do not call a calculated result an AI decision. If asked, explain that the optional AI draft remains advisory and is checked against available material." },
    { n: "8", title: "Evidence confidence", time: "0:55", aim: "Present the responsible-AI score with its limitations.", pointer: "Point to the score, then Coverage, Limitations, and Boundary—one at a time.", script: "After a report is available, the product shows evidence confidence. This is a deterministic support-coverage indicator: it summarizes how well the supplied records and guidance support the displayed draft, and it exposes known limitations. It is not a probability of crime, legality, money laundering, or the correct case outcome. The score is a prompt for human review, not an automated recommendation.", prep: "Say ‘support coverage’ every time; never shorten it to ‘risk score.’" },
    { n: "9", title: "OKF, chunks, and RAG", time: "1:20", aim: "Explain the key coding logic behind source ingestion, retrieval, and citations.", pointer: "Point to the source chunks screenshot on the left while describing steps 1–2; then point to Index and RAG review on the right and finally the code-flow strip.", script: "This is the core evidence-retrieval logic. Our OKF, or Open Knowledge Format, keeps a synthetic source ID, scenario, title, criteria, and body text together. The ingestion code creates a metadata chunk, called C0, and then small body chunks of about two sentences. SQLite FTS5 performs a local keyword search, BM25 ranks the matching chunks, and the retrieved chunk IDs become the context for a cited answer. The reviewer can open the exact passage. Retrieval helps find text; it does not prove that the text is true or that an alert is wrongdoing.", prep: "Be ready to define FTS5 as SQLite full-text search and BM25 as the ranking method for keyword matches. Use ‘RAG’—retrieval-augmented generation—not ‘REG.’" },
    { n: "10", title: "InvestigateIQ Copilot", time: "0:50", aim: "Show the Copilot’s limited, evidence-bound role.", pointer: "Point to the three allowed capabilities, then the sentence that it cannot submit or alter a decision.", script: "The InvestigateIQ Copilot can summarize the stored fictional records, cite source IDs and evidence gaps, and explain the selected case context. It remains bounded by the available material. It cannot verify an outside document, decide that funds are lawful or unlawful, or submit or change a human decision.", prep: "Keep the explanation short; the detailed retrieval logic was already covered on the previous slide." },
    { n: "11", title: "Human decisions and Compliance", time: "1:05", aim: "Explain append-only decisions and the three separate Compliance outcomes.", pointer: "Point first to Investigator, then Compliance Officer, then the no-automation statement.", script: "A decision becomes an accountable audit event only when a named investigator selects an allowed action and records a rationale. The completed form becomes a recorded state rather than being silently editable. Compliance is a separate human review. It can acknowledge with no further action, return the case for more information, or record an onward referral. Each result maps to a distinct queue state and audit history. The tool does not file externally.", prep: "Use ‘append-only audit event’ if a technical examiner asks why the form locks. Do not describe a referral as a regulatory filing." },
    { n: "12", title: "Analytics", time: "1:00", aim: "Explain every graph as descriptive stored-data analysis.", pointer: "Point to the title and axes of the chart currently being mentioned; never point at an unrelated plot.", script: "The Analytics page uses clearly named measures. Severity charts count stored labels. Status charts count the latest workflow state. High-severity share is a percentage within a typology. Monthly records describe fictional source dates, and decision charts count saved human events. These are descriptive charts—not a prediction of crime, a staff productivity score, or a model-accuracy measure.", prep: "Read both axis labels before interpreting a chart. If a graph has a small sample, say it is a count in the fictional dataset." },
    { n: "13", title: "Context and ownership", time: "0:40", aim: "Explain Global Search and the role guide.", pointer: "Point to Global Search on the left and the Role guide on the right, one after the other.", script: "Global Search is a context-finding tool: it helps the reviewer locate a fictional customer, account, transaction, or case and return to the relevant page. The role guide explains who performs the workflow activities. A displayed role label does not authenticate a person or grant Admin permission.", prep: "Keep the two concepts distinct: search finds context; roles clarify responsibilities." },
    { n: "14", title: "Technical architecture and code logic", time: "1:20", aim: "Connect the page experience to the actual implementation layers.", pointer: "Move across the six architecture cards from top left to bottom right; finish on the code-flow line.", script: "Technically, Streamlit routes each left-navigation selection to a page module. Each page reads the active case context and renders the appropriate queue, report, evidence, or Compliance interface. SQLite stores fictional alerts, sources, chunks, and audit events. FTS5 and BM25 retrieve reviewable passages, while deterministic checks calculate evidence confidence. The key flow is route to active case, then local storage and search, then cited report, then an append-only human audit event. The product favors inspectable logic instead of hidden autonomous behavior.", prep: "Rahul Chainani should be ready for technical questions on file structure, local SQLite, the FTS5 index, and Railway deployment after the talk." },
    { n: "15", title: "Protected administration", time: "0:40", aim: "Show the protected boundary without demonstrating the passcode.", pointer: "Point only to the locked screen and its explanatory text.", script: "Administration is visibly separated from normal case review. Knowledge Base and Rule Config support inspection of source material and fictional rule settings behind a masked passcode. We do not reveal or automate that passcode. The point is to make a boundary visible in this learning environment, not to claim production authentication.", prep: "Never type or speak the passcode during a demo." },
    { n: "16", title: "Validation and deployment", time: "0:45", aim: "Summarize how changes are checked and released.", pointer: "Point to each numbered validation card clockwise, then the final release statement.", script: "Our release path starts with exercising the changed screen locally. We protect the workflow by avoiding real decision creation during a demo, run visual checks for contrast, tooltips, tables, and charts, then commit intended files, push the main branch, and verify the Railway deployment by visiting the affected page. This makes the demonstration reproducible as well as presentable.", prep: "Do not claim a build log alone proves release success; say the live page is checked after deployment." },
    { n: "17", title: "Closing", time: "0:25", aim: "Close with the product’s narrow, responsible claim.", pointer: "Point to the three closing pillars, then leave the pointer still.", script: "InvestigateIQ makes the review path visible: the stored evidence, exact chunks, retrieval limits, confidence gaps, and accountable human action. It helps a reviewer inspect supplied fictional material. It does not prove guilt, legality, or wrongdoing, and it does not replace the human decision-maker. Thank you.", prep: "Pause for questions. Rahul Chainani can address implementation detail; Pankaj remains the presenter and first responder." },
  ];
  const programRow = { title: "Program statement", aim: "State the capstone commitment, success measures, and non-goals before the product tour.", pointer: "Hold the pointer on the central Program Statement, then move through Problem, Program outcome, Success measures, and Non-goals.", script: "Our program statement is simple: we are designing and demonstrating a transparent, AI-assisted workflow for fictional AML case review. Every report claim should be traceable to supplied material, every limitation should be visible, and every workflow action must remain a named human decision. We measure success through traceability, clear states, visible gaps, and required rationale—not automated outcomes.", prep: "Do not shorten the program statement to an AI claim. Read the non-goals: no real data, autonomous action, legal conclusion, or external filing." };
  const roiRow = { title: "Value realization, ROI, and roadmap", aim: "Present a measurable ROI planning model and the future roadmap without claiming a financial result from fictional data.", pointer: "Move through the four value levers, the ROI formula, then the three future steps at the bottom.", script: "We do not claim financial ROI from fictional data. Instead, we define how a real pilot would measure value: verified time saved finding records and source passages, reduced rework, faster audit reconstruction, and fewer unsupported claims or unclear workflow states. Once a baseline and approved cost boundary exist, ROI can be calculated from verified annual benefit minus implementation and run cost. Our roadmap starts with evaluation fixtures and citation tests, adds authentication and evidence-lineage versioning, and only then considers governed ingestion and approved integrations.", prep: "Call the formula a planning model, not a current result. If asked for a number, explain that it requires pilot baseline data and approved cost assumptions." };
  const presentationRows = [rows[0], rows[1], programRow, ...rows.slice(2, -1), roiRow, rows[rows.length - 1]].map((r, i) => ({ ...r, n: String(i + 1), time: ["0:35", "0:40", "0:45", "0:40", "0:50", "0:35", "0:50", "1:00", "0:50", "1:20", "0:40", "1:00", "0:55", "0:35", "1:10", "0:35", "0:45", "0:45", "0:30"][i] }));
  const outlineRows = presentationRows.map(r => [r.n, r.title, "Pankaj Bharsakale", r.aim, r.time]);
  const doc = new Document({ creator: "Capstone Group 7", title: "InvestigateIQ Deck Presenter Guide", sections: [{ properties: { page: { margin: { top: 720, bottom: 720, left: 720, right: 720 } } }, children: [
    gp("InvestigateIQ Deck Presenter Guide", { heading: HeadingLevel.TITLE, size: 36, bold: true, color: C.navy, after: 180 }),
    gp("15-minute, single-presenter script for the Product Blueprint presentation", { size: 22, color: C.grey, after: 360 }),
    gp("How to use this guide", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy }),
    gp("Pankaj Bharsakale is the single presenter for this 15-minute deck. Rahul Chainani is the technical preparation and question-support contact. The presenter should let each fade settle, speak to the item under the pointer, and keep every case, source, chart, and record described as fictional.", { size: 20 }),
    new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [520, 1800, 1700, 4300, 1040], rows: [new TableRow({ children: [gcell("#", 520, C.navy), gcell("Slide", 1800, C.navy), gcell("Presenter", 1700, C.navy), gcell("Purpose", 4300, C.navy), gcell("Time", 1040, C.navy)] }), ...outlineRows.map(r => new TableRow({ children: r.map((v, i) => gcell(v, [520, 1800, 1700, 4300, 1040][i])) }))] }),
    gp("Speaker script and stage direction", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy, before: 260 }),
    ...presentationRows.flatMap(r => [
      gp(`${r.n}. ${r.title} — ${r.time}`, { heading: HeadingLevel.HEADING_2, size: 24, bold: true, color: C.navy, before: 220, after: 80 }),
      gp(`Pankaj says: “${r.script}”`, { size: 19, after: 80 }),
      gp(`Pointer and pacing: ${r.pointer}`, { size: 18, bold: true, color: C.teal, after: 60 }),
      gp(`Rahul prepares: ${r.prep}`, { size: 18, color: C.grey, after: 130 }),
    ]),
    gp("Presentation guardrails", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy, before: 260 }),
    gp("1. Say fictional data whenever discussing a case, record, customer, transaction, or chart.  2. Describe a citation as a pointer to inspect, not proof.  3. Describe evidence confidence as support coverage, never a risk or crime probability.  4. State that only a named person records an action.  5. Do not show or speak an Admin passcode.", { size: 20 }),
    gp("Suggested close", { heading: HeadingLevel.HEADING_1, size: 28, bold: true, color: C.navy, before: 260 }),
    gp("InvestigateIQ makes the review path visible: the alert, the exact stored material, the evidence gaps, the bounded explanation, and the accountable human action. It helps a reviewer inspect the supplied material; it does not make legal, regulatory, or factual conclusions for them.", { size: 20 }),
  ] }] });
  fs.writeFileSync(guideFile, await Packer.toBuffer(doc));
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  await pptx.writeFile({ fileName: deckFile });
  await addFadeTransitions(deckFile);
  await buildGuide();
  console.log(deckFile); console.log(guideFile);
})().catch(err => { console.error(err); process.exit(1); });
