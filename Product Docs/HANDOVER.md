# InvestigateIQ — Handover Document

## Current local work — 30 September 2026

- 20:01 ET pre-batch safety review: `git status` shows only expected app/docs/test changes; untracked files are the three course/evidence notes and six Python tests. No tracked demo database, workbook, source course PDF, key file, or generated runtime DB appears in the changed list. A filename-only high-risk key-pattern scan found no matches in text sources. `python -m unittest discover -s tests -q` passed 27 tests, `git diff --check` passed with Windows line-ending warnings only, and the offline injection probe passed. Do not turn these checks into a claim of full security or live-model validation.
- End-to-end cached rehearsal (20:00 ET) used Streamlit AppTest and a temporary runtime DB: CASE-001 was replayed, escalated with a rationale, appeared as one high-severity case in Compliance Queue, then received a Compliance acknowledgment with its own rationale. The temporary database contained two human-action rows and two matching human audit events; the Compliance queue returned to zero. Both screens had zero app exceptions. No real demo decision/audit history was changed. This verifies the local cached human handoff, not the live Gemini path or a public browser deployment.
- Pre-batch CI-style data check ran `data.build_database.main()` against a temporary database, not tracked `data/investigateiq.db`: 552 customers, 654 accounts, 9,950 transactions, 42 alerts, 24 playbooks, and 57 chunks rebuilt successfully. Both hero cases are present, every alert scenario has playbook coverage, and an FTS5 `source of funds` query found six matches. No dataset file was overwritten. The old acceptance-criteria file is now explicitly labelled target-state, not a completed pass report.
- The report and chat prompts now explicitly say when the alert has no identified trigger transaction and prohibit inferring a ratio from another transaction. The UI/PDF label is “Trigger/baseline ratio,” not an unexplained “Deviation ratio.” The validator additionally requires the trigger ID to appear in the supplied in-window evidence before accepting numeric `Nx` wording. Regression suite: 27 passing tests; `git diff --check` passes (only Windows LF/CRLF notices). No live Gemini call or tracked database rebuild occurred.
- Trigger-provenance correction (hourly continuation): the transaction agent now computes `deviation_ratio` only from an alert's recorded, in-window `trigger_transaction_id`, never from the first convenient transaction. Cached replay recomputes from that ID or clears an unsupported stored ratio without rewriting cached JSON. The validator withholds unanchored or mismatched `Nx` wording and marks the draft for review. Five cached cases now replay as CASE-001/002/041 `PASS`, CASE-003/006 `REVIEW_REQUIRED`; CASE-003's former `0.9x` is not displayed as verified. CASE-003 UI AppTest had zero exceptions and showed the ratio as unavailable. New isolated SQLite tests brought the suite to 26 passing checks. This is a provenance safeguard, not full trigger-rule verification.
- Human Decision section now uses a real keyed Streamlit container with a distinct green border/background rather than a raw HTML tag pair that might not wrap Streamlit widgets. Cached-case AppTest still shows the header and submit button with zero exceptions; 21 tests still pass. Visual color rendering on the public app remains to be checked after deployment.
- Rule-preview time arithmetic fix: outbound debit timestamps are normalized with SQLite `datetime()` on both sides of the comparison, so same-day ISO `T` timestamps are counted correctly in short windows. Three in-memory SQLite regression tests cover R1 baseline, same-day R2 proxy timing, and the two-debit minimum; 21 tests now pass. Read-only Admin AppTest still renders with zero exceptions and shows 300 accounts checked, 2 R1 matches, 0 R1-plus-proxy matches under default thresholds. This remains an illustrative proxy, not two-hop trace proof.
- Admin rule saves now use `set_rule_params` so all moved thresholds and their audit entries commit or roll back together. The page reports a failed batch instead of crashing or leaving partial settings. New tests simulate failure on the second audit insert and verify full rollback; the suite now has 18 passing tests. No actual threshold was changed during verification.
- Read-only AppTest follow-up: Case Queue rendered with zero exceptions and five `CACHED` badges. Admin Rule Config rendered and its default-threshold preview ran with zero exceptions: 300 accounts checked, 2 matching the simple R1 condition, 0 matching R1 plus the outbound proxy. These are synthetic sensitivity-preview counts, not validated alerts or a performance result. The preview was not saved; only a temporary runtime database was used.
- A second prompt-entry path was corrected: chat now uses the same narrow transaction-reference filtering as report drafting and records withheld transaction IDs in its chat-answer audit details. An offline test confirms the injected text does not reach the chat prompt. Read-only recomputation found 24 of the current 42 alert review windows empty (not 24 of 41). The test suite is now 16 passing checks. No claim of comprehensive prompt-injection defense, full alert reconstruction, or Indian regulatory certification follows from these checks.
- `python scripts/test_prompt_injection.py --offline` now exercises the existing synthetic injected transaction without Gemini or runtime-audit writes. It confirms TXN-19869 remains identifiable while the instruction-like reference is withheld from the prompt. The optional live probe remains unrun in this batch and would need credentials/network; offline PASS is not a model-resistance claim.
- UI smoke check with a temporary runtime database: the investigation page loaded all 42 case choices and replayed CASE-001 without exceptions. CASE-006 replay also had zero app exceptions and correctly showed `REVIEW_REQUIRED`, the missing trigger-ID warning, and `Nearby transactions (context only): 5` rather than mislabeling them in-window. The orchestration audit regression test now checks that a flagged transaction ID produces `untrusted_transaction_reference_withheld` without storing the instruction text. Current suite: 15 passing tests; `git diff --check` passes. The UI check used Streamlit AppTest, not a public deployment or live Gemini call.
- Read-only source-data audit found 38 of 42 alerts lack `trigger_transaction_id` (the two main demo cases do have one). The investigation screen and PDF now identify recorded rule labels as source metadata, warn when the trigger ID is absent, and avoid implying that the app independently reproduced every alert. This is a dataset/provenance limitation, not something to silently repair by inventing IDs.
- Prompt boundary follow-up: the live summary prompt now withholds reference_text that matches narrow instruction-like patterns while leaving the original transaction visible to the human; the orchestrator logs flagged transaction IDs as an audit event, not the malicious text. The actual synthetic injected transaction TXN-19869 is flagged in a read-only check. Offline tests cover redaction, original-evidence preservation, and the audit event. This does **not** establish general prompt-injection immunity or prove a live model resisted every attempt. All five cached cases also pass offline replay/PDF export; CASE-006 remains REVIEW_REQUIRED under the stricter evidence-window check.
- Latest local correctness pass: the investigation screen now labels nearest background transactions as context rather than transactions inside an empty alert window. The admin rule preview now says explicitly that two same-account debits are only an outbound-activity proxy, not proof of two linked transfer hops or an automatically created alert. Queue cache badges reflect all available cached reports; the PDF validator section no longer calls a selected-check pass "no corrections needed." The dataset README counts now match the tracked SQLite database (552 customers, 654 accounts, 9,950 transactions, 42 alerts, 24 playbooks). Eleven unit tests still pass. No commit/deploy yet; keep the 9 p.m. ET batch.
- User preference clarified: do not keep creating separate documents or give the user a large reading assignment. The user's single short entry point is the “Read this first — the five-minute version” section at the top of `15-Course-Concept-Application-Map.md`. `16` and `17` are internal evidence/verification notes; maintain them only if a specific claim needs proof. The app's 24 synthetic playbooks are its existing retrieval knowledge base, not extra course-reading for the user.
- User subsequently authorized application improvements and completion of the to-do list without waiting for Saturday. First correctness change: `data/runtime_db.py` now saves a human decision and its audit event in one SQLite transaction. New `tests/test_runtime_db.py` checks success, required rationale, and rollback if the audit insert fails; all three pass. README stale status/counts were corrected. This does **not** make the audit log immutable or the mock identity production-grade.
- Second correctness change: `agents/grounding_validator.py` now removes specified verdict-like wording across displayed report fields, downgrades a Verified finding with a mismatched ratio, and uses `REVIEW_REQUIRED` instead of the misleading `PASS_WITH_CORRECTIONS` when notes exist. `agents/chat_agent.py` applies the same wording guardrail; cached reports are revalidated on replay in `pages/2_Investigation_Demo.py`. Added `tests/test_grounding_validator.py` and `tests/test_chat_agent.py`; all eight local unit tests pass. These are bounded checks, not proof of factual correctness or Indian regulatory compliance.
- CI now runs the unit-test suite after the existing data/FTS sanity check. All five cached reports passed the revised validator without notes, and logged-in home AppTest had zero exceptions. `.streamlit/config.toml` was changed from `enableCORS = false` to `true` based on Streamlit's official configuration guidance and the runtime warning; local AppTest no longer emits the CORS warning. Confirm the public Railway app still works after the 9 p.m. deployment before claiming this security configuration is settled. The unrelated `st.components.v1.html` deprecation warning remains.
- Follow-up edge-case correction: when a case has no transaction inside the alert review window, the nearby transactions shown as background can no longer support a `Verified` finding. `tests/test_grounding_validator.py` covers this. Revalidating existing cached reports now yields four `PASS` and one `REVIEW_REQUIRED` (CASE-006); the cached JSON files were **not** rewritten, but replay runs the current validator. Nine unit tests pass. The earlier “all five pass” note above records the check before this stricter rule.
- Admin rule changes now save their config row and audit event atomically as well; two more regression tests cover success and rollback on simulated audit failure. Eleven unit tests pass. `README.md` now has Windows PowerShell-friendly local run instructions and current 42-alert/24-playbook status; no source workbook or tracked database rebuild was performed.
- The shared `page_banner` now adds “Prototype · all customer and transaction data is fictional” to all seven operational pages; an admin subtitle was corrected from “real effect” to “illustrative effect.” Isolated AppTest runs showed zero exceptions and the fictional-data caption on all seven pages. `pages/home.py` cannot be tested as a standalone page because its `st.page_link` requires the `app.py` navigation router; it previously passed when run through that router. Tests used a temporary runtime DB, not the user's decision/audit file.
- User preference: save work locally and batch GitHub commits / Railway deployments at 9:00 p.m. New York time daily. A thread heartbeat has been scheduled for that review. Do not commit or deploy after each small task.
- Current priority: map supplied IIT Bombay course modules and case studies to what InvestigateIQ actually implements. The first research pass is saved in `15-Course-Concept-Application-Map.md` and `16-Course-Source-Evidence-Register.md`. The register records page anchors, specific case-study analogies, exact repository proof, remaining gaps, and a file-by-file inventory of all 40 top-level supplied items with honest review-depth labels. Continue deeper source review if a slide or viva answer needs a specific claim.
- A repository-file audit is now saved in `17-Repository-File-Audit.md`: 106 visible files classified by exact role, current/historical status, capstone value and gap. It identifies the older Sentinel/29 September materials as history rather than current proof. No files were deleted or moved.
- All six existing PNG diagrams were visually reviewed. Diagrams `1-workflow-flowchart.png`, `2-architecture-diagram.png`, and `5-rag-okf-pipeline.png` conflict with current code: they show respectively every-finding validation/immutable audit, old agent/tool-call architecture, and a vector index/embeddings. Do not use these as implementation proof in the final presentation until corrected; the exact caveats are in `17-Repository-File-Audit.md`. Diagram 4's team roles need Saturday confirmation. No image was modified in this research phase.
- Presenter-material check: the old CEO Playbook `.docx` contains material inaccuracies for the current code (every-claim citations, vector retrieval, immutable audit, Compliance screen “document only”). The 13-page `InvestigateIQ - GIT.pdf` is best treated as a concept deck: “faster” is not measured and its ₹8M case is illustrative. Exact caveats are in `17-Repository-File-Audit.md`; neither file was edited or copied during this audit.
- Documentation safety labels added to the two Mermaid flowcharts, the merged `Sentinel-AML-Document.md`, the old index, and `BUILD-STATUS.md`. These remain historical/target-state source files; only top-of-file caveats were added, not broad rewrites. This prevents old “immutable,” automatic monitoring, and request/response-loop claims from being mistaken for implemented features.
- Audit integrity check: all 107 currently visible project-file names (including the new inventory itself) appear in `17-Repository-File-Audit.md`; its 30 Python and 26 non-playbook Markdown entries were counted. Local links checked in the new research documents and caveated historical docs; no broken local links found. `git diff --check` passed. No commit, push, or deployment has been performed in this local research phase.
- Hourly progress heartbeat is active for this thread. Each update should report current work, remaining scope, realistic completion estimate, and next task. This is separate from the 9 p.m. New York batch review/commit/deploy heartbeat.
- Provisional academic identity: **Capstone Group 7** is now shown in the app sidebar, home footer, and README. Do not add individual member names or assign contributions until the user confirms the official group name and team decisions.
- The source corpus is in `C:\D\IIT Mumbai`. Course materials are outside the Git repository; cite their filenames and page numbers in derived notes, and do not copy the licensed PDFs into GitHub.
- Important analytical correction: the software's six specialist classes run in a fixed sequence. Describe them as specialist components coordinated by an orchestrator; do not claim six independently planning LLM agents. The course's agentic-fit distinction is on Module 2 Session 4, PDF p. 17.
- Accuracy cleanup in this local batch: the home page and validator docstring no longer claim that every generated sentence is checked. `BUILD-STATUS.md` remains a historical build report with older dataset counts (for example 41 alerts versus 42 in the current local database); refresh its snapshot later rather than treating it as the current count source.
- Current code cross-check: retrieval is FTS5/BM25 keyword search in `data/knowledge_search.py`, six specialist stages run sequentially in `agents/orchestrator.py`, and Gemini is called for the summary. The validator flags some issues without removing the wording and cannot prove a cited record supports the exact prose; its `PASS_WITH_CORRECTIONS` label should not be described as a clean pass. Human decisions require rationale, but the human-action row and audit event are separate commits, not an atomic transaction. These limits are recorded in the source evidence register; do not overclaim them in the presentation.
- Demo wording audit: the Investigation Demo now shows validator notes as a warning and says that selected checks found no issue only when there are no notes. The home, case queue, and admin-rule descriptions now call the dataset fictional and describe the pipeline as six fixed steps. These are explanation/label fixes, not a change to the underlying investigation logic; Python syntax and `git diff --check` passed locally. A small direct validator behavior check passed for a clean report and for invented IDs/forbidden wording; a visual/live UI smoke test has not yet been performed.
- Course-map speaking answers were aligned with those checks: the financial-crime PDF is labelled a sample blueprint, retrieved guidance is labelled synthetic, and the validator is described as checking selected citations/claims rather than establishing full truth. Keep these caveats when drafting the final presentation.
- Local Streamlit smoke check (AppTest, logged-out and logged-in home): zero app exceptions; the provisional group label appeared in the sidebar. Runtime warnings remain: `.streamlit/config.toml` sets `enableCORS = false` while XSRF is enabled, and Streamlit reports older UI APIs (`use_container_width`, `st.components.v1.html`) as deprecated. These are existing configuration/maintenance gaps, not evidence that the prototype is production-secure. No public deployment test was run in this pass.
- Pre-batch check: `data/investigateiq.db` is tracked by Git. `scripts/ci_check.py` rebuilds that file, so it was intentionally not run during the local preflight. Read-only checks confirmed all five current alert scenarios have knowledge-base coverage and FTS retrieval returns guidance. The home tagline now accurately says AI drafts the *report*, not the underlying evidence. Before any 9 p.m. commit, inspect the exact staged file list and avoid including rebuilt database churn unless deliberately intended.
- Source spot-check: read-only page checks confirmed the key anchors in DBS (`DBS' AI Journey.pdf`, PDF pp. 4, 6, 11–12), the agentic-fit distinction (Module 2 Session 4, p. 17), the financial-crime sample blueprint (pp. 1–5), Erica (pp. 4, 8, 12), BMW (pp. 7–9), and the HBR anthology's employee-autonomy, handoff, and deep-and-narrow passages (pp. 18–20, 90, 162–164). The available Adobe PDF skill was consulted, but its Acrobat tools are not connected here, so a local text-only reader was used for these narrow checks. No source PDF was copied into the repository.
- No real-user baseline, regulatory validation, or bank integration has been performed. Technical operation and synthetic demo results are the current evidence; measured business outcomes remain future work.
- The current repository HEAD at the start of this work was `3ad2ef9` (29 September 2026). The older handover snapshot below describes an earlier release and is retained for historical context; its "latest commit" and "clean status" lines are no longer current.

