# HRAS Release Gate Review

**Candidate identity:** spec/version/hash, schema hash, code/artifact hash, config hash, dependency lock hash, runtime/model/provider/tool build, target environment  
**Review date:** `YYYY-MM-DD`  
**Independent reviewers:** `REQUIRED`

| Gate | Applicability | State (`PASS/FAIL/UNKNOWN/NOT_RUN/BLOCKED`) | Evidence ID/hash | Reviewer | Residual risk / closure requirement |
|---|---|---|---|---|---|
| Schema/package identity | REQUIRED | UNKNOWN | none | TBD | validate exact candidate |
| Required regression tests | REQUIRED | NOT_RUN | none | TBD | run immutable suite |
| Runtime / E2E hard gates | based on risk | BLOCKED | none | TBD | materialize fixtures and target adapters |
| Trusted authorization | REQUIRED for external effects | BLOCKED | none | TBD | independent broker verification |
| Durable operation ledger/idempotency | REQUIRED for external effects | BLOCKED | none | TBD | failure-injection proof |
| Security/privacy review | risk-based | UNKNOWN | none | TBD | independent review |
| Rollback/recovery | REQUIRED for relevant changes | UNKNOWN | none | TBD | rehearsal evidence |

Do not conclude production readiness with any applicable mandatory gate that is `FAIL`, `UNKNOWN`, `NOT_RUN`, or `BLOCKED`.
