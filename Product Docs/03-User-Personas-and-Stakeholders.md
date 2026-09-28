# 03 — User Personas & Stakeholder List

**Product:** Sentinel AML

---

## 1. Personas (who uses the product)

### Persona 1 — AML Investigator (primary user)
- **Role in product:** Reviews assigned cases in the investigation workspace, works through evidence, makes and records decisions.
- **Goals:** Close/escalate cases accurately and quickly; avoid missing real red flags; avoid over-flagging legitimate activity.
- **Pain today:** Compiling evidence across systems is slow; hard to be sure nothing was missed; write-ups are inconsistent across the team.
- **What Sentinel AML gives them:** A pre-assembled, cited evidence pack, explicit "missing information" list, and a structured decision panel with mandatory rationale.
- **Primary screens:** Case queue, Investigation workspace, Human decision panel.

### Persona 2 — Investigation Team Lead
- **Role in product:** Monitors team caseload, reassigns cases, reviews quality on a sample basis.
- **Goals:** Balance workload, meet SLA, spot inconsistent decisions.
- **Primary screens:** Case queue (team view), Audit log.

### Persona 3 — Compliance Officer (MLRO-delegate view)
- **Role in product:** Reviews escalated cases only; does not use the AI investigation workspace directly for routine cases.
- **Goals:** Confirm escalation is warranted; decide on further action (outside product scope — regulatory filing is manual/out of scope).
- **Primary screens:** Escalation / compliance queue, Audit log, case read view.

### Persona 4 — System Admin (light role)
- **Role in product:** Configures the two trigger-engine rule thresholds; manages the mock playbook; manages user role assignment (mock auth).
- **Goals:** Keep detection rules current; keep next-step guidance (playbook) accurate.
- **Primary screens:** Admin / rule configuration.

### Persona 5 — Capstone Presenter / Demo Viewer (prototype-only persona)
- **Role in product:** Not a real product persona — represents the evaluator watching the 15-minute demo.
- **Goals:** Quickly understand what triggers detection, how AI helps, and where the human decides.
- **Implication for design:** The product must be legible to a first-time viewer within minutes — favors a visible trigger moment and a clearly separated AI vs. human panel (see [09-UI-Wireframes-and-Screen-Designs.md](09-UI-Wireframes-and-Screen-Designs.md)).

## 2. Stakeholder List

| Stakeholder | Interest | Involvement |
|---|---|---|
| Capstone team (7 members) | Build, present, and be evaluated on the product | Build/approve everything in this pack |
| IIT Mumbai faculty / evaluation panel | Assess against the rubric (problem relevance, process understanding, data-driven design, AI appropriateness, architecture, guardrails, roadmap, value logic, communication) | Approves the submission (evaluator, not a build stakeholder) |
| (Illustrative, for blueprint realism) Bank AML Operations Head | Would own the business case in a real deployment | Referenced in blueprint governance/roadmap sections only — not a real contact for this capstone |
| (Illustrative) Bank Compliance / MLRO function | Would own escalation policy and final regulatory decisions in a real deployment | Referenced for the Human Decision boundary and escalation design only |
| (Illustrative) Bank IT / Data Owners | Would own real source systems in a real deployment | Referenced in Data Requirements as the target-state source of truth; capstone uses mock data instead |

**Note:** The bank-side stakeholders above are illustrative — used to keep the blueprint realistic — not actual people the team has consulted. This is stated plainly so the document is not misread as claiming real institutional engagement.

## 3. RACI (who does what on this decision layer)

| Decision | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Close a case with no findings | Investigator | Investigator | — | Team Lead |
| Escalate a case | Investigator | Investigator | Team Lead (optional) | Compliance |
| Accept escalation, decide further action | Compliance Officer | Compliance Officer | Investigator | Team Lead |
| Change trigger-rule thresholds | Admin | Team Lead | Investigators (feedback on false positives) | Compliance |
| Update the mock playbook | Admin | Team Lead | Investigators | — |

This RACI illustrates the governance model the blueprint recommends (see [06-Technical-Architecture.md](06-Technical-Architecture.md) and blueprint governance section); the prototype simulates it with role-based views rather than real approval workflows.
