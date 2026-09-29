---
type: AML Playbook Entry
scenario_id: amount-anomaly
id: PB-AML-AA-04
title: Escalation criteria for the amount-anomaly scenario
escalation_criteria: unresolved large-value transaction with no plausible explanation after investigation
version: 1.0
last_updated: 2026-09-28
---
# Escalation criteria for the amount-anomaly scenario

Escalate when the flagged amount remains unexplained after a documented request, AND the customer's declared profile does not plausibly account for it, AND no supporting evidence has been produced. A single large but well-documented transaction (e.g., a verified property sale) does not meet this bar.
