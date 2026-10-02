// Rebuild the course-facing technical walkthrough from verified repository facts.
// Run: node scripts/build_technical_presentation.js
const path = require('path');
const PptxGenJS = require('C:/Users/HP/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pptxgenjs');

const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'InvestigateIQ';
pptx.subject = 'Verified technical flow of the InvestigateIQ course prototype';
pptx.title = 'InvestigateIQ | Technical Flow and Code Walkthrough';
pptx.company = 'Capstone Group 7';
pptx.lang = 'en-IN';

const W = 13.333, H = 7.5;
const C = {
  navy: '10203B', navy2: '172D50', ink: '172840', muted: '5B6C81',
  paper: 'F6F9FD', white: 'FFFFFF', blue: '2E67B7', teal: '087E8B',
  cyan: 'D9F2F5', pale: 'E8F0FA', amber: 'B06A14', gold: 'F8E7BF',
  green: '247352', mint: 'E1F4EB', red: 'A24040', rose: 'F8E9E9',
  border: 'C8D6E8', violet: '7657A6', lavender: 'EEE8F8'
};
const S = pptx.ShapeType;
function txt(slide, text, x, y, w, h, o={}) {
  slide.addText(text, {x,y,w,h,margin:0,isTextBox:true,fontFace:'Arial',fontSize:15,
    color:C.ink,breakLine:false,fit:'shrink',valign:'mid',...o});
}
function box(slide,x,y,w,h,fill=C.white,line=C.border,r=0.16) {
  slide.addShape(S.roundRect,{x,y,w,h,rectRadius:r,
    fill:{color:fill},line:{color:line,width:1.2},radius:r});
}
function circle(slide,x,y,d,fill,label,color=C.white) {
  slide.addShape(S.ellipse,{x,y,w:d,h:d,fill:{color:fill},line:{color:fill}});
  txt(slide,label,x,y,d,d,{fontSize:17,bold:true,color,align:'center'});
}
function dotted(slide,x1,y1,x2,y2,color=C.teal) {
  const dx=x2-x1,dy=y2-y1,dist=Math.hypot(dx,dy);
  const count=Math.max(3,Math.floor(dist/0.09));
  for(let i=0;i<count;i++){
    const t=i/count,d=0.028;
    slide.addShape(S.ellipse,{x:x1+dx*t-d/2,y:y1+dy*t-d/2,w:d,h:d,
      fill:{color},line:{color}});
  }
  txt(slide,Math.abs(dx)>Math.abs(dy)?(dx>=0?'›':'‹'):(dy>=0?'⌄':'⌃'),x2-0.09,y2-0.14,0.18,0.28,
      {fontSize:20,bold:true,color,align:'center'});
}
function base(title,kicker='TECHNICAL WALKTHROUGH',dark=false) {
  const slide=pptx.addSlide(); slide.background={color:dark?C.navy:C.paper};
  if(title) {
    txt(slide,kicker.toUpperCase(),0.58,0.38,11,0.25,{fontSize:10,bold:true,color:dark?'9CCFE5':C.teal,charSpacing:1.3});
    txt(slide,title,0.58,0.75,12.15,0.62,{fontSize:31,bold:true,color:dark?C.white:C.navy});
  }
  const n=pptx._slides.length;
  txt(slide,'InvestigateIQ  /  Capstone Group 7',0.58,7.12,7,0.18,{fontSize:9,color:dark?'A9BDD7':C.muted});
  txt(slide,String(n).padStart(2,'0'),12.1,7.1,0.6,0.18,{fontSize:9,color:dark?'A9BDD7':C.muted,align:'right'});
  return slide;
}
function card(slide,{x,y,w,h,n,title,body,color=C.blue,fill=C.white,bodySize=13}) {
  box(slide,x,y,w,h,fill,C.border);
  circle(slide,x+0.18,y+0.2,0.46,color,n);
  txt(slide,title,x+0.77,y+0.17,w-0.96,0.48,{fontSize:17,bold:true,color:C.navy});
  txt(slide,body,x+0.2,y+0.79,w-0.4,h-0.94,{fontSize:bodySize,color:C.muted,valign:'top'});
}
function note(slide,body){slide.addNotes(body);}
function smallTag(slide,label,x,y,w,fill=C.pale,color=C.blue){
  box(slide,x,y,w,0.32,fill,fill,0.1); txt(slide,label,x+0.08,y+0.01,w-0.16,0.28,{fontSize:10,bold:true,color,align:'center'});
}

