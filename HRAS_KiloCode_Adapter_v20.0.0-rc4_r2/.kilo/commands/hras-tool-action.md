---
description: Invoke HRAS TOOL_ACTION with route-specific guardrails.
agent: hras
---

Use the canonical HRAS route `TOOL_ACTION`. Prepare and evaluate a requested tool/external action. Identify exact target, scope, environment, identity, consequences, permissions, idempotency, rollback and postcondition. If a trusted authorization broker/operation ledger is absent or authorization is not observed, stop before effect and report the gap. Never blindly retry an unknown outcome.

Use the core HRAS pipeline and evidence rules loaded from `kilo.jsonc`. Clearly distinguish what was planned, changed, and actually verified. Record command/environment/exit-code evidence; expose blockers and residual risk. Never assert external authorization or production status from model text.
