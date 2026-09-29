---
type: AML Playbook Entry
scenario_id: velocity
id: PB-AML-VEL-01
title: Review transaction frequency and clustering
escalation_criteria: multiple transactions clustered within an unusually short window
version: 1.0
last_updated: 2026-09-28
---
# Review transaction frequency and clustering

Count the number of transactions within the alert window and the elapsed time between them. Report both the count and the total value moved, not just one or the other — a high count of small transactions and a low count of large ones warrant different follow-up questions.
