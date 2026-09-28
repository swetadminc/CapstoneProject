# 09 — UI Wireframes / Screen Designs

**Product:** Sentinel AML
**Format note:** These are text/ASCII wireframes — enough to build from and to drop into slides. Convert to Figma/draw.io mockups if the team has time and a designer.

---

## Screen 1 — Login / Role Landing

```
+--------------------------------------------------+
|  SENTINEL AML          [Prototype — mock data]    |
|                                                    |
|   Sign in as:  ( ) Investigator                   |
|                ( ) Team Lead                       |
|                ( ) Compliance Officer               |
|                ( ) Admin                            |
|                                                    |
|   Name: [___________]      [ Enter ]              |
|                                                    |
|   This is an academic prototype. All customer,    |
|   account and transaction data is fictional.       |
+--------------------------------------------------+
```

## Screen 2 — Case Queue Dashboard (the real "landing page")

```
+--------------------------------------------------------------+
| SENTINEL AML   Investigator: [Name]        [mock data banner] |
+--------------------------------------------------------------+
|  Filters: [Status v] [Priority v] [Alert type v]               |
|--------------------------------------------------------------|
|  Case      Customer   Alert Type          Rule(s)   Priority  |
|  CASE-001  CUST-004   Rapid movement       R1+R2      High    |
|  CASE-002  CUST-007   Rapid movement       R1+R2      Med     |
|  CASE-003  CUST-002   Rapid movement       R1+R2      High    |
|  ...                                                            |
|--------------------------------------------------------------|
|  KPI strip: Open cases: 6   Avg age: 1.2d   Escalated: 1       |
+--------------------------------------------------------------+
```

## Screen 3 — Investigation Workspace (core screen)

```
+--------------------------------------------------------------+
| CASE-001  |  Customer CUST-004  |  Account ACC-1004  | Status: Open |
| Alert trigger: Rule R1+R2 fired — 50x baseline, 86% moved in 48h    |
+--------------------------------------------------------------+
| ALERT SUMMARY STRIP                                            |
| Trigger amt: Rs 1,00,00,000 | Baseline avg: Rs 2,00,000        |
| Txns in window: 4 | Accounts involved: 4 | Review period: 72h  |
+--------------------------------------------------------------+
| TRANSACTION TIMELINE                 | FUND-FLOW / NETWORK VIEW|
| Sep20 +1,00,00,000 (credit)          |  CUST-004               |
| Sep20 -95,00,000 -> ACC-B            |     |                   |
| Sep21 -90,00,000 -> ACC-C            |  ACC-A --95L--> ACC-B   |
| Sep21 -85,00,000 -> ACC-D (external) |          --90L--> ACC-C |
|                                        |               --85L--> ACC-D (external, no data) |
+--------------------------------------------------------------+
| AI FINDINGS (AI recommendation — draft)                        |
|  [VERIFIED] Amount 50x historical average   [cite: TXN-10543]  |
|  [VERIFIED] 86% moved out within 48h        [cite: TXN-...]    |
|  [MISSING]  No KYC on record for ACC-D (external)               |
|  [MISSING]  No declared source of funds for the credit          |
+--------------------------------------------------------------+
| INVESTIGATION QUESTIONS         | RECOMMENDED NEXT STEPS        |
| - Where did the Rs1Cr come from?| 1. Request source-of-funds doc |
| - Is ACC-B/C/D previously flagged| 2. Review relationship ACC-A/B |
|                                   |    [playbook: PB-AML-07-02]  |
+--------------------------------------------------------------+
| HUMAN DECISION  (separate panel, distinct color/border)         |
|  Action: ( ) Request info  ( ) Add evidence  ( ) Escalate  ( ) Close |
|  Rationale (required): [_________________________________]    |
|  Findings accepted: [x][x][ ][x]   Findings rejected: [ ]      |
|                                  [ Submit decision ]            |
+--------------------------------------------------------------+
| Status: PENDING HUMAN REVIEW                                   |
+--------------------------------------------------------------+
```

**Design note:** the AI Findings panel and the Human Decision panel use visibly different colors/borders (e.g., AI = blue outline "draft," Human = green outline "action required") so a first-time viewer instantly sees the boundary the product enforces.

## Screen 4 — Escalation / Compliance Queue

```
+--------------------------------------------------------------+
| COMPLIANCE REVIEW QUEUE                                        |
| Case      Escalated by     Reason                    Date      |
| CASE-001  Investigator A   Unverified source of funds  Sep22    |
+--------------------------------------------------------------+
| [Open case — read-only investigation view + escalation note]   |
+--------------------------------------------------------------+
```

## Screen 5 — Audit Log Viewer

```
+--------------------------------------------------------------+
| AUDIT LOG — CASE-001                                            |
| Time       Actor        Action                                 |
| 09:02:11   System        Alert generated (R1+R2, rule v1.0)     |
| 09:02:12   System        Case created, added to queue           |
| 09:14:03   AI Agent      Called get_transaction_history          |
| 09:14:05   AI Agent      Called trace_fund_flow                  |
| 09:14:22   AI Agent      Report generated, validator: PASS       |
| 10:01:07   Investigator  Reviewed case                            |
| 10:12:40   Investigator  Action: Escalate — rationale: "..."     |
+--------------------------------------------------------------+
```

## Screen 6 — Admin / Rule Configuration (light)

```
+--------------------------------------------------------------+
| RULE CONFIGURATION                                              |
| R1  Amount deviation     Threshold: [5]x baseline   [Save]      |
| R2  Rapid pass-through   Threshold: [80]% within [72] hours [Save]|
+--------------------------------------------------------------+
| PLAYBOOK ENTRIES (scenario: rapid-movement)                     |
| PB-AML-07-01  Review customer KYC/profile information            |
| PB-AML-07-02  Review relationship between sending/receiving accts|
| ... [Edit]                                                      |
+--------------------------------------------------------------+
```

## Mobile / Responsive Requirements

Not required for the capstone demo (desktop-only, presented on a laptop/projector). Noted as a target-state requirement in [10-Non-Functional-Requirements.md](10-Non-Functional-Requirements.md) rather than built.

## Accessibility Expectations

- Evidence-status tags use **color + text label** together (not color alone), since color-only status indicators fail accessibility and are also hard to read on a projector.
- All screens keep a persistent text banner: "Prototype — fictional data. AI assists; the investigator decides." (not relying on a tooltip or icon alone).
