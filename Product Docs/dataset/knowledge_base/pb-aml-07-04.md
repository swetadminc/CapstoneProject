---
type: AML Playbook Entry
scenario_id: rapid-movement-of-funds
id: PB-AML-07-04
title: Review transaction velocity and pass-through pattern
escalation_criteria: over 75 percent of a credit leaves within 72 hours across multiple accounts
version: 1.1
last_updated: 2026-09-28
---
# Review transaction velocity and pass-through pattern

Trace the fund-flow chain starting from the trigger credit through every subsequent outbound transaction on the same account. Record the number of hops, the elapsed time between each leg, and whether each receiving account is internal to the bank or external. A short elapsed time combined with multiple external hops is a stronger indicator than either factor alone.
