# InvestigateIQ — Handover Document

**As of:** 29 September 2026, end of session (session ended on approaching usage limits)
**Live app:** https://investigateiq-app-production.up.railway.app/
**Repo:** https://github.com/swetadminc/CapstoneProject (branch: `main`)
**Latest commit:** `3f8487f` — "Fix truncated 'Investigate ->' buttons — icon + real tooltip instead"

**Purpose of this file:** a fast-start briefing for whoever (human or another Claude session) picks this up
next. Read this before `Product Docs/BUILD-STATUS.md` — that file is the full feature-by-feature record;
this one is "what's live, what's mid-flight, and exactly where to pick up."

---

## 1. Everything is safely committed and pushed

`git status` is clean. Every change described in `BUILD-STATUS.md` and everything built this session
(multi-agent split, Analytics, PDF export, Global Search, dark mode, the animated landing page, the
sidebar-navigation fix, the radiant light-mode background, the truncated-button fix) is on `main` on GitHub,
commit `3f8487f`. **Nothing is sitting uncommitted on disk.**

## 2. Deployment note — read this before assuming something is broken

Railway's build queue was running unusually slowly for the last ~30 minutes of this session (deploys that
normally take 1–2 minutes were taking 5–10+ minutes, stuck in "Queued"/"Initializing"/"Building" states one
after another). This happened consistently across multiple separate deploys, including ones that succeeded
in the end — it's platform-side queue congestion, not a code problem. **Production was live and serving the
previous good version the entire time** (verified repeatedly with `curl` returning 200), so there was no
downtime at any point.

**First thing to do in the next session:** run `railway status` (or check the Railway dashboard) to see
whether commit `3f8487f` finished deploying. If it's still not live, there is nothing wrong with the code —
just let it finish, or trigger a fresh deploy from the Railway dashboard if it looks truly stuck (not just
slow).

## 3. What's live and working (verified this session, not just built)

Everything in `Product Docs/BUILD-STATUS.md`'s "built and verified live" table, plus, added at the very end
of this session:
- **Sidebar navigation fixed** — migrated to `st.navigation()` so every page gets a real title/icon instead
  of Streamlit deriving the entry page's label from the literal filename (`app.py` → "app", lowercase, ugly).
  `app.py` is now a pure router; the actual landing page content moved to `pages/home.py`.
- **Real animated landing page** (`pages/home.py`) — a hero with a drifting particle-network canvas
  (`st.components.v1.html`), staggered fade-up text, a working CTA button into Case Queue (note: had to move
  the CTA *outside* the iframe — Streamlit's `components.html` sandbox blocks `target="_top"` navigation from
  inside it), and cascading KPI/nav cards below.
- **Dark mode toggle fixed for real** — there was a genuine one-click-behind bug (toggle looked delayed by
  one click). Root cause: `inject_global_styles()` was reading a separately-tracked `session_state["dark_mode"]`
  key that only got its fresh value from a line of code *later* in the same script run. Fixed by reading the
  toggle widget's own key (`dark_mode_toggle`) directly — Streamlit updates a widget's own key before the
  script starts running, so there's no lag. See `ui_common.py`, `inject_global_styles()` and the toggle in
  `require_login()`.
- **Light mode background** — no longer flat white; two soft radial blue glows (upper-left/upper-right) on a
  pale blue base, matching the deliberate navy of dark mode. See `.streamlit/config.toml` and the `:root`
  section of `_GLOBAL_CSS` in `ui_common.py`.
- **Truncated "Investigate →" buttons fixed** — the label didn't fit its column at most viewport widths and
  silently truncated to "I..". Replaced with a 🔍 icon + Streamlit's real `help=` tooltip (shows
  "Investigate CASE-XXX" on hover) on both Case Queue and Global Search.

## 4. Pending — a large batch of UI/UX feedback just received, NOT yet started

The user sent detailed feedback (with a screenshot) right as this session was ending. **No code changes have
been made for any of this yet** — it's all still to do. Listed in the order it was raised, with concrete
starting points so the next session doesn't have to re-diagnose from scratch:

