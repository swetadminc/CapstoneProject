/* Capture current InvestigateIQ screens for the production walkthrough.

   This records only non-submitting interactions. It does not create an
   intake case, record a human decision, or submit a Compliance action.
   Admin pages are deliberately captured in their locked state only; their
   passcode must never be stored in capture automation.
*/
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const http = require("http");

const root = path.resolve(__dirname, "..");
const screenDir = path.join(root, "assets", "walkthrough_screens");
const manifestPath = path.join(screenDir, "2026_current_capture_manifest.json");
const edge = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const width = 1280;
const height = 720;
const production = "https://investigateiq-app-production.up.railway.app/";
const captured = [];

fs.mkdirSync(screenDir, { recursive: true });

function waitForServer(url, timeoutMs = 45000) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const request = http.get(url, response => {
        response.resume();
        if (response.statusCode && response.statusCode < 500) return resolve();
        retry();
      });
      request.on("error", retry);
      request.setTimeout(2500, () => { request.destroy(); retry(); });
      function retry() {
        if (Date.now() - started > timeoutMs) reject(new Error(`Timed out waiting for ${url}`));
        else setTimeout(attempt, 500);
      }
    };
    attempt();
  });
}

async function settle(page) {
  await page.waitForLoadState("domcontentloaded");
  // Streamlit sends page fragments after the initial DOM event.  Waiting for
  // the finished fragment avoids recording a half-rendered screen.
  await page.waitForTimeout(4200);
}

async function capture(page, name, target = null) {
  const file = path.join(screenDir, `2026_${name}.png`);
  const fullHeight = await page.evaluate(() => Math.max(
    document.documentElement.scrollHeight, document.body.scrollHeight, window.innerHeight
  ));
  let targetPoint = null;
  if (target) {
    const element = page.locator(target).first();
    if (await element.count()) {
      const box = await element.boundingBox();
      if (box) targetPoint = {
        x: Math.round(box.x + box.width / 2),
        y: Math.round(box.y + box.height / 2 + await page.evaluate(() => window.scrollY)),
      };
    }
  }
  await page.screenshot({ path: file, fullPage: true, animations: "disabled" });
  captured.push({ name, file: path.basename(file), width, height: fullHeight, target: targetPoint });
  console.log(`captured ${name}: ${fullHeight}px`);
}

async function scrollAndCapture(page, name, delta, target = null) {
  // Keep the cursor over the main canvas, never the sidebar, so the recorded
  // state follows the page the narration is discussing.
  await page.mouse.move(1080, 560);
  await page.mouse.wheel(0, delta);
  await page.waitForTimeout(900);
  await capture(page, name, target);
}

async function go(page, base, route) {
  // With Streamlit, a direct URL visit opens a new browser session and loses
  // the workspace identity. Follow the visible sidebar instead so each page
  // in the video is the real, current signed-in demo state.
  const labels = {
    Case_Queue: "Case Queue",
    Evidence_RAG: "Evidence & RAG",
    Compliance_Queue: "Compliance Queue",
    Analytics: "Analytics",
    Global_Search: "Global Search",
    Project_Team: "Project & Team",
    Admin_Knowledge_Base: "Admin: Knowledge Base",
    Admin_Rule_Config: "Admin: Rule Config",
  };
  const label = labels[route];
  const link = label ? page.locator("[data-testid='stSidebarNav']").getByText(label, { exact: true }) : null;
  if (link && await link.count()) {
    await link.click();
    await settle(page);
    return;
  }
  await page.goto(`${base}${route}`, { waitUntil: "networkidle", timeout: 60000 });
  await settle(page);
}

async function enterWorkspace(page) {
  await page.goto(production, { waitUntil: "networkidle", timeout: 60000 });
  await settle(page);
  // Streamlit gives the adjacent help control an aria-label of “Your name”,
  // so use the actual text-input element rather than label resolution.
  const name = page.locator("input[type='text']").first();
  if (await name.count()) {
    await name.fill("Demo Investigator");
    await page.getByRole("button", { name: "Open workspace", exact: true }).click();
    await settle(page);
  }
}

async function clickText(page, label) {
  const control = page.getByText(label, { exact: true }).first();
  if (await control.count()) {
    await control.click();
    await page.waitForTimeout(900);
  }
}

