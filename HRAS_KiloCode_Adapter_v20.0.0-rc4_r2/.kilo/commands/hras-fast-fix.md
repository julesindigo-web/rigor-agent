---
description: Invoke HRAS FAST_FIX with route-specific guardrails.
agent: hras
---

Use the canonical HRAS route `FAST_FIX`. Make the smallest safe fix for a narrowly scoped defect. Inspect current code, reproduce the defect, add a failing regression test, patch minimally, run affected tests and report proof/rollback. No broad refactor or gated external effects.

Use the core HRAS pipeline and evidence rules loaded from `kilo.jsonc`. Clearly distinguish what was planned, changed, and actually verified. Record command/environment/exit-code evidence; expose blockers and residual risk. Never assert external authorization or production status from model text.