### 4a. KPI tile coloring
On the Home page and Case Queue page, the KPI cards (Total Alerts, Open, High Severity, Escalated, Closed)
all currently render identically (`.iq-card` class, same background/border for every tile, in both light and
dark mode). Requested: distinct color per tile that means something — e.g. Open in a warning color, High
Severity/Escalated in red, Total in neutral/blue, Closed in green. Should work in both themes.
- **Where:** `.iq-card` / `.iq-kpi-value` in `ui_common.py`; the KPI-rendering loops in `pages/home.py` and
  `pages/0_Case_Queue.py` (search for `iq-kpi-label`). Easiest approach: add per-metric class names
  (`iq-kpi-open`, `iq-kpi-high`, etc.) reusing the existing `--iq-sev-*`/`--iq-status-*` color variables
  already defined in `ui_common.py`, rather than inventing a new palette.

### 4b. Login screen ("Who's using InvestigateIQ?") feels blank; wants a logo
User specifically said this screen "looks quite blank" next to the new radiant background elsewhere, and
separately asked for **a real logo — "an innovative one," as a PNG** — plus a top banner showing it. There is
currently no logo asset in the repo at all (`🔎` emoji is used as a stand-in icon everywhere). This needs:
1. An actual logo image generated/sourced (the `openart_generate_image` MCP tool was available this session
   if it still is — deferred tool, needs `ToolSearch "select:openart_generate_image"` or similar first).
2. The login form in `ui_common.py`'s `require_login()` (currently just `st.markdown("### 👤 Who's using...")`)
   redesigned to feel like part of the branded app, not a bare form — likely wrapped in an `.iq-card`, with the
   logo above it.
3. The logo also referenced from `page_banner()` (used at the top of every page) and possibly the hero on
   `pages/home.py`.
- Also requested: "colorful, small PNG icons" on the KPI tiles themselves (Total Alerts / Open specifically
  named), not just emoji.

### 4c. Two more dark-mode contrast bugs (real, not yet fixed)
- **"Search customer name" placeholder text is not visible in dark mode.** Confirmed location:
  `pages/0_Case_Queue.py:101`, `st.text_input("Search customer name", placeholder="e.g. Apex")`. The dark
  override CSS in `ui_common.py` sets the *typed* text color (`[data-testid="stTextInput"] input { color:
  #E8EDF7 !important; }`) but never touches the `::placeholder` pseudo-element, which likely keeps a
  medium-gray default that has poor contrast against the dark navy input background. **Fix:** add an explicit
  `::placeholder { color: ...; }` rule inside `_DARK_OVERRIDE_CSS` in `ui_common.py`.
- **"Right-side panel text is not visible in dark mode."** This was being actively investigated when the
  session ended — working hypothesis, not yet confirmed or fixed: **every bordered `st.container(border=True)`
  probably keeps its own light/white background in dark mode**, because the dark override CSS never gives
  `[data-testid="stVerticalBlockBorderWrapper"]` a dark `background-color` (it only adds a hover
  transform/shadow to it — see the `.iq-card, [data-testid="stVerticalBlockBorderWrapper"] { transition: ...
  }` rule near the bottom of `ui_common.py`). Meanwhile the blanket `[data-testid="stAppViewContainer"] *
  { color: #E8EDF7 !important; }` rule forces the *text inside* those containers to light gray regardless —
  so light text on a still-white/light bordered box would be genuinely invisible. This is the **exact same
  bug shape** already found and fixed twice this session (badges, then backtick-code spans) — a blanket
  text-color override clobbering a component that keeps its own light background. If this hypothesis is
  right, it would affect: the findings cards and the "Ask the Copilot" chat panel on
  `pages/2_Investigation_Demo.py` (the "right-side panel" the user is almost certainly describing), the nav
  cards on `pages/home.py`, and any other `st.container(border=True)` in the app.
  **Suggested fix:** add `[data-testid="stVerticalBlockBorderWrapper"]` (and `[data-testid="stChatMessage"]`,
  `[data-testid="stChatInput"]` for the chat panel specifically) to the dark override's background-color rule,
  same as `[data-testid="stSidebar"]` already gets. **Verify by actually opening Investigation Demo in dark
  mode and reading a finding card / the chat history before declaring this fixed** — don't ship on the
  hypothesis alone, the last two times this exact bug shape appeared, the concrete details differed slightly
  from the first guess.

