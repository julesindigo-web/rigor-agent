# HRAS v20 Refinement Report

## 1. Executive assessment

HRAS v20.0.0-rc4 is the controlled candidate derived from the immutable v20.0.0-rc3 baseline. The original refinement narrative below records the rc3 source history; candidate-specific remediation status and current evidence are recorded in the rc4 work/evidence ledger. It adds typed state/mode/delivery enums and conditional schema rules, signature evidence references, independent exception proposal/approval fields, a canonical action and non-waivable policy registry, a separate operation reconciliation state machine, bidirectional requirement/test projections, typed test oracles and trial policies, a compiled core prompt, and reference controller primitives.

The current rc4 package contains 53 requirements, 63 JSON Schema `$defs`, 139 test cases and 695 typed oracle assertions (five per case); these inventory counts are derived in `HRAS_v20_Package_Manifest.json`, not maintained as independent sources. All 139 cases remain `NOT_RUN`; fixtures are `UNMATERIALIZED`, actual `fixture_hash` and `environment_id` are null, and only `fixture_declaration_hash` is populated. Static checks validate artifact structure and cross-references; they do not prove actual LLM behavior, authorization cryptography, remote side-effect idempotency, or deployment readiness. Earlier source-history mentions of 51 definitions refer to a prior snapshot and are superseded for rc4.

## 2. Source and assumptions

- Source baseline: HRAS v19 canonical specification, schema registry, and 122-case v19 baseline test registry in the active workspace.
- Adversarial input: user-provided review enumerating schema, traceability, oracle, state/status, action policy, hash, validator, scoring, and editorial defects.
- Assumption: v19 requirement IDs and stated intent remain compatible; substantial route/status additions are new normative requirements, documented as v20 changes.
- Unknown: target runtime, actual model/provider, tool adapters, identity and cryptographic services, memory backend, CI/CD and release environment.

## 3. Changes implemented

1. Strengthened schema enums/conditionals, cryptographic references and exception independence evidence.
2. Added GENERAL_ASSISTANCE and INCIDENT_RESPONSE modes and expanded TOOL_ACTION state/delivery statuses.
3. Centralized non-waivable, restricted-action, release-blocking and hash policies in a versioned JSON policy artifact.
4. Reworked tests from a prose pass oracle to 695 typed assertions, case-specific predicates, provenance assertions, explicit environment profiles, fixture declaration-vs-content hash semantics, policy rationale and per-trial plans.
5. Generated both traceability views from the test case registry, with bidirectional and mutation checks.
6. Replaced prior NFC/code-point hash language with RFC 8785 requirements and duplicate-key rejection; the included reference helper fails closed on float values pending use of a fully conforming library.
7. Corrected the INP boundary to ≤ 200 ms; fixed Annex order and AC-T-011 ID; added manifest/hash provenance and compiled core prompt.
8. Added a typed `TestObservationEnvelope`, signed run-manifest identity binding contract, and conditional rule that forbids PASS until fixture/environment/oracle/threshold are materialized and frozen.

## 4. Required deliverables

1. Executive assessment: this section.
2. Requirement inventory: `HRAS_v20_Requirements_and_Design_Decisions.md`.
3. Audit and defect register: `HRAS_v20_Audit_and_Defect_Register.md`.
4. Design decisions: same Requirements and Design Decisions document.
5. Full copy-ready specification: `HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md`.
6. Change log/traceability: `HRAS_v20_Change_Log_and_Traceability_Matrix.md` plus `HRAS_v20_Requirement_Traceability.json`.
7. Test suite: human-readable and machine-readable 139-case suite.
8. Quality assessment: `HRAS_v20_Final_Quality_Assessment.md`.
9. Next actions: `HRAS_v20_Outstanding_Issues_and_Next_Actions.md`.

## 5. Design trade-offs and limitations

A complete schema registry and 139 test specifications materially increase artifact size, but move policy and validation out of implicit LLM prose. The compiled prompt is intentionally compact; it cannot replace external enforcement. Semantic mappings are proposed and need an independent owner review. The reference controller shows the intended contract but is not a production security boundary.

## 6. Status

**Candidate v20.0.0-rc4 / implementation and independent review required.** Do not mark `PRODUCTION_READY`, `DEPLOYED_AND_VERIFIED`, or `MASTERPIECE_VERIFIED` until trusted controller integration and runtime conformance evidence exist.


## 7. RC4 candidate addendum (2026-10-28)

The figures and capability descriptions in the historical sections above describe the rc3 source state and are not evidence that rc4 is conformance-tested. For the rc4 worktree, the canonical remediation plan and per-MR closure ledger govern current status. Static validation is reproduced only when the exact command, exit code, input hashes and generated report are recorded; runtime cases remain `NOT_RUN` until their fixtures, environments and oracles are materialized and executed. The candidate remains `CANDIDATE_NOT_PRODUCTION_READY` until every non-waivable P0 gate and applicable P1 prerequisite is independently closed.