---

**As of:** 29 September 2026
**Live app:** https://investigateiq-app-production.up.railway.app/
**Repo:** https://github.com/swetadminc/CapstoneProject (branch: `main`)
**Latest commit:** `e2b6251` — "Add product logo, branded top banner, and colorful KPI icons"

**Purpose of this file:** a fast-start briefing for whoever (human or another Claude session) picks this up
next. Read this before `Product Docs/BUILD-STATUS.md` — that file is the full feature-by-feature record;
this one is "what's live, what's mid-flight, and exactly where to pick up."

---

## 1. Everything is safely committed and pushed

`git status` is clean. Every change described below is on `main` on GitHub, commit `e2b6251`. **Nothing is
sitting uncommitted on disk.**

## 2. Deployment note

Railway's build queue was running unusually slowly for stretches of the session that produced this batch of
fixes (deploys that normally take 1–2 minutes sometimes took 5–10+ minutes, stuck in
"Queued"/"Initializing"/"Building"). This is platform-side queue congestion, not a code problem — production
stayed live and serving the previous good version throughout every single deploy (verified repeatedly with
`curl` returning 200). If a fresh push looks slow to land, that's consistent with the same pattern — let it
finish, or trigger a fresh deploy from the Railway dashboard only if it looks truly stuck (not just slow).

