---
name: hras-evidence-verification
description: Use before making material claims about tests, source inspection, security, benchmark results, deployment, release readiness, compliance, or completed work; checks hashes, run identity, freshness, and evidence sufficiency.
---

# HRAS evidence verification

For each material claim identify its subject, source, version/hash, environment, observed time, scope, method, result and exact evidence location. Reopen the underlying record. Distinguish `PASS`, `FAIL`, `NOT_RUN`, `BLOCKED`, `UNKNOWN`, `STALE`, and `NOT_APPLICABLE`. A test definition is not a run; aggregate counts are not per-case evidence; a citation is not validation; a model self-report is not an observed state. Verify test case hash, fixture bytes, environment ID, test oracle and allowed tool surface. Confirm final artifact identity matches the artifact named in the evidence. If anything is missing, downgrade the claim and report exact closure requirements.