// 01 — Title
{
  const s=base(null,'',true);
  txt(s,'InvestigateIQ',0.72,1.0,8.5,0.9,{fontSize:46,bold:true,color:C.white});
  txt(s,'Trace the evidence. Own the decision.',0.75,2.03,9.7,0.52,{fontSize:23,color:'BFEAF0'});
  txt(s,'Technical flow + code walkthrough',0.75,2.88,9.7,0.48,{fontSize:21,bold:true,color:C.white});
  txt(s,'How an alert becomes an evidence-linked draft, then a human decision.',0.75,3.48,9.3,0.58,{fontSize:17,color:'C2D3E8'});
  const nodes=[['A','Alert'],['E','Evidence'],['R','Retrieve'],['D','Draft'],['V','Validate'],['H','Human']];
  nodes.forEach((p,i)=>{const x=0.83+i*2.08; circle(s,x,5.15,0.58,i===5?C.amber:C.teal,p[0]);txt(s,p[1],x-0.12,5.84,0.82,0.3,{fontSize:11,color:C.white,align:'center'});if(i<5)dotted(s,x+0.65,5.44,x+1.96,5.44,'6EC9D2');});
  note(s,'Open with the product promise: AI helps prepare an investigation; a person owns the decision. The data shown is fictional. This is a course prototype, not a live bank monitoring or regulatory filing system.');
}

// 02 — Purpose and boundary
{
  const s=base('A narrow problem, with a clear boundary','01 / WHY THIS EXISTS');
  card(s,{x:0.65,y:1.65,w:5.75,h:3.62,n:'?',title:'The investigator’s problem',body:'A monitoring alert is only a signal. Someone must connect customer context, transactions, relationships, documents and guidance before reaching a reasoned conclusion.',color:C.blue,bodySize:18});
  card(s,{x:6.84,y:1.65,w:5.75,h:3.62,n:'!',title:'What this product does',body:'One workspace assembles those records, retrieves relevant synthetic playbook text, drafts a cited report, checks selected claims and records a human action.',color:C.teal,bodySize:18});
  smallTag(s,'BUILT: investigation workflow',0.74,5.7,3.3,C.mint,C.green);
  smallTag(s,'NOT BUILT: real bank feed or filing',4.35,5.7,4.1,C.rose,C.red);
  smallTag(s,'DATA: fictional',8.82,5.7,2.2,C.gold,C.amber);
  note(s,'Explain the distinction between alert and finding. An alert is a reason to investigate, not proof of fraud. The application is intentionally scoped to post-alert case work. The source data is synthetic.');
}

// 03 — Full flow
{
  const s=base('One case, end to end','02 / THE OPERATING FLOW');
  const a=[
    ['1','Review alert','Imported or calculated'],['2','Case selected','Investigation Workspace'],
    ['3','Facts gathered','Six stages or intake packet'],['4','Guidance found','FTS5 / BM25'],
    ['5','Draft + checks','Calculated or Gemini'],['6','Human decision','Rationale + audit'],
    ['7','Compliance review','Only if escalated'],['8','Explore & explain','Search / Analytics / RAG']
  ];
  a.forEach((v,i)=>{let row=i<4?0:1,col=i<4?i:7-i,x=0.62+col*3.2,y=1.72+row*2.25;card(s,{x,y,w:2.87,h:1.78,n:v[0],title:v[1],body:v[2],color:i<4?C.teal:C.blue,bodySize:12});if(i<3)dotted(s,x+2.91,y+0.91,x+3.18,y+0.91);if(i>=4&&i<7)dotted(s,x-0.04,y+0.91,x-0.27,y+0.91);});
  dotted(s,11.66,3.55,11.66,3.8,C.amber);
  txt(s,'Escalation is a human action. “Referred” is recorded internally; the app does not file an STR.',0.73,6.34,11.75,0.42,{fontSize:15,bold:true,color:C.red});
  note(s,'Walk through this left to right, top row then bottom row. The last box contains supporting views rather than a mandatory sequential step. For rebuilt-source cases, the six-stage workflow can produce a calculated or optional Gemini draft, and a human may request information, close or escalate. Feature-gated fictional-intake cases instead use a separate calculated review of their stored runtime packet: it recomputes the rule, checks hashes and chunks, shows missing original KYC and source-of-funds evidence, and permits only request-for-information or human escalation. Do not imply those cases ran through the six agents or Gemini.');
}

