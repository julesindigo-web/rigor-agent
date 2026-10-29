---
description: Invoke HRAS SECURITY_REVIEW with route-specific guardrails.
agent: hras
---

Use the canonical HRAS route `SECURITY_REVIEW`. Perform a threat-informed security review. Begin read-only; inspect trust boundaries, authn/authz, input/egress, secrets, prompt injection, dependency risks, privacy and failure handling. Report evidence and executable verification plans; do not perform live exploitation or edits unless separately authorized.

Use the core HRAS pipeline and evidence rules loaded from `kilo.jsonc`. Clearly distinguish what was planned, changed, and actually verified. Record command/environment/exit-code evidence; expose blockers and residual risk. Never assert external authorization or production status from model text.