## 3. The full UI/UX feedback batch — all five items now done

A detailed round of feedback (with a screenshot) came in mid-session. All five items are now implemented,
tested live in the browser (both themes, and mobile viewport for the responsiveness item), and pushed:

### 3a. KPI tile coloring — done
Each KPI tile (`Total alerts`/`Open`/`High severity`/`Escalated`/`Closed`) now has a distinct colored left
border (`iq-kpi-blue`/`iq-kpi-amber`/`iq-kpi-red`/`iq-kpi-green` classes in `ui_common.py`), reusing the
existing severity/status color tokens so it's correct in both themes without a new palette. Applied on both
`pages/home.py` and `pages/0_Case_Queue.py`.

### 3b. Two dark-mode contrast bugs — done
- Text input `::placeholder` color (was inheriting an unreadable browser default) — fixed in
  `_DARK_OVERRIDE_CSS` in `ui_common.py`.
- Bordered containers (`st.container(border=True)` — findings cards, the "Ask the Copilot" chat panel, the
  compliance escalation cards) were keeping a light background while the blanket text-color override forced
  their text light too, making it invisible. Fixed by giving
  `[data-testid="stVerticalBlockBorderWrapper"]`, `[data-testid="stChatMessage"]`, `[data-testid="stChatInput"]`
  an explicit dark background in the dark override CSS.
