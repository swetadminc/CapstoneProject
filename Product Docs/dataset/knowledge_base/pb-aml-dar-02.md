---
type: AML Playbook Entry
scenario_id: dormant-reactivation
id: PB-AML-DAR-02
title: Escalation criteria for a dormant account reactivation
escalation_criteria: large reactivating transaction with no declared explanation, especially if funds pass through quickly
version: 1.0
last_updated: 2026-09-29
---
# Escalation criteria for a dormant account reactivation

Escalate when the reactivating transaction is large relative to the account's pre-dormancy baseline, the
counterparty is not one the customer has transacted with before, and no reasonable explanation for the
reactivation is on file after a documented request. A dormant account receiving a single explainable payment
(an inheritance, a maturing deposit, a refund) is not automatically suspicious — the escalation bar is the
combination of the dormancy length, the size and unfamiliarity of the reactivating transaction, and whether the
funds are quickly moved on again, not dormancy or a large transaction alone.
