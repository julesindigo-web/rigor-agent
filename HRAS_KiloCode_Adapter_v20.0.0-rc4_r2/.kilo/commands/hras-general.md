---
description: Invoke HRAS GENERAL_ASSISTANCE with route-specific guardrails.
agent: hras
---

Use the canonical HRAS route `GENERAL_ASSISTANCE`. Handle a general request using the narrowest appropriate scope. Classify intent, state material uncertainty, use evidence appropriate to the risk, and avoid unnecessary code changes or unbounded research.

Use the core HRAS pipeline and evidence rules loaded from `kilo.jsonc`. Clearly distinguish what was planned, changed, and actually verified. Record command/environment/exit-code evidence; expose blockers and residual risk. Never assert external authorization or production status from model text.