- Also found and fixed proactively, same bug shape: `st.selectbox`/`st.multiselect` (this Streamlit version
  renders them via `.react-aria-ComboBox`, not the older `data-baseweb="select"` markup — confirmed via live
  DOM inspection), `st.code()`'s `<pre>` wrapper, and `st.json()`'s `react-json-view` background.

### 3c. Mobile responsiveness — done
The Case Queue table's 7-column `st.columns()` row stacks vertically below ~640px with no way to tell what a
stacked value means. Fixed with a CSS-only approach: the header row hides at that breakpoint
(`[data-testid="stHorizontalBlock"]:has(.iq-queue-header) { display: none; }`), and each data cell gets an
inline `<span class="iq-mobile-label">Label: </span>` prefix that's `display:none` on desktop (redundant next
to the real header) and `display:inline` only under the same media query. Verified live at 375×812 — see
`pages/0_Case_Queue.py` (the queue-table loop) and the mobile CSS block in `ui_common.py`.

### 3d. Tooltips / contextual help — done
Added `help=` text (and, for the two decision-recording radio buttons, `captions=` per option) throughout:
Admin Rule Config's passcode field, threshold metrics, preview/save buttons; the Investigation Workspace
Human Decision radio, investigator name field, rationale field, submit button; the Compliance Queue action
radio, officer name field, rationale field, submit button.

