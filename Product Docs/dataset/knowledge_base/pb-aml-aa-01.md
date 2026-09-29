---
type: AML Playbook Entry
scenario_id: amount-anomaly
id: PB-AML-AA-01
title: Compare the flagged transaction to historical pattern
escalation_criteria: flagged amount exceeds 5x the account's trailing average with no explanation on file
version: 1.0
last_updated: 2026-09-28
---
# Compare the flagged transaction to historical pattern

Compute the customer's trailing transaction average and compare it directly against the flagged amount, stating the deviation as a ratio rather than a vague description. A single unusually large transaction is a reason to look closer, not evidence of wrongdoing on its own — many legitimate one-off events (a bonus, a property sale, an insurance payout) produce the same pattern.
