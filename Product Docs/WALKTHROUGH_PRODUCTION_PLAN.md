# InvestigateIQ walkthrough production plan

Status: completed on 2026-10-09 with explicit owner approval. The replacement is a 1280×720, 8 fps H.264/AAC walkthrough assembled only from fresh current-product captures. It is 8 minutes 40 seconds long, includes WebVTT captions, uses the current reordered sidebar, and was checked at the opening plus Case Queue, Evidence & RAG, Compliance, Analytics, and Global Search sections. Admin screens are intentionally shown locked; no passcode was stored, spoken, or automated.

## Completed capture and QA record

- Fresh production capture followed the visible sidebar after workspace entry so the Streamlit session and current user state were preserved; direct route captures that reset the session were discarded.
- The sequence includes Home, Case Queue, Investigation Workspace, evidence-confidence and findings states, all six Evidence & RAG tabs, the floating Copilot, Compliance Queue, Analytics graphs, Global Search, Project & Team role responsibilities, and both locked Admin boundaries.
- Screens are native 1280×720 captures. The retired video player was excluded from the replacement; no portrait or legacy screenshot was resized into the video.
- Cursor callouts are limited to visible reviewed controls. General explanatory scenes have no cursor, so it cannot point away from the narration.
- Capture used only non-submitting interactions. It did not create an intake, submit a decision, submit a Compliance action, save rule settings, or change production audit history.

## Non-negotiable capture rules

- Capture every screen at a fixed 16:9 viewport. Never resize a portrait capture into 1280×720. If the browser viewport cannot be made 16:9, preserve the source aspect ratio on a branded background and verify the result before narration.
- Capture the same screen at its real scroll positions: top, control area, evidence/content area, and bottom. Do not stitch stretched screenshots. Use a 120–160 px/second vertical scroll, with a 0.8 second pause after each section settles.
- The pointer is semantic, not decorative. It may point only to a visible control, card, link, graph mark, dropdown, or accordion. Record its target bounding box during capture; hide the pointer when no target is visible.
- Open dropdowns for 1.5 seconds, select the intended option, then hold the resulting state for 1 second. Open accordions for 2 seconds before scrolling onward. Keep the pointer still while the narrator names the control.
- Narration drives duration. Generate the no-audio visual preview first; inspect every frame and pointer target; only then synthesize the final voice track. No live Gemini/model call is needed for this video.
- Use fictional data only. Do not submit a new case decision, create a new intake, or alter persistent audit history during capture. Use existing safe fixtures and read-only modes.

## Shot list and narration contract

Each scene below has a fixed visual target, camera move, scroll speed, pointer target, and narration purpose. The renderer must not invent extra motion.

