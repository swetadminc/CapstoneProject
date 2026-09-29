---
type: AML Playbook Entry
scenario_id: velocity
id: PB-AML-VEL-03
title: Check for structuring indicators
escalation_criteria: multiple transactions clustered just below an internal review threshold
version: 1.0
last_updated: 2026-09-28
---
# Check for structuring indicators

Look specifically for a pattern of transactions sized just under a known reporting or review threshold, repeated across a short period. This is a specific red flag distinct from velocity alone and should be called out explicitly as a finding if present, with the actual amounts cited.
