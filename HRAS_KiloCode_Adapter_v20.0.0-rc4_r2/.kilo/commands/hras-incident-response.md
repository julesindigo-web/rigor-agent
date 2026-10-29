---
description: Invoke HRAS INCIDENT_RESPONSE with route-specific guardrails.
agent: hras
---

Use the canonical HRAS route `INCIDENT_RESPONSE`. Preserve evidence first; classify severity, affected assets, scope and uncertainty; propose containment/recovery with an explicit approval gate. Do not destroy logs, rotate/revoke credentials, change production, or run live containment without scoped authority. Reconcile any external action outcome before retry.

Use the core HRAS pipeline and evidence rules loaded from `kilo.jsonc`. Clearly distinguish what was planned, changed, and actually verified. Record command/environment/exit-code evidence; expose blockers and residual risk. Never assert external authorization or production status from model text.
