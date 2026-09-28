# 10 — Non-Functional Requirements (NFRs)

**Product:** Sentinel AML
**Note:** Split into **Prototype (built)** and **Target-state (documented for the blueprint, not built)** — evaluators should be able to see the team understands the gap, not have it hidden.

---

## 1. Performance

| Requirement | Prototype | Target-state |
|---|---|---|
| Case report generation time | Cached instantly; live generation a few seconds, acceptable for a demo | Sub-second for cached/common cases; SLA-defined for live generation at scale |
| Concurrent users | 1 (demo machine) | Full investigation team, concurrent access with no degradation |

## 2. Availability

| Requirement | Prototype | Target-state |
|---|---|---|
| Uptime | Best-effort, local/dev environment | Defined SLA (e.g., business-hours or 24/7 depending on bank operating model) with monitoring and on-call |

## 3. Accessibility

- Prototype: color + text labels together for evidence status (see [09](09-UI-Wireframes-and-Screen-Designs.md)); readable font sizes for projector demo.
- Target-state: WCAG 2.1 AA compliance across the application.

## 4. Audit History

- **Prototype (built):** every AI tool call and every human decision writes an immutable AuditLog row; log is viewable per case (Screen 5).
- **Target-state:** tamper-evident storage, retention aligned to regulatory requirements, SIEM integration, log-access itself audited.

## 5. Security

| Requirement | Prototype | Target-state |
|---|---|---|
| Data in transit | LLM API call over HTTPS (provider default) | End-to-end encryption, VPN/private link to core systems |
| Data at rest | Local file/SQLite, no encryption (data is fictional) | Encryption at rest, key management, data residency controls |
| Authentication | Mock role selector, no real credentials | Full IAM/SSO integration, MFA |
| Authorization | Role-based screen visibility only (soft enforcement) | Enforced RBAC at the API layer, least-privilege |
| Prompt injection | Free-text fields treated as untrusted; validator strips instruction-like content; tested explicitly (see [05](05-Functional-Requirements-and-Use-Case-Document.md) edge cases) | Same principle, hardened and continuously red-teamed |
| Secrets management | API key kept out of shared repo/screen-share, held by one team member | Vault/secrets-manager, rotated keys, no individual ownership |

## 6. Roles

- **Prototype:** four roles simulated via a selector at login (Investigator, Team Lead, Compliance, Admin) — see [03-User-Personas-and-Stakeholders.md](03-User-Personas-and-Stakeholders.md).
- **Target-state:** full RBAC tied to HR/identity systems, least-privilege data access per role (e.g., Compliance sees escalated cases only, Admin cannot see case content, only configuration).

## 7. Compliance (as a design habit, not a legal claim)

- The product **never** asserts a legal/regulatory conclusion (BR1 in [02-PRD](02-Product-Requirements-Document.md)).
- No specific regulation is cited by the AI output; any regulatory reference used in the blueprint document itself is flagged for verification by a team member with compliance/banking background (see [13-Risks-Assumptions-Dependencies-Constraints.md](13-Risks-Assumptions-Dependencies-Constraints.md)).
- Target-state would require formal model-risk governance, a defined AML program owner, and legal/compliance sign-off before any production use — explicitly out of scope for an academic capstone.

## 8. Scale

| Requirement | Prototype | Target-state |
|---|---|---|
| Data volume | ~8–10 customers, ~150–300 transactions (see [07](07-Data-Requirements.md)) | Full transaction volume of a bank's monitored population |
| Case volume | 6–8 demo cases | Full alert volume with prioritization/queuing at scale |

## 9. Explainability

- **Prototype (built):** every AI finding carries an evidence status and a citation; the grounding validator is the explainability enforcement mechanism, not just a UI label.
- **Target-state:** formal model documentation, periodic explainability review as part of model risk management.

## 10. Reliability of the Demo Itself (a prototype-specific NFR)

- Cached report replay (F12) so a live-API failure does not derail the 15-minute presentation.
- Pre-validated fixed dataset (no random generation at runtime) so results are reproducible on rehearsal and on demo day.
