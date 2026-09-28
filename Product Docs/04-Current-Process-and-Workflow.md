# 04 — Current Process / Workflow Document

**Product:** Sentinel AML — describes the **as-is** (today, without the product) process this capstone targets.

---

## 1. As-Is Process Narrative

1. A bank's transaction-monitoring platform (existing system, out of scope to rebuild) applies rules across all transactions and raises an alert when a rule fires.
2. The alert lands in a case-management queue, typically with minimal context (customer ID, account ID, rule name).
3. An investigator is assigned or claims the case.
4. The investigator manually:
   - opens the core banking / CRM system to review customer and KYC details
   - opens the transaction system to pull recent history and compute (by eye or spreadsheet) whether the flagged activity is unusual
   - checks internal systems or spreadsheets for related accounts and counterparties
   - searches for prior alerts or cases involving the customer or counterparties
   - reviews any supporting documents already on file
   - manually writes an investigation summary, usually in a free-text case note or a Word/Excel template
5. The investigator decides: close (no concern), request more information, or escalate to a senior investigator / compliance.
6. The decision and rationale are recorded, typically as free text, in the case management system.
7. Audit trail exists only insofar as the case management system logs status changes; the evidence trail itself is reconstructed from notes, screenshots, and emails if ever revisited.

## 2. Pain Points (mapped to what Sentinel AML addresses)

| Pain point | Effect | Addressed by |
|---|---|---|
| Evidence scattered across 4–6 systems | Time-consuming compilation before analysis can even start | AI Investigation Workspace pulls all evidence into one screen (mock data in prototype) |
| No structured way to say "I don't have this information" | Gaps get missed or silently assumed away | Explicit **Missing** evidence-status category |
| Free-text write-ups vary investigator to investigator | Inconsistent quality, hard to review | Structured case report template, same fields every time |
| Hard to reconstruct "what was known when" | Weak defensibility on audit/regulatory review | Full audit log of AI actions and human decisions, timestamped |
| Investigators may treat every large transaction as suspicious (or the reverse — alert fatigue) | Both over- and under-investigation risk | Twin-case design (C1 suspicious / C2 legitimate) built into the product's evidence logic — see [05](05-Functional-Requirements-and-Use-Case-Document.md) |
| No visible link between "why was this flagged" and "what should I check" | Investigator has to independently reconstruct the rule logic | Trigger Engine shows the exact rule and threshold that fired, attached to the case |

## 3. Approvals, Exceptions, and Handoffs (as-is, and how the product maps to them)

| Step | Who approves / handles today | Product equivalent |
|---|---|---|
| Alert generated | Automatic (existing monitoring system) | Trigger Engine (rule-based, F3) |
| Case assignment | Team lead / queue auto-assignment | Case queue dashboard (F2/F4) |
| Evidence gathering | Investigator, manual | AI Investigation Workspace (F5/F6) |
| Request for more information | Investigator emails/calls relevant teams | "Request information" action (F7) — logged, outcome manually re-entered by investigator (integration out of scope) |
| Escalation | Investigator flags to senior/compliance manually | Escalation queue (F9) |
| Final regulatory decision (e.g., filing) | Compliance/MLRO, outside the investigator's system entirely | **Out of scope** — product stops at escalation hand-off |

## 4. Future-State Summary (delta this product introduces)

The future-state process is identical in its decision authority (human investigator and compliance retain every consequential decision) but compresses steps 4–6 above from a multi-system manual exercise into a single AI-assembled workspace with mandatory citation and status tagging. See the two flowcharts:
- [Flowchart-1-End-to-End-Data-Flow.md](Flowchart-1-End-to-End-Data-Flow.md)
- [Flowchart-2-Investigation-Process-Flow.md](Flowchart-2-Investigation-Process-Flow.md)
