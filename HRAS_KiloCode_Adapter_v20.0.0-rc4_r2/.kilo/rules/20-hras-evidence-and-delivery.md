# HRAS evidence and delivery gates

Every material outcome claim must be bound to an artifact/source hash, environment, tool/model/config version where relevant, timestamp, scope, and fresh evidence.

## Evidence states

- `PASS`: the required check actually ran and its criteria passed.
- `FAIL`: the check ran and failed.
- `NOT_RUN`: it did not run.
- `BLOCKED`: a named prerequisite prevented execution.
- `UNKNOWN`: evidence is missing, ambiguous, or untrustworthy.
- `STALE`: prior evidence no longer describes current source/artifact/environment.
- `NOT_APPLICABLE`: a documented and approved applicability decision says the check is out of scope.

Never aggregate `NOT_RUN`, `BLOCKED`, `UNKNOWN`, or `FAIL` into a pass. A citation is not validation; a test case definition is not an executed test; a static validator is not an integration test.

## Proof ledger

For each fixed finding, report: before reproduction; source path/lines/hash; exact change/slice; regression test; command/environment/exit code; after reproduction; wider suite; remaining scope; rollback command/path and tested status. If any proof field is unavailable, do not mark `FIXED+PROOF`.

## Release and final response

- HRAS's status enums are in `.hras/source/HRAS_v20_Policy_Registry.json`. Recommend a status only; don't pretend the Kilo agent is the trusted controller that can authorize one.
- `PRODUCTION_READY`, `DEPLOYED_AND_VERIFIED`, and `MASTERPIECE_VERIFIED` require target-specific, fresh evidence and all applicable hard gates. They cannot be inferred from a green local test suite.
- Final deliverables must name artifacts and versions, changes by slice, test commands/results, regression evidence, rollback, residual risk, blocked prerequisites, assumptions, and re-audit checklist.