### 3e. Product logo + branded top banner + KPI icons — done
No logo existed anywhere in the repo before this. OpenArt's image-generation credit balance is 0 (checked via
`openart_model_list` — every model shows `"affordable": false`), so a generated PNG wasn't available. Built
instead as hand-authored SVG (sharper at any size, no regeneration needed, zero cost):
- `assets/logo_icon.svg` — shield (compliance) + magnifying glass (investigate) mark, used as the collapsed
  sidebar icon.
- `assets/logo_full.svg` / `assets/logo_full_dark.svg` — full lockup with "InvestigateIQ" wordmark, light/dark
  variants (the dark variant uses light text — a single shared file would've gone invisible against the dark
  navy sidebar).
- Wired in via `st.logo()` inside `require_login()` in `ui_common.py` — gives every page a real top banner in
  the sidebar, theme-aware (picks the variant based on `session_state["dark_mode_toggle"]`).
- The login screen (previously a bare `### 👤 Who's using...` heading — the "page looks quite blank" feedback)
  now leads with the full logo image and wraps the form in a bordered card.
- Small colored icon badges (`.iq-kpi-icon` — 📊/🕒/🔥/🚨/✅) added to every KPI tile on Home and Case Queue,
  reusing the same severity/status CSS variables so they're correct in dark mode automatically.