async function productionCaptures(page) {
  await page.goto(production, { waitUntil: "networkidle", timeout: 60000 });
  await settle(page);
  await capture(page, "home_guest", "#root");

  await enterWorkspace(page);
  await capture(page, "home_workspace", "[data-testid='stSidebarNav']");
  await scrollAndCapture(page, "home_workspace_lower", 620, "text=Start here");

  await go(page, production, "Case_Queue");
  await capture(page, "case_queue_top", "h1");
  await scrollAndCapture(page, "case_queue_table", 630, "text=Case");
  const fields = page.locator("input");
  const placeholders = await fields.evaluateAll(inputs => inputs.map(input => input.getAttribute("placeholder") || ""));
  const searchIndex = placeholders.findIndex(value => /customer|search/i.test(value));
  if (searchIndex >= 0) {
    await fields.nth(searchIndex).fill("Coastal");
    await page.waitForTimeout(850);
  }
  await capture(page, "case_queue_filtered", "button:has-text('Open')");

  await go(page, production, "Evidence_RAG");
  await capture(page, "evidence_case_records", ".iq-case-confidence");
  await scrollAndCapture(page, "evidence_case_records_detail", 610, ".iq-case-confidence");
  const copilotLauncher = page.getByRole("button", { name: /Ask InvestigateIQ/ });
  if (await copilotLauncher.count()) {
    await copilotLauncher.click();
    await page.waitForTimeout(900);
    await capture(page, "evidence_copilot_open", "text=InvestigateIQ Copilot");
    const closeCopilot = page.getByRole("button", { name: "×", exact: true });
    if (await closeCopilot.count()) await closeCopilot.click();
    await page.waitForTimeout(500);
  }
  for (const [label, name] of [
    ["Rule Lab", "evidence_rule_lab"],
    ["Fictional Intake", "evidence_fictional_intake"],
    ["Source & chunks", "evidence_source_chunks"],
    ["Search the index", "evidence_search_index"],
    ["Method & code", "evidence_method_code"],
  ]) {
    await clickText(page, label);
    await capture(page, name, "h2");
    if (["Source & chunks", "Search the index", "Method & code"].includes(label)) {
      await scrollAndCapture(page, `${name}_detail`, 620, "h2");
    }
  }

  await go(page, production, "Compliance_Queue");
  await capture(page, "compliance_queue", "h1");
  await scrollAndCapture(page, "compliance_queue_detail", 620, "text=Compliance action");
  await go(page, production, "Analytics");
  await capture(page, "analytics", "h1");
  await scrollAndCapture(page, "analytics_charts", 620, "h2");
  await scrollAndCapture(page, "analytics_lower_charts", 620, "h2");
  await go(page, production, "Global_Search");
  const search = page.locator("input[type='text']").first();
  if (await search.count()) {
    await search.fill("Coastal");
    await page.waitForTimeout(850);
  }
  await capture(page, "global_search", "h1");
  await go(page, production, "Project_Team");
  await capture(page, "project_team", "h1");
  await scrollAndCapture(page, "project_team_roles", 620, "text=What each role can do");
  await go(page, production, "Admin_Knowledge_Base");
  await capture(page, "admin_knowledge_locked", "h1");
  await go(page, production, "Admin_Rule_Config");
  await capture(page, "admin_rules_locked", "h1");
}

async function localWorkspaceCapture(browser) {
  const child = spawn(process.env.PYTHON || "python", [
    "-m", "streamlit", "run", "app.py", "--server.port", "8517", "--server.headless", "true",
  ], { cwd: root, stdio: "ignore", windowsHide: true });
  try {
    await waitForServer("http://127.0.0.1:8517");
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
    await page.goto("http://127.0.0.1:8517/", { waitUntil: "networkidle", timeout: 60000 });
    await page.locator("input[type='text']").first().fill("Demo Investigator");
    await page.getByRole("button", { name: "Open workspace", exact: true }).click();
    await settle(page);
    const workspaceLink = page.locator("[data-testid='stSidebarNav']").getByText("Investigation Workspace", { exact: true });
    await workspaceLink.click();
    await settle(page);
    // The default CASE-001 is the saved-report example. Keeping that default
    // gives the walkthrough a deterministic, non-submitting report replay.
    const runButton = page.getByRole("button", { name: /Run investigation/ });
    if (!(await runButton.count())) {
      console.error("Workspace report action unavailable. Current page text:\n" +
        (await page.locator("body").innerText()).slice(0, 4000));
      await capture(page, "workspace_entry");
      return;
    }
    await runButton.click();
    await page.waitForTimeout(2500);
    await capture(page, "workspace_current_report", "text=Evidence confidence");
    await page.mouse.move(1080, 560);
    await page.mouse.wheel(0, 520);
    await page.waitForTimeout(900);
    await capture(page, "workspace_confidence", "text=Evidence confidence");
    await page.mouse.wheel(0, 650);
    await page.waitForTimeout(900);
    await capture(page, "workspace_findings", "text=Findings");
    await page.close();
  } finally {
    child.kill();
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: edge });
  try {
    if (!process.argv.includes("--workspace")) {
      const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
      await productionCaptures(page);
      await page.close();
    }
    await localWorkspaceCapture(browser);
    const existing = fs.existsSync(manifestPath) ? JSON.parse(fs.readFileSync(manifestPath, "utf8")) : [];
    fs.writeFileSync(manifestPath, JSON.stringify([...existing, ...captured], null, 2));
    console.log(manifestPath);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.stack || error); process.exit(1); });
