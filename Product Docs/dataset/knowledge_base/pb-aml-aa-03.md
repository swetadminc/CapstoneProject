---
type: AML Playbook Entry
scenario_id: amount-anomaly
id: PB-AML-AA-03
title: Check consistency with the customer's declared profile
escalation_criteria: declared income or occupation does not plausibly support the transaction size
version: 1.0
last_updated: 2026-09-28
---
# Check consistency with the customer's declared profile

Compare the flagged amount against the customer's declared annual income, occupation, and expected activity on file. A mismatch is a Conflicting-evidence finding to note and explain, not by itself a basis to escalate — declared profiles are sometimes stale or incomplete.
