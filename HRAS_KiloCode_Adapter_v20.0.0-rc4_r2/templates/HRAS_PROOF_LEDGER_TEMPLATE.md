# HRAS Proof Ledger

| Proof ID | Finding/slice | Source hash | Before command/environment/exit/output | Regression test | Change/commit | After command/environment/exit/output | Wider suite | Rollback command/path | Rollback status | Evidence artifact/hash |
|---|---|---|---|---|---|---|---|---|---|---|
| P-001 | F-001 / slice-01 | `sha256:...` | `NOT_RUN` | test path::test name | pending | `NOT_RUN` | pending | `git revert <commit>` or path-specific restore | `UNTESTED` | `none` |

Use only observed outputs. Keep `NOT_RUN`, `FAIL`, `UNKNOWN`, and `BLOCKED` explicit. Never retrofit evidence after the fact without marking the actual observation time.
