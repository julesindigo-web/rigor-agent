---
description: Invoke HRAS DESIGN_ONLY with route-specific guardrails.
agent: hras
---

Use the canonical HRAS route `DESIGN_ONLY`. Produce a decision-ready design/architecture/UX specification with requirements, alternatives, rationale, contracts, data flow, threats, acceptance criteria, rollout and rollback. Do not silently implement; implementation must be requested separately.

Use the core HRAS pipeline and evidence rules loaded from `kilo.jsonc`. Clearly distinguish what was planned, changed, and actually verified. Record command/environment/exit-code evidence; expose blockers and residual risk. Never assert external authorization or production status from model text.
