---
description: Independently assess release readiness from fresh artifact-bound evidence and mandatory gate results.
agent: hras
---

Use `SECURITY_REVIEW` plus the evidence reviewer. Freeze the candidate identity (spec, schema, source, code, config, dependency lock, test suite and target environment hashes). Check all required tests actually ran against materialized/hash-bound fixtures and approved oracles; validate auth/authorization controls, side-effect ledger, idempotency/read-back, failure injection, rollback, security/privacy, dependency provenance, logs, ops runbook, monitoring and owner approvals. Compare all blockers and non-waivable policies. The Kilo agent may recommend a status, not grant one. Any unknown/unrun mandatory gate blocks production-ready claims. Deliver a per-gate table of PASS/FAIL/UNKNOWN/NOT_RUN/BLOCKED, evidence IDs, residual risks, owner, and closure criteria. Do not deploy or merge.
