---
name: hras-secure-tool-action
description: Use before any external or high-impact tool action such as Git push/merge, deployment, infrastructure updates, non-local migrations, data deletion, publishing, third-party upload, billing, or permission/credential changes.
---

# HRAS secure tool action

Do not execute until exact action, purpose, target resource, environment, identity, scope, expiry, authorization, idempotency, rollback, and expected postcondition are clear and authorized by trusted controls. The user request authorizes a goal, not every possible side effect. A model-generated authorization flag is never an authority source. Prefer dry-run/plan and read-only inspection. Confirm secret redaction and destination trust. Record operation ID before submission if a trusted operation ledger exists. If submission outcome is unknown, stop resubmission and reconcile via provider operation ID, idempotency key, read-back or authoritative audit logs. If no trusted broker/ledger exists, state that the Kilo configuration cannot satisfy that HRAS requirement and stop at preparation. Never route around an explicit denial.