// 04 — Alert source
{
  const s=base('Where does the alert come from?','03 / ALERT ORIGIN');
  card(s,{x:0.66,y:1.7,w:3.58,h:2.23,n:'1',title:'Fictional inputs',body:'42 workbook alerts, two matched fixtures, and optional numeric-only intake.',color:C.teal});
  card(s,{x:4.87,y:1.7,w:3.58,h:2.23,n:'2',title:'Calculate + store',body:'The rule calculates signals; enabled intake stores synthetic rows and labeled chunks separately.',color:C.blue});
  card(s,{x:9.08,y:1.7,w:3.58,h:2.23,n:'3',title:'Case Queue',body:'44 source alerts plus feature-gated new fictional cases open their matching review path.',color:C.violet});
  dotted(s,4.27,2.77,4.82,2.77);dotted(s,8.49,2.77,9.03,2.77);
  box(s,0.73,4.48,11.86,1.33,C.gold,C.amber);
  txt(s,'Future integration point',1.0,4.76,3.0,0.35,{fontSize:18,bold:true,color:C.amber});
  txt(s,'A bank-owned monitoring platform could send alerts through an authenticated API or batch feed into an ingestion layer. That endpoint, contract, validation and queue consumer do not exist in this code.',4.05,4.58,8.1,0.95,{fontSize:15,color:C.ink});
  txt(s,'Rule Config only previews sensitivities; changing sliders does not regenerate existing alerts.',0.78,6.24,11.8,0.38,{fontSize:13,bold:true,color:C.red});
  note(s,'If asked “Where is the third-party alert webhook?”, answer directly: there is none. Forty-two alerts are imported from the fictional workbook, and two are calculated from fictional transaction fixtures during the local database build. The Rule Lab only recalculates in memory. Separately, ENABLE_FICTIONAL_INTAKE=1 exposes numeric-only course intake: data/fictional_intake.py rejects non-synthetic IDs, stores a qualifying batch in runtime SQLite, generates labeled sample records and exact FTS5 chunks, and the Case Queue opens a separate calculated review. This is not an authenticated upload or real bank feed. A real feed needs identity, contracts, validation, deduplication, secure storage and compliance ownership. Rule Config previews sensitivities; it does not regenerate existing alerts.');
}

// 05 — Matched case example
{
  const s=base('CASE-043: calculate the signal; inspect the gaps','04 / CONCRETE EXAMPLE');
  smallTag(s,'Arjun Mehta  ·  ACC-TEST-01  ·  fictional',0.66,1.48,5.9,C.pale,C.blue);
  const metrics=[
    ['4 credits','₹300,000 each = ₹1,200,000'],
    ['6 debits','₹180,000 each = ₹1,080,000'],
    ['Baseline','₹80,000 monthly credit (six months)'],
    ['Rule result','15× baseline · 90% out · 6 beneficiaries']
  ];
  metrics.forEach((v,i)=>{let y=2.05+i*0.83;box(s,0.69,y,6.15,0.67,i%2?C.white:C.pale,C.border);txt(s,v[0],0.92,y+0.13,1.65,0.35,{fontSize:15,bold:true});txt(s,v[1],2.55,y+0.1,4.0,0.4,{fontSize:14,color:C.blue,bold:i===3});});
  box(s,7.15,2.05,5.4,3.43,C.white,C.border);
  circle(s,7.43,2.38,0.59,C.amber,'?');
  txt(s,'Evidence still missing',8.18,2.36,3.98,0.43,{fontSize:19,bold:true});
  txt(s,'No original PAN/OVD files. All 10 distinct counterparties lack a mapped customer profile here; KYC is unknown. No independent funds proof or external-bank posting confirmation.',7.48,3.15,4.6,1.45,{fontSize:15,color:C.ink});
  txt(s,'Customer explanation is uncorroborated.',7.48,4.8,4.6,0.38,{fontSize:15,bold:true,color:C.teal});
  txt(s,'The same ten-transaction signal also fires for CASE-044. Neither case is a fraud verdict.',0.73,6.2,11.8,0.52,{fontSize:16,bold:true,color:C.red});
  note(s,'Use CASE-043 as the safer current-build example: both it and CASE-044 were derived from Rahul’s matched test data, but their hidden proposed outcomes were deliberately omitted. Four incoming rows total INR 1.2 million; six outgoing rows total INR 1.08 million. The source account has a six-month INR 80,000 monthly credit baseline, so incoming is 15 times baseline and outbound is 90 percent of incoming. These are account activity aggregates, not proof that any particular incoming rupee funded a particular outgoing payment. All ten distinct counterparties on completed rows lack mapped customer profiles in this dataset; a mapped profile would not itself prove verified KYC, and other banks may hold records we cannot see. The opening INR 20,000 and ending INR 140,000 balance are fixture assumptions. The right next step is to request original evidence and verify counterparty identities; do not infer legality. CASE-041 remains in the deployed video, but its older captured material is separate and must not be mistaken for this new case.');
}