| # | Screen / state | Scroll and camera | Pointer target | Narration (script intent) |
|---|---|---|---|---|
| 01 | Home hero and title | Static 2 s, then 80 px/s to the hero subtitle | Hero title, then the “Open the Case Queue” button | “This is InvestigateIQ, a fictional evidence-to-decision workspace. We will follow one alert from queue, through evidence and Copilot retrieval, to a human decision and Compliance review.” |
| 02 | Workspace entry | Static; no pan | Name field, role radio group, Continue | “The display name attributes actions; it is not authentication. Select Investigator to enter the review workflow.” |
| 03 | Home overview | 120 px/s from hero to workflow guide and Start here cards | Workflow step cards; each receives one short pulse | “Home explains the route and links to every page: Project & Team, Case Queue, Investigation Workspace, Compliance, Analytics, Search, Evidence & RAG, and both Admin pages.” |
| 04 | Case Queue top | 140 px/s through the page guide into KPI cards | Total, Open, Escalated, Source closed, High severity cards and each info icon | “The queue counts orient work. Status and severity are labels, not proof of wrongdoing. The definitions explain source-closed versus a recorded human close.” |
| 05 | Case Queue filters | Pause, open each dropdown for 1.5 s, then close; 120 px/s to the search field | Severity, Status, Scenario dropdowns; customer search placeholder | “These controls filter the fictional alert cards. Search matches customer names; it is not a transaction or external-person search.” |
| 06 | Case Queue card rows | 130 px/s down two cards; pause on an Evidence action and Open case | Case ID, status badge, Evidence, Open case | “A completed or Compliance-reviewed case exposes evidence separately. The action label describes the next screen; it must not contradict a completed decision.” |
| 07 | Investigation Workspace setup | Static top, then 100 px/s to case selector/mode | Case combobox, saved/calculated/AI mode radios, Run investigation | “Choose Case zero four one and the saved report for a repeatable review. Saved mode is historical; calculated mode reads current stored records; AI mode is optional.” |
| 08 | Workspace case context | 140 px/s across the case heading and metrics | Customer heading, baseline amount, trigger ratio, transaction count, prior cases | “Coastal Wholesale Traders has six review-window credits, a ₹395,000 baseline, a 2.5× trigger ratio, and no prior cases in this dataset. These are facts to check, not a verdict.” |
| 09 | Evidence & Findings | 120 px/s through saved evidence, current index, and finding cards | Saved snapshot warning, current-index count, RED_FLAG, MISSING | “The historical report and current index are intentionally separate. Four cash deposits are cited; the missing business explanation is a follow-up question, not proof of improper purpose.” |
| 10 | Evidence links and RAG guidance | 120 px/s to recommended steps; pause on each source link | PB-AML-STR-01 and PB-AML-STR-02 source buttons | “The recommendation cites a playbook. A citation tells the investigator where to read; it does not verify every generated sentence.” |
| 11 | Floating InvestigateIQ Copilot | Open launcher; panel opens; no page jump | Ask InvestigateIQ launcher, suggested-question picker, message field, Send | “There is one Copilot entry point. Select a long suggested question, show the full text, then press Send. The transcript stays above the composer.” |
| 12 | Copilot answer and provenance | Scroll the panel transcript at 90 px/s; pause on latest answer | Latest answer, case ID, cited transaction/source links | “The answer is bounded by stored rows and exact chunks. The latest response is highlighted and its evidence links are inspectable.” |
| 13 | Evidence & RAG — Case records | Switch to Case records; open one exact chunk accordion | Case record tab, chunk accordion, source ID and status | “Case records show the exact stored passage and its scope. Source rows are fictional and incomplete; they are not independent KYC or source-of-funds proof.” |
| 14 | Evidence & RAG — Rule Lab | Open Rule Lab; expand the rule explanation | Rule Lab tab, threshold explanation, rule card | “The Rule Lab explains a calculated review signal. It is a review aid, not an automatic finding of fraud.” |
| 15 | Evidence & RAG — Fictional Intake | Open Fictional Intake; show fields without submitting | Baseline, incoming, outgoing fields and calculation preview | “A separate fixture can create a ten-row fictional packet. The video will show the inputs and evidence boundary but will not create another persistent case.” |
| 16 | Evidence & RAG — Source & chunks | Select the document picker; expand metadata and body chunks | Document selector, source title, C0/C1/C2 accordions | “A playbook is stored as an Open Knowledge Format source, then split into a metadata chunk and two-sentence body chunks.” |
| 17 | Evidence & RAG — Search the index | Enter the safe query; wait for results; scroll 100 px/s | Search field, BM25 score, result source/chunk link | “SQLite FTS5 performs lexical matching and BM25 ranks the chunks. This is keyword retrieval, not a vector database.” |
| 18 | Evidence & RAG — Method & code | Open each of the eight code accordions one at a time | Each accordion header; pause 2 s per panel | “The Method and code panels show alert calculation, chunking, search, transaction links, context gathering, and citation checks. The validator checks selected claims, not full factual truth.” |
| 19 | Human Decision | 120 px/s to the decision card; pause on each radio option | Investigator name, three decision radios, rationale, Submit button | “Only the named investigator chooses Close, Request more information, or Escalate. The rationale is required. The Copilot cannot submit a decision.” |
| 20 | Read-only recorded decision | Scroll to the stored-action state | Recorded choice, investigator, rationale, timestamp; disabled controls | “After submission, the selected decision is shown and the form is locked. The audit record is append-only; it is not an editable chat setting.” |
| 21 | Compliance Queue | Navigate; scroll 130 px/s through queue and action panel | Escalation card, action radios, rationale, Submit compliance action | “Compliance is a separate human review. Acknowledge means no further action; Return requests more information; Refer records an onward referral and does not file anything.” |
| 22 | Compliance outcome labels | Show each safe fixture outcome or explanatory state card | Outcome badge and Case Queue mapping | “These outcome labels are visible on the queue and audit trail, so users can distinguish returned, acknowledged, and referred cases.” |
| 23 | Analytics overview | 100 px/s between graphs; pause 1.5 s per chart | Chart title, x-axis, y-axis, tooltip icon | “Analytics is descriptive only. We will name each unit rather than imply a risk verdict.” |
| 24 | Analytics graph explanations | Static chart-by-chart holds | Severity, typology, current status, high-severity share, monthly records, human actions | “Severity counts labels; typology counts categories; status counts workflow states; high-share is a proportion, not crime probability; monthly records are fictional dates; human-action bars count saved events, not productivity or outcomes.” |
| 25 | Global Search | Enter a customer query; wait; open one result | Search field, result type, open-context link | “Global Search finds fictional customers, accounts, cases, and transactions. It is a pointer to context, not a conclusion.” |
| 26 | Project & Team | 120 px/s through roster, then open role-responsibility section | Team names, role cards, responsibility accordion | “The four roles are Investigator, Team Lead, Compliance Officer, and Admin. Names are shown without email addresses; role labels are workflow responsibilities, not authentication.” |
| 27 | Admin Knowledge Base locked | Static; passcode field remains masked | Passcode field, Unlock, help tooltip | “The passcode is a limited demo gate. It is never spoken or displayed in the recording.” |
| 28 | Admin Knowledge Base unlocked | 120 px/s through metrics, source list, chunks, and search | Document count, chunk count, vocabulary metric, source/chunk search | “The Admin page exposes the 24 playbooks, 57 chunks, indexed vocabulary, source-to-chunk map, and live retrieval query.” |
| 29 | Admin Rule Config | Unlock; scroll through sliders and read-only preview | Threshold controls, preview counts, no-save boundary | “Rule settings are saved examples. Preview checks fictional accounts without changing existing alerts; no threshold is saved in this recording.” |
| 30 | Closing scope | Slow 80 px/s to the final disclaimer, then static 3 s | Evidence boundary, human-decision statement, no-filing statement | “InvestigateIQ makes evidence easier to inspect and questions easier to ask. It does not prove lawfulness, replace human judgment, authenticate original documents, or file with a regulator.” |

## Timing and pointer QA

- Target final length: 18–22 minutes, with scene duration generated from the narration track plus a 0.15 second buffer.
- Section transitions: 0.35 second cross-fade; no rapid cuts during a dropdown, accordion, graph tooltip, or decision explanation.
- Scroll speed: 120 px/s for normal pages, 90 px/s inside the Copilot transcript, 80 px/s for the Home hero and closing disclaimer. Pause 0.8 seconds after every scroll stop.
- Pointer speed: 180 px/s maximum, ease-in/ease-out, 1.0 second hold on the target, blue ring only when the target is visible. No pointer on blank margins or over text that is not being discussed.
- Before final narration, render a silent low-resolution preview and inspect: no aspect-ratio distortion, no retired split Copilot screen, no pointer outside the target, no clipped dropdown/accordion, no unreadable graph axis, and no persistent mutation.
- After approval, render the final H.264/AAC MP4 and WebVTT, decode the full file, sample the start of every section, verify the title/duration, then atomically replace the production asset and deploy.

## Release gate

The owner approved replacement. The new MP4, poster, and captions may now be committed and deployed after the repository release checks pass.
