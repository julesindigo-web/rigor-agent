---
description: Execute the audit-driven remediation pipeline with TDD, minimal slices, proof ledger, and rollback.
agent: hras
---

Use the user's supplied audit report/ledger **and** the original source audited. Both are mandatory. If the findings are missing, halt remediation and report the missing input; do not silently audit afresh. If a source required to verify a finding is missing, block that finding and continue only independent safe findings.

Pipeline: `BIND → TRIAGE → REVALIDATE → PLAN → EXECUTE → VERIFY → DELIVER`. Extract every finding as ID/severity/location/evidence/fix/status; record audit as-of date; validate the current source and reproduce each fix-now finding before changing it. Triage by severity, blast radius, exploitability, effort, and dependencies. Work in reversible slices and maintain a ledger of failed attempts. Bug fix: regression test first, prove failure before, make minimal fix, prove after, run affected and risk-appropriate full tests, review regression edges, define and test rollback when feasible. No weakened tests, no unrelated fixes, no silent removal of challenged findings. External/deployment/infra/non-local migration/push steps stop for scoped authorization; prepare but do not bypass. Final output follows `templates/HRAS_REMEDIATION_DELIVERY_TEMPLATE.md`.