// 06 — data model
{
  const s=base('Two data stores, two jobs','05 / DATABASE MODEL');
  box(s,0.65,1.64,5.75,4.58,C.white,C.border);
  circle(s,0.96,1.94,0.61,C.blue,'S');
  txt(s,'Source SQLite',1.75,1.95,4.1,0.44,{fontSize:22,bold:true});
  txt(s,'data/investigateiq.db',1.0,2.54,4.9,0.3,{fontSize:13,color:C.teal,bold:true});
  txt(s,'Customers 554  •  Accounts 676\nTransactions 9,982  •  Alerts 44\nCase source records 1,770\nCase chunks 4,282  •  KB chunks 57',1.0,3.12,4.88,2.17,{fontSize:16,breakLine:false,valign:'top',color:C.ink});
  box(s,6.86,1.64,5.75,4.58,C.white,C.border);
  circle(s,7.17,1.94,0.61,C.teal,'R');
  txt(s,'Runtime SQLite',7.96,1.95,4.1,0.44,{fontSize:22,bold:true});
  txt(s,'data/investigateiq_runtime.db',7.21,2.54,4.9,0.3,{fontSize:13,color:C.teal,bold:true});
  txt(s,'Human actions and rationale\nAudit events and rule settings\nGated fictional intake: 10 rows, 5 generated records and exact chunks per saved case\nMounted volume preserves runtime state.',7.21,3.12,4.88,2.17,{fontSize:15,valign:'top',color:C.ink});
  txt(s,'IDs link cases to rows and chunks. One source account ID has two owners: attribution is withheld.',0.74,6.42,11.85,0.46,{fontSize:14,bold:true,color:C.navy});
  note(s,'The source SQLite file is rebuilt deterministically from a fictional workbook plus two fictional matched fixtures. The runtime file preserves user actions, audit history and feature-gated fictional intake packets. A saved qualifying intake case has 10 synthetic transaction rows, five labeled generated records, exact paragraph chunks and a separate case-scoped FTS5 index; it is not a real bank upload. The 1,770 source case records are generated text/row representations, not 1,770 uploaded documents. Original identity uploads remain zero. The workbook has an ACC-1004 collision between CUST-1004 and CUST-0004, so the code warns and withholds ownership-specific conclusions for older cases. Avoid saying the runtime audit is tamper-proof. Code: data/build_database.py, data/case_evidence.py, data/fictional_intake.py and data/runtime_db.py.');
}

