# InvestigateIQ — Handover Document

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
