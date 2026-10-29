---
description: Invoke HRAS PROTOTYPE with route-specific guardrails.
agent: hras
---

Use the canonical HRAS route `PROTOTYPE`. Build a bounded prototype only when requested. Mark it non-production, document shortcuts and missing security/operations, test the learning objective, and prevent prototype outputs from being labelled production-ready.

Use the core HRAS pipeline and evidence rules loaded from `kilo.jsonc`. Clearly distinguish what was planned, changed, and actually verified. Record command/environment/exit-code evidence; expose blockers and residual risk. Never assert external authorization or production status from model text.