### 4d. Mobile responsiveness
Reported: on mobile viewport, KPI tiles and table text get misaligned, and long Alert Type text makes it
worse. This is a real, structural issue — the Case Queue table and KPI rows are built with `st.columns()`,
which does not reflow/stack on narrow viewports by default; long text in a fixed-width column just overflows
or squeezes everything else. Not investigated or fixed this session. Likely needs either (a) CSS media queries
that stack `st.columns()` output vertically below some breakpoint, or (b) restructuring the Case Queue table
into a card-per-row layout below a breakpoint instead of a fixed column grid. Test using the browser tool's
`resize_window` with `preset: "mobile"`.

### 4e. Tooltips / contextual help throughout, especially Admin Rule Config
Requested: every page should explain itself better — specifically called out Admin Rule Config's radio
buttons/decision controls ("if I select this radio button, there should be some information about it"), plus
general validation messaging. `st.radio`, `st.selectbox`, `st.slider` etc. all accept a `help=` kwarg (same
mechanism just used to fix the Investigate button tooltips) — this is a straightforward, low-risk pass to add
short explanatory `help=` text to the key decision points in `pages/4_Admin_Rule_Config.py`, the Human
Decision panel in `pages/2_Investigation_Demo.py`, and the Compliance action radio in
`pages/3_Compliance_Queue.py`. Not started.

## 5. Suggested order for next session

Roughly in the order raised, adjusted for risk/value:
1. Fix the two confirmed/likely dark-mode contrast bugs (4c) — these are real correctness bugs, fast to fix,
   high value. Verify the bordered-container hypothesis live before committing to it.
2. KPI tile coloring (4a) — well-scoped, safe, reuses existing color variables.
3. Tooltips pass (4e) — safe, additive, no risk of regressing anything.
4. Logo + login screen redesign (4b) — needs an actual asset first (image generation or sourcing), then wiring
   it into `page_banner()`/the login form/the hero.
5. Mobile responsiveness (4d) — the most structurally involved; budget real time for this, don't rush it late
   in a session the way some of tonight's fixes had to be.

Ship each as its own commit (matches the pattern used all session), verify locally in the browser (both
light/dark mode, and mobile preset for 4d) before pushing, run `scripts/ci_check.py`, then push and confirm
the Railway deploy actually lands (see §2 above about the queue being slow).

## 6. Operational notes / gotchas for whoever continues

- **Local testing pattern:** kill any stale `streamlit run` process on the port you're about to reuse before
  starting a new one — `netstat -ano | grep ":<port>" | grep LISTENING` then `taskkill //F //PID <pid>`.
  Always `rm -f data/investigateiq_runtime.db` before a fresh local run so you're not reading stale local
  state. Use `--server.fileWatcherType=none` to avoid a hot-reload edge case, but remember that means **you
  must fully restart the process** after editing any `.py` file — hot reload won't pick it up.
- **`railway run python3 -c "..."` sometimes silently returns no output** in this environment; if that
  happens, write the script to a file in the scratchpad directory and run that file instead, rather than
  retrying the inline `-c` form.
- **This session hit a transient tool-classifier error** (all tool calls failing with "server-side auto mode
  classifier gave no verdict") for a few minutes partway through — it resolved on its own. If it recurs,
  Read/Grep/Glob keep working; wait and retry Bash/Browser tools rather than assuming something is broken.
- **All data in this project is fictional** — this constraint has been strictly maintained all session and
  must continue to be.
- Cached reports only exist for 5 of the now-42 cases (one per typology: CASE-001, CASE-002, CASE-003,
  CASE-006, CASE-041). Any other case selected in "Cached" mode on Investigation Demo falls back to a live
  Gemini call.

## 7. Reference

- **Admin passcode** (Knowledge Base / Rule Config pages): `IQ-Demo-2026`
- **Full build history:** `Product Docs/BUILD-STATUS.md`
- **Original requirements pack:** `Product Docs/Sentinel-AML-Document.md` and the numbered `Product Docs/0X-*.md`
  files