// 07 — specialists
{
  const s=base('Six narrow components, one fixed sequence','06 / ORCHESTRATION');
  const stages=[
    ['1','Alert Triage','Find selected alert and its scenario.'],
    ['2','Customer / KYC','Load profile, account and past cases.'],
    ['3','Transaction Review','Collect window; compute two distinct ratios.'],
    ['4','Relationship Review','Show linked records; stop at uncertain owners.'],
    ['5','Evidence Retrieval','Load case passages + playbook chunks.'],
    ['6','Investigation Summary','Calculated draft or optional Gemini draft.']
  ];
  stages.forEach((v,i)=>{let row=Math.floor(i/3),col=i%3,x=0.7+col*4.24,y=1.62+row*2.16;card(s,{x,y,w:3.8,h:1.82,n:v[0],title:v[1],body:v[2],color:i===5?C.amber:C.teal,bodySize:13});if(col<2)dotted(s,x+3.84,y+0.9,x+4.16,y+0.9);});
  txt(s,'Source cases use this sequence. Gated intake cases use a separate calculated review, not these six stages.',0.73,6.2,11.9,0.45,{fontSize:14,bold:true,color:C.navy});
  note(s,'This is a decomposed fixed workflow, not six autonomous planning agents. Stages 1–5 use Python, SQLite and search. Stage 6 can use a non-generative calculated draft or optional Gemini. The single-trigger amount / average-transaction ratio is not the same as 24-hour aggregate incoming / six-month monthly credit baseline. GroundingValidator runs after the draft and cannot guarantee factual correctness. Code: agents/orchestrator.py, agents/transaction_investigation_agent.py, agents/calculated_summary.py.');
}

// 08 — RAG
{
  const s=base('RAG: the answer has a visible source path','07 / RETRIEVAL');
  const steps=[
    ['1','Source sets','Guidance, generated case records, and gated intake packets.'],
    ['2','Make chunks','Guidance: metadata + 2 sentences; case/intake: paragraphs.'],
    ['3','Index','57 guidance + 4,282 source-case chunks; intake index separate.'],
    ['4','Retrieve','Scenario or case scope; FTS5 keyword matches.'],
    ['5','Inspect','Open exact source text, chunk ID and data limitations.']
  ];
  steps.forEach((v,i)=>{let x=0.67+i*2.54;card(s,{x,y:1.77,w:2.27,h:3.56,n:v[0],title:v[1],body:v[2],color:i%2?C.blue:C.teal,bodySize:13});if(i<4)dotted(s,x+2.31,3.53,x+2.50,3.53);});
  box(s,0.78,5.73,11.76,0.75,C.cyan,C.teal);
  txt(s,'This is keyword-search RAG, not vector search. A citation points to a source; it is not proof that every sentence is correct.',1.04,5.92,11.2,0.36,{fontSize:15,bold:true,color:C.navy});
  note(s,'The rebuilt source has two retrieval corpora: 24 synthetic playbooks and 1,770 generated case records. Playbook C0 holds title/escalation criteria and body chunks group two sentences. Source-case records use exact paragraph chunks with source row IDs, SHA-256, case/customer scope and verification status. Separately, each saved feature-gated intake packet has five generated records and its own case-scoped FTS5 paragraph index; its calculated review searches that index but does not feed the six-stage/Gemini pipeline. This is keyword retrieval, not vector embeddings. Generated fictional PAN/OVD samples are deliberately invalid and clearly marked; they are not original KYC scans or independently verified evidence. Evidence & RAG exposes exact source and chunks on-site. The review-window link register shows recorded endpoints, customer mappings, dataset KYC fields, original-file counts and link quality; this is ledger visibility, not verified settlement. Code: data/knowledge_search.py, data/case_evidence.py, data/fictional_intake.py, data/fund_flow.py, agents/evidence_agent.py and pages/8_Evidence_RAG.py.');
}

// 09 — draft and checks
{
  const s=base('From retrieved facts to a checked draft','08 / COPILOT + GROUNDING');
  card(s,{x:0.68,y:1.66,w:3.57,h:2.48,n:'F',title:'Fact packet',body:'Case IDs, KYC status, transaction math, ownership gaps, case passages and guidance.',color:C.teal,bodySize:14});
  card(s,{x:4.88,y:1.66,w:3.57,h:2.48,n:'D',title:'Draft choice',body:'Calculated source-anchored draft works without AI; Gemini can draft from controlled context.',color:C.blue,bodySize:14});
  card(s,{x:9.07,y:1.66,w:3.57,h:2.48,n:'V',title:'Selected checks',body:'Validator checks cited IDs, chunk references, selected ratios and verdict-like wording.',color:C.amber,bodySize:14});
  dotted(s,4.29,2.9,4.84,2.9);dotted(s,8.49,2.9,9.03,2.9);
  box(s,0.78,4.75,5.75,1.14,C.mint,C.green);
  txt(s,'Calculated mode: no model needed',1.03,5.0,5.25,0.42,{fontSize:17,bold:true,color:C.green});
  box(s,6.8,4.75,5.75,1.14,C.gold,C.amber);
  txt(s,'Optional Gemini + five saved reports',7.05,5.0,5.25,0.42,{fontSize:17,bold:true,color:C.amber});
  txt(s,'A “PASS” is only a pass of selected automated checks; it is not a factual or legal guarantee.',0.82,6.38,11.7,0.38,{fontSize:14,bold:true,color:C.red});
  note(s,'The calculated draft uses current database facts and missing-evidence markers without calling a model. Gemini can draft a JSON-shaped report when configured; five saved reports support replay. The validator checks selected reference and math claims but can miss unsupported statements. A citation is not independent proof, and a PASS is not a legal assessment. The chat panel is separate. Code: agents/calculated_summary.py, agents/investigation_summary_agent.py, agents/grounding_validator.py, agents/chat_agent.py.');
}

