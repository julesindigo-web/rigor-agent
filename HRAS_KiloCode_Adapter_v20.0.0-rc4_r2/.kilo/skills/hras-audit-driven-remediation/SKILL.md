---
name: hras-audit-driven-remediation
description: Use when remediating an existing audit, findings ledger, defect register, or security review; requires read-back, reproduction-before-fix, severity/dependency triage, minimal reversible slices, proof ledger, regression checks, and rollback.
---

# HRAS audit-driven remediation

1. Bind the audit report/findings ledger and source bytes. If findings are not supplied, stop rather than silently auditing from scratch when the task explicitly requires audit-driven remediation.
2. Read the full audit. Extract every finding as ID, severity, location, evidence, recommendation, status, as-of date, dependencies, and required proof.
3. Revalidate every finding on current source before fix. Preserve stale/challenged findings with reasons; never delete silently.
4. Sort by severity, exploitation likelihood, blast radius, effort, and dependencies. Build a graph of slices and define rollback first.
5. For each bug, write a regression test, demonstrate the pre-fix failure, implement a minimal diff, then demonstrate the post-fix pass.
6. Run related tests first, then complete suites and risk-based integration/E2E/failure-injection checks. Do not hide failures by weakening tests.
7. Record each attempt and exact evidence. Repeated identical failure signatures require a change of approach; do not loop blindly.
8. Re-run the original audit check at the touched surface. Add newly discovered findings to the ledger with a disposition.
9. Report per-finding state, per-slice diff/commit, before/after proof, test outputs, rollback status, residual risks, blocked prerequisites, and the re-audit checklist.

Use `templates/HRAS_FINDING_WORKLIST_TEMPLATE.md` and `templates/HRAS_PROOF_LEDGER_TEMPLATE.md`.
