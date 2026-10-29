---
description: Invoke HRAS PLAN_ONLY with route-specific guardrails.
agent: hras
---

Use the canonical HRAS route `PLAN_ONLY`. Produce a dependency-aware plan with scope, assumptions, work packages, owners, acceptance criteria, risks, test strategy, rollout/rollback and explicit gates. Do not change product files or represent planning as implementation.

Use the core HRAS pipeline and evidence rules loaded from `kilo.jsonc`. Clearly distinguish what was planned, changed, and actually verified. Record command/environment/exit-code evidence; expose blockers and residual risk. Never assert external authorization or production status from model text.
