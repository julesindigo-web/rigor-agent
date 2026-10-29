# HRAS execution pipeline and scope

Use the pipeline `BIND → TRIAGE → REVALIDATE → PLAN → EXECUTE → VERIFY → DELIVER` whenever applicable. Skip a phase only when it is genuinely not relevant, and state why.

## Bind and triage

- For an audit/remediation task, identify the audit report/ledger and the exact source version being audited. If the audit findings are absent, stop remediation and report the missing input; do not silently replace it with a new audit. If the source required to verify a finding is absent, mark the affected finding blocked.
- Create a worklist with ID, severity, location, audit evidence, fix recommendation, as-of date, current reproduction, dependency, and initial disposition.
- Re-triage by severity, exploitability/blast radius, effort, and dependencies. Allowed initial dispositions: `FIX-NOW`, `FIX-CONDITIONAL`, `DEFER` (reason required), and `CHALLENGE` (specific evidence required).

## Revalidate, plan, execute

- Reproduce every fix-now finding against current bytes before editing. Exact source/line mismatch or absent reproduction may mean `STALE`; insufficient evidence means `CHALLENGED`, not blind repair.
- Build a dependency graph and reversible slices. Keep each slice small and the tree buildable. One semantic slice per commit when commits are authorized and appropriate.
- Add/fix a failing regression test before a bug fix; implement the minimum correction; run the affected tests, then the required wider suite.
- Record each failed attempt in the ledger. Same failure signature three times, no progress twice, or four repeated failures require a change in approach or explicit deferral.
- Do not scope-drift into unrelated refactoring or opportunistic hardening. Report newly discovered issues separately with disposition.

## Continue independent work

A blocked external/integration finding does not block independent safe local tasks. Do not fake a missing fixture, adapter, runtime, owner approval, or external authority. Stop before gated side effects; prepare the exact command/plan/rollback for the authorized operator.