// 10 — human gate
{
  const s=base('The human decision is the record','09 / HUMAN-IN-THE-LOOP');
  const options=[
    ['C','Close','Record why the alert does not need further investigation.',C.green,C.mint],
    ['I','Request information','Identify the missing business context or evidence.',C.amber,C.gold],
    ['E','Escalate','Send the case to a separate Compliance queue.',C.red,C.rose]
  ];
  options.forEach((v,i)=>card(s,{x:0.7+i*4.22,y:1.83,w:3.76,h:2.58,n:v[0],title:v[1],body:v[2],color:v[3],fill:v[4],bodySize:14}));
  box(s,0.76,4.99,11.8,1.07,C.white,C.border);
  circle(s,1.02,5.2,0.5,C.blue,'✓');
  txt(s,'Investigator name + written rationale are required; accepted findings and the action are saved to runtime SQLite with an audit event.',1.73,5.16,10.3,0.62,{fontSize:16,bold:true,color:C.navy});
  txt(s,'Gated intake cases cannot be closed with no concern while original identity and funds evidence is missing.',0.84,6.34,11.75,0.38,{fontSize:14,bold:true,color:C.red});
  note(s,'Show the Human Decision panel. AI can suggest an outcome but cannot submit it. For rebuilt-source cases, the reviewer can accept or reject individual draft findings and choose close, request information or escalate with a rationale. Feature-gated intake cases have a separate calculated review; because original KYC and independent fund-source evidence are missing, it allows only request information or escalate, not no-concern closure. Both paths record a named human action and rationale in runtime SQLite. The selected display role is not real authentication.');
}

// 11 — compliance
{
  const s=base('Escalation leads to another human review','10 / COMPLIANCE + AUDIT');
  card(s,{x:0.75,y:1.88,w:3.56,h:2.9,n:'1',title:'Investigator escalates',body:'The saved decision changes the visible case status and puts the case in Compliance Queue.',color:C.red,bodySize:15});
  card(s,{x:4.87,y:1.88,w:3.56,h:2.9,n:'2',title:'Officer reviews',body:'A compliance officer can acknowledge, return for more work or record a referral.',color:C.blue,bodySize:15});
  card(s,{x:8.99,y:1.88,w:3.56,h:2.9,n:'3',title:'Audit persists',body:'Human action, rationale and timestamps are written to the runtime database on a mounted volume.',color:C.teal,bodySize:15});
  dotted(s,4.34,3.25,4.83,3.25);dotted(s,8.46,3.25,8.95,3.25);
  box(s,0.88,5.35,11.6,0.83,C.rose,C.red);
  txt(s,'“Referred” is an internal recorded state. The app does not file an STR with FIU-IND or any regulator.',1.12,5.55,11.1,0.41,{fontSize:17,bold:true,color:C.red});
  note(s,'The Compliance Queue derives escalated cases from latest saved human decisions, not from LLM output alone. It records a second human action and rationale. Audit is persistent in this deployment but should not be described as immutable, legally certified or bank-grade. Code: pages/3_Compliance_Queue.py and data/runtime_db.py.');
}

