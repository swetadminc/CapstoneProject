# Flowchart 1 — End-to-End Data Flow

**Product:** Sentinel AML
**How to use this file:** Copy the code block below into [mermaid.live](https://mermaid.live), the Mermaid VS Code extension, or draw.io's "Insert > Mermaid" option to get a rendered, editable diagram for the blueprint document and the slide deck.

Shows: how a transaction becomes a trigger, how a trigger becomes a case, how the AI agent assembles evidence, and how the case reaches a human decision and the audit log.

```mermaid
flowchart TB
  subgraph SRC["Mock Bank Systems (fictional data)"]
    TXN[Transaction Feed]
    CUST[Customer / KYC Store]
    ACCT[Account Master]
    REL[Relationship / Counterparty Store]
    HIST[Prior Alerts and Cases]
    DOC[Document Store]
  end

  TXN --> TE
  CUST --> TE
  ACCT --> TE

  subgraph MON["Monitoring Layer - rule-based, no AI"]
    TE["Trigger Engine<br/>Rule R1: amount deviation<br/>Rule R2: rapid pass-through"]
  end

  TE -->|Alert generated| ALERT[("Alert Record<br/>rule id + thresholds")]
  ALERT --> CASE["Case Created<br/>added to Case Queue"]

  CASE --> DASH["Investigator Dashboard<br/>Case Queue - landing page"]
  DASH --> CLAIM["Investigator claims case"]

  CLAIM --> AGENT

  subgraph AI["AI Investigation Layer"]
    AGENT["AI Investigation Agent"]
    TOOLS["Deterministic Tools:<br/>baseline calc, fund-flow trace,<br/>relationship lookup, history lookup"]
    AGENT <--> TOOLS
  end

  CUST --> TOOLS
  ACCT --> TOOLS
  REL --> TOOLS
  HIST --> TOOLS
  DOC --> TOOLS
  TXN --> TOOLS

  AGENT --> VALID["Grounding Validator<br/>checks citations and numbers"]
  VALID --> REPORT[("AI Case Report:<br/>red flags, evidence status,<br/>questions, next steps")]

  REPORT --> WS["Investigation Workspace<br/>Investigator reviews"]
  WS --> DECISION{"Human Decision"}
  DECISION -->|Close| CLOSE["Case Closed<br/>+ rationale"]
  DECISION -->|Request info| REQ["Request Information<br/>back to investigation"]
  DECISION -->|Escalate| ESC["Compliance Review Queue"]

  CLOSE --> AUDIT
  REQ --> AUDIT
  ESC --> AUDIT
  ESC --> COMP["Compliance Officer Review"]
  COMP --> AUDIT

  subgraph GOV["Audit and Governance"]
    AUDIT[("Immutable Audit Log")]
  end
```

## Reading Notes for the Blueprint / Deck

- The **Monitoring Layer** is deliberately rules-only — no AI/LLM involvement in raising the alert. This is worth calling out on the slide: it shows the team understood not every step should use GenAI (see [06-Technical-Architecture.md](06-Technical-Architecture.md) §1, §4).
- The **AI Investigation Layer** never writes back to source data — tools are read-only (see [08-Integration-and-API-Specifications.md](08-Integration-and-API-Specifications.md) §1).
- Every path out of "Human Decision" ends in the **Audit and Governance** block — this is the diagram's visual proof of the human-in-the-loop guarantee.
- Cross-reference: [Flowchart-2-Investigation-Process-Flow.md](Flowchart-2-Investigation-Process-Flow.md) zooms into the "Investigation Workspace -> Human Decision" portion of this diagram.
