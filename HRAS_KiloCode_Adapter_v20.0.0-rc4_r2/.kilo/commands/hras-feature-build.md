---
description: Invoke HRAS FEATURE_BUILD with route-specific guardrails.
agent: hras
---

Use the canonical HRAS route `FEATURE_BUILD`. Build the requested feature end to end. Convert intent into testable acceptance criteria, inspect local architecture, plan dependencies, implement vertical slices, test workflows/error states/security/accessibility as relevant, and provide verified handoff.

Use the core HRAS pipeline and evidence rules loaded from `kilo.jsonc`. Clearly distinguish what was planned, changed, and actually verified. Record command/environment/exit-code evidence; expose blockers and residual risk. Never assert external authorization or production status from model text.