// 12 — screens
{
  const s=base('What each screen is for','11 / NAVIGATION MAP');
  const v=[
    ['Home','Purpose, walkthrough, entry'],['Case Queue','Filter and open alerts'],['Investigation','Evidence, chat, decision'],
    ['Compliance','Review escalations'],['Analytics','Population trends'],['Global Search','Find records by ID/name'],
    ['Evidence & RAG','Chunks + Rule Lab + gated intake'],['Admin: KB','Inspect indexed guidance'],['Admin: Rules','Preview/save thresholds']
  ];
  v.forEach((p,i)=>{let col=i%3,row=Math.floor(i/3),x=0.7+col*4.22,y=1.52+row*1.61;card(s,{x,y,w:3.76,h:1.37,n:String(i+1),title:p[0],body:p[1],color:i<3?C.teal:i<6?C.blue:C.violet,bodySize:12});});
  txt(s,'Project & Team is a separate identity/roster page. Roles listed there are proposals pending team confirmation.',0.76,6.6,11.8,0.3,{fontSize:13,color:C.muted});
  note(s,'Demonstrate these pages in flow order, not menu order. Home introduces the product. Queue is the operational entry. Investigation is the main work area. Compliance is downstream only if escalated. Search, Analytics, RAG and Admin are supporting/explanatory views. The roster is a draft; confirm names and assignments with the group.');
}

// 13 — design decisions and course map
{
  const s=base('Why this mix of technologies?','12 / COURSE CONCEPT → CODE');
  const rows=[
    ['Data foundation','Workbook → SQLite','Repeatable rows, IDs and calculated test alerts','data/build_database.py'],
    ['Hybrid AI','Rules + search + Gemini','Deterministic facts before optional drafting','agents/orchestrator.py'],
    ['RAG','Scoped chunk retrieval','Case and guidance text inspectable on-site','data/case_evidence.py'],
    ['Responsible AI','Validator + human gate','Drafts are reviewable, not final decisions','agents/grounding_validator.py'],
    ['Governance','Audit and Compliance','Actions have names, reasons and sequence','data/runtime_db.py']
  ];
  rows.forEach((r,i)=>{let y=1.62+i*0.94;box(s,0.69,y,11.93,0.73,i%2?C.white:C.pale,C.border);circle(s,0.88,y+0.15,0.39,i%2?C.blue:C.teal,String(i+1));txt(s,r[0],1.47,y+0.12,2.23,0.47,{fontSize:15,bold:true});txt(s,r[1],3.68,y+0.12,2.41,0.47,{fontSize:14,color:C.blue});txt(s,r[2],6.04,y+0.1,3.82,0.5,{fontSize:13});txt(s,r[3],10.02,y+0.13,2.34,0.43,{fontSize:10,color:C.muted});});
  note(s,'Use the same oral pattern for each row: course idea; actual problem; exact file/screen; reason for this choice; honest boundary. Case studies can motivate principles but do not prove our results. In particular, DBS/Erica/BMW inform human oversight; they are not Indian regulatory evidence. Source: Product Docs/15-Course-Concept-Application-Map.md.');
}

// 14 — results and limits
{
  const s=base('What we can show—and what remains open','13 / RESULTS + GAPS');
  card(s,{x:0.7,y:1.62,w:5.68,h:4.45,n:'✓',title:'Verified locally + publicly',body:'103 automated tests pass locally; GitHub CI passes.\n44 source alerts; public fictional intake adds saved cases.\nPublic QA: 10 rows, 5 generated records, 15 chunks; escalation reached Compliance.',color:C.green,fill:C.mint,bodySize:16});
  card(s,{x:6.92,y:1.62,w:5.68,h:4.45,n:'→',title:'Before real bank use',body:'No authenticated bank feed or real identity files yet.\nResolve the ACC-1004 double-owner source error.\nObtain independent counterparty records, security review and official Indian compliance validation.',color:C.amber,fill:C.gold,bodySize:16});
  txt(s,'No measured fraud accuracy, time savings or ROI; no automated regulatory filing.',0.79,6.46,11.78,0.38,{fontSize:15,bold:true,color:C.red});
  note(s,'The public UI was smoke-tested on 2 October after commit 0501f6a: one saved fictional case survived reload, appeared in Queue, showed its exact FTS5 chunks and calculated review, and a named escalation appeared in Compliance. This does not prove persistence through another redeploy. Do not imply tests prove fraud accuracy, business value or regulatory compliance. Original uploaded KYC files: zero. Intake saves only numeric fictional batches and generated sample documents; its runtime cases do not run the existing six-agent/Gemini pipeline. ACC-1004 has two customer owners in the source, so code withholds attribution. A real rollout needs legal/compliance ownership, data permissions, authenticated ingestion, retention, official Indian regulatory review and evaluation.');
}

