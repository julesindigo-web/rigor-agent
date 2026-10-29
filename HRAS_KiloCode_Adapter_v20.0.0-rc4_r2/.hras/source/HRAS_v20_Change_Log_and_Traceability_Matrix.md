# HRAS v20 Change Log and Traceability Matrix

| ID | v19 problem or objective | v20 change | Location | Verification | Status |
|---|---|---|---|---|---|
| CHG-001 | Free-form mode/state/status fields | Typed enums for 13 primary modes, 23 workflow states and 20 delivery statuses | Canonical spec §18; schemas RouteDecision/StateTransition/DeliveryManifest | Meta-schema + negative enum tests | Static candidate; runtime open |
| CHG-002 | Authorization signature represented only by booleans | Require signature evidence reference, algorithm, key, signed payload hash, verifier and grant ID for ALLOW | Schema AuthorizationDecision; §4.4; Annex C | Conditional schema negative test; trusted verifier test not run | Structural correction |
| CHG-003 | Exception approver not distinguishable from proposer | Add proposer_id, approver independence evidence and policy version; controller rejects self-approval | ExceptionRecord schema; §19.1 | Schema and controller mutation check | Runtime identity policy open |
| CHG-004 | Retry after unknown outcome can duplicate side effects | Formal operation state and `must_not_resubmit` rule | §11.4, §16.3, §18.4; OperationRecord schema | RES-006, AC-T-002, controller operation helper | Runtime provider integration open |
| CHG-005 | Non-waivable/action policies duplicated or too narrow | Add one Policy Registry with non-waivable, restricted actions, blocking and hash policy | HRAS_v20_Policy_Registry.json; §§4.3,10.6,19.1; Annex B | Hash identity / policy references / negative tests | Owner approval open |
| CHG-006 | Traceability one-direction only | Generate requirement/test projections from one case registry; include mutations on each direction | §27; HRAS_v20_Requirement_Traceability.json | Bidirectional check and mutation tests | Semantic review open |
| CHG-007 | Expected behavior repeated as oracle | Add typed assertion ID, target, operator, expected value, evidence path, impact, and trial policy | §17.3; TestCaseSpec / OracleAssertion / TrialPolicy | Schema and oracle mutation checks | Fixtures unmaterialized |
| CHG-008 | 122-count/report hardcoding and stale status claims | Counts are computed from source records; all current cases remain NOT_RUN | Static validator/report/manifest | Dynamic count and status consistency checks | Static run only |
| CHG-009 | General Q&A / incident path missing | Add GENERAL_ASSISTANCE and INCIDENT_RESPONSE modes | §5, §18; RouteDecision schema | Enum/path checks, GEN-001/INC-001 | Runtime route test open |
| CHG-010 | JCS and duplicate-key ambiguity | Require RFC 8785 and strict parse; built-in helper fails closed on floating values | §17.3; HRAS-POL-HASH-001; reference controller | Duplicate-key and bounded-corpus hash tests | Full RFC vectors still required |
| CHG-011 | Compiled prompt/controller absent | Provide compact prompt core and reference controller interfaces | HRAS_v20_Compiled_Core_Prompt.md; HRAS_v20_reference_controller.py | Syntax checks and API smoke tests | Not production security boundary |
| CHG-012 | Score weights could be invalid and review self-referential | Normalize weights to exactly 100; label score provisional and require external review | Final Quality Assessment | Weight sum assertion and arithmetic check | Independent score open |

## Requirement coverage

The canonical trace registry contains 53 requirements and 139 cases. Every requirement presently maps to at least one case, and each case maps to valid requirements. Links are marked `PROPOSED` until semantic review is independently approved; edge presence is not proof of semantic correctness or successful execution.

| CHG-013 | Fixture declaration hash confused with materialized fixture identity; weak run provenance binding | Separate `fixture_declaration_hash` from nullable actual `fixture_hash`; add `TestObservationEnvelope` and run-manifest identity binding | §17.3; schemas `TestCaseSpec`, `TestObservationEnvelope`, `ConformanceRunReport`; reference controller | Null-hash negative test, schema validation, case-hash/fixture identity positive and mismatch mutations | Static candidate passes; real adapter/runtime evidence open |

## RC4 follow-on hardening — 2026-10-29 (candidate-only; no promotion)

| Change ID | Area | Change | Evidence | Disposition |
|---|---|---|---|---|
| RC4-HARDEN-001 | Authorization helper | Verifier callback is accepted only when the return value is the literal boolean `True`; arbitrary truthy values such as `"DENY"`, `1`, or `{}` no longer authorize. Mandatory evidence fields, scope, resource limits, digest format, and grant time bounds fail closed. | `tests/test_rc4_plan_closure.py`; follow-on regression execution record | Local reference-controller hardening only; production authorization broker not present. MR-05 remains `AWAITING-DECISION(D-05)` and is not closed. |
| RC4-HARDEN-002 | Delivery state | `DEPLOYED_AND_VERIFIED` requires `deployment_observed is True`; false, null, integer, or string substitutes are rejected. | `tests/test_rc4_plan_closure.py`; follow-on regression execution record | Partial invariant hardening only; target identity, trusted deployment evidence, post-deploy health/smoke, signed manifest binding, and D-05/D-06-dependent schema/controller closure remain open. MR-06 remains `AWAITING-DECISION(D-05)`. |

**Authority note:** No owner decision was inferred from the user's request to continue remediation. D-02, D-05, and D-12 remain pending owner action; no schema changes dependent on those unresolved decisions were made in this follow-on slice. `rc3` remains unchanged. No remote push, deploy, waiver, or promotion occurred.
