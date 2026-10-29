---
description: Run a read-only, source-bound HRAS audit and produce an evidence-led finding worklist.
agent: hras
---

Run `ARTIFACT_AUDIT` on the user-authorized scope. Bind the exact source artifacts, hashes, version, and as-of timestamp. If a prior audit is provided, read the full report/ledger and extract every finding before inspecting source; if not provided and user requires attachment-bound remediation, do not substitute a new audit. Delegate read-only inspection to `hras-audit`, then reconcile its report with the original source. No edits during audit. Output: scope/exclusions, methods and commands actually run, prioritized finding table, evidence paths, severity/exploitability rationale, dependency graph, challenge/stale dispositions, and next steps. Include all execution gaps.