// 15 — team, carefully worded
{
  const s=base('Proposed team responsibilities','14 / GROUP DISCUSSION');
  const team=[
    ['Rahul Chainani','Application development & integration'],
    ['Lakshmi','Requirements & case-study mapping'],
    ['Laxman Singh','User experience & walkthrough'],
    ['Pankaj','AI workflow & evidence review'],
    ['RS','QA & edge-case review'],
    ['Sweta Singh','Course linkage & explanation']
  ];
  team.forEach((p,i)=>{let row=Math.floor(i/3),col=i%3,x=0.72+col*4.21,y=1.72+row*2.0;box(s,x,y,3.73,1.55,C.white,C.border);circle(s,x+0.19,y+0.28,0.55,i===5?C.violet:C.blue,p[0].split(' ').map(q=>q[0]).join('').slice(0,2));txt(s,p[0],x+0.88,y+0.2,2.62,0.46,{fontSize:17,bold:true});txt(s,p[1],x+0.89,y+0.74,2.58,0.6,{fontSize:13,color:C.muted});});
  box(s,0.78,6.06,11.77,0.53,C.gold,C.amber);
  txt(s,'Proposed ownership for discussion—not a record of completed coding. Confirm names and actual work before submission.',0.99,6.17,11.3,0.28,{fontSize:12,bold:true,color:C.amber});
  note(s,'These roles are proposed, not verified completed contributions. Do not tell the evaluation panel that a person wrote code without checking commits and asking the team. Rahul is known to be a strong developer per user input, but that does not establish authorship of each module. Confirm the official group name and full roster as well.');
}

// 16 — closing code map
{
  const s=base('Eight code locations to remember','15 / PRESENTER MEMORY CUES',true);
  const rows=[
    ['INPUT','data/build_database.py','Builds fictional source rows'],
    ['INTAKE','data/fictional_intake.py','Saves gated synthetic packet + chunks'],
    ['ALERT','data/incoming_monitor.py','Calculates 24-hour review signal'],
    ['FLOW','agents/orchestrator.py','Runs six fixed stages'],
    ['RAG','data/case_evidence.py','Makes case sources and chunks'],
    ['DRAFT','agents/calculated_summary.py','Builds model-free source draft'],
    ['CHECK','agents/grounding_validator.py','Checks selected claims and IDs'],
    ['DECIDE','data/runtime_db.py','Persists human action and audit']
  ];
  rows.forEach((v,i)=>{let y=1.47+i*0.61;circle(s,0.75,y+0.07,0.4,i%2?C.blue:C.teal,String(i+1));txt(s,v[0],1.38,y,1.33,0.47,{fontSize:13,bold:true,color:'9FE4E5'});txt(s,v[1],2.77,y,4.46,0.47,{fontSize:13,bold:true,color:C.white});txt(s,v[2],7.27,y,5.3,0.47,{fontSize:12,color:'C4D6E9'});});
  txt(s,'“The rules flag. The evidence informs. The human decides.”',0.82,6.54,11.75,0.38,{fontSize:20,bold:true,color:'F7D991',align:'center'});
  note(s,'Practice the one-sentence memory cue. For “Where is the third-party alert code?” answer that incoming_monitor.py calculates a signal from supplied data, but there is no authenticated bank endpoint or durable incoming feed. For the optional numeric-only intake, show data/fictional_intake.py: it validates synthetic rows, saves an isolated packet and creates exact searchable chunks. For “Is it fraud?” answer no: the app identifies activity for review. For “Where is the evidence?” show exact transaction IDs, generated source and chunk text, and the missing-evidence flags in Evidence & RAG. For optional Gemini drafting on source cases, show agents/investigation_summary_agent.py; calculated_summary.py is the model-free route. Intake cases never enter that six-stage drafting path.');
}

const output=path.join(__dirname,'..','Product Docs','InvestigateIQ_Technical_Flow.pptx');
pptx.writeFile({fileName:output}).then(()=>console.log(output));
