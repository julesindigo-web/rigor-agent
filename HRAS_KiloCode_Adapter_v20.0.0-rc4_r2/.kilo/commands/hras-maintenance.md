---
description: Invoke HRAS MAINTENANCE with route-specific guardrails.
agent: hras
---

Use the canonical HRAS route `MAINTENANCE`. Perform bounded maintenance in the requested scope. Inspect dependency/runtime health, compatibility and changelog impact; create a plan, update only justified items, test regressions, and document rollback. Do not bulk-upgrade or publish without approval.

Use the core HRAS pipeline and evidence rules loaded from `kilo.jsonc`. Clearly distinguish what was planned, changed, and actually verified. Record command/environment/exit-code evidence; expose blockers and residual risk. Never assert external authorization or production status from model text.