**If real image-generation budget becomes available later:** the SVGs at `assets/logo_*.svg` are the natural
thing to replace with a generated PNG/vector if a more illustrated/branded mark is wanted — the wiring
(`st.logo()` call, login-screen `st.image()`, all class names) doesn't need to change, just the file contents.

## 4. What's NOT in this feedback batch (untouched, no known issues)

Everything from the prior handover's "live and working" list is still live: multi-agent investigation
pipeline (6 specialists + Grounding Validator), Analytics, PDF export, Global Search, the animated landing
page hero, `st.navigation()`-based sidebar routing, the radiant light-mode background.

## 5. Operational notes / gotchas for whoever continues

- **Local testing pattern:** kill any stale `streamlit run` process on the port you're about to reuse before
  starting a new one — `netstat -ano | grep ":<port>" | grep LISTENING` then `taskkill //F //PID <pid>`.
  Always `rm -f data/investigateiq_runtime.db` before a fresh local run so you're not reading stale local
  state. Use `--server.fileWatcherType=none` to avoid a hot-reload edge case, but remember that means **you
  must fully restart the process** after editing any `.py` file — hot reload won't pick it up.
- **Streamlit version is 1.64.0** — `st.logo()` supports SVG directly (confirmed working, no PNG conversion
  needed).
- **OpenArt image-generation MCP tool has a $0 credit balance** as of this session (`openart_model_list`
  reports every model `"affordable": false`) — don't assume it's usable without checking again first.
- **All data in this project is fictional** — this constraint has been strictly maintained throughout and
  must continue to be.
- Cached reports only exist for 5 of the 42 cases (one per typology: CASE-001, CASE-002, CASE-003, CASE-006,
  CASE-041). Any other case selected in "Cached" mode on Investigation Demo falls back to a live Gemini call.

## 6. Reference

- **Admin passcode** (Knowledge Base / Rule Config pages): `IQ-Demo-2026`
- **Full build history:** `Product Docs/BUILD-STATUS.md`
- **Original requirements pack:** `Product Docs/Sentinel-AML-Document.md` and the numbered `Product Docs/0X-*.md`
  files
