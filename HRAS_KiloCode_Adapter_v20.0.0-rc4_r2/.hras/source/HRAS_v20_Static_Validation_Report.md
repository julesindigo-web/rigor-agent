# HRAS v20 Static Validation Report

**Version:** `20.0.0-rc4`
**Status:** `PASS`
**Assertions:** 83/83 passed; 0 failed.
**Observed at (UTC):** 2026-10-28T22:06:01.264262+00:00

**Scope limit:** this validates static artifact structure, schemas, module I/O contracts, policy references and traceability. It does not execute the target LLM, production authorization broker, durable operation store, real tool adapters, isolated domain oracle, or deployment target. Runtime test cases retain their actual source statuses.

| Assertion | Status | Details |
|---|---|---|
| schema-meta-schema-valid | PASS | JSON Schema Draft 2020-12 |
| all-local-refs-resolve | PASS | [] |
| module-output-contracts-present | PASS | [] |
| module-io-registry-valid | PASS | [] |
| artifact-status-enums-explicit-and-separated | PASS |  |
| inconclusive-result-aggregation-fail-closed | PASS |  |
| performance-metric-referential-integrity | PASS |  |
| yaml-examples-explicitly-non-normative | PASS |  |
| intent-record-and-source-reference-contracts-defined | PASS |  |
| canonical-evidence-research-subroute | PASS | ['REQUIREMENTS', 'ARCHITECTURE', 'IMPLEMENTATION', 'TESTING', 'SECURITY', 'PERFORMANCE', 'ACCESSIBILITY', 'DEPLOYMENT', 'MIGRATION', 'INCIDENT_TRIAGE', 'INCIDENT_CONTAINMENT', 'RECOVERY', 'POSTMORTEM', 'DOCUMENTATION', ' |
| version-identity-consistent | PASS | [] |
| schema-registry-freeze-status-is-explicit-and-bound | PASS | version=OPEN_NOT_FROZEN; manifest=OPEN_NOT_FROZEN |
| test-count-derived | PASS | declared=139 actual=139 |
| requirement-count-derived | PASS | registry_count=53 rendered_count=53 |
| test-IDs-unique | PASS | count=139 |
| all-requirements-rendered | PASS |  |
| all-requirements-have-test-or-disposition | PASS |  |
| bidirectional-trace-valid | PASS | [] |
| bidirectional-trace-mutations-detected | PASS |  |
| all-case-refs-known | PASS |  |
| canonical-policy-IDs | PASS |  |
| case-hashes-recomputed | PASS |  |
| package-file-hashes-sizes-and-checksum-coverage | PASS | [] |
| all-cases-have-typed-oracle | PASS |  |
| oracle-required-field-mutation-detected | PASS |  |
| pass-criteria-distinct-from-description | PASS |  |
| oracle-assertions-linked-to-pass-and-fail-criteria | PASS |  |
| case-specific-failure-conditions | PASS |  |
| observation-envelope-provenance-assertions | PASS |  |
| fixture-hash-semantics-explicit | PASS |  |
| environment-profiles-declared | PASS |  |
| adversarial-trials-bounded-and-repeated | PASS |  |
| source-and-case-trace-projections-equal | PASS |  |
| pass-for-unmaterialized-fixture-rejected | PASS |  |
| observation-envelope-validates | PASS |  |
| observation-envelope-missing-provenance-rejected | PASS |  |
| unmaterialized-observation-cannot-pass-provenance-controller | PASS |  |
| materialized-matching-observation-provenance-accepted | PASS |  |
| materialized-mismatched-fixture-hash-rejected | PASS |  |
| run-manifest-config-mismatch-rejected | PASS |  |
| restricted-actions-present | PASS |  |
| policy-hash-contract-explicit | PASS |  |
| all-trial-policies-bounded | PASS |  |
| no-test-claims-execution | PASS |  |
| fixtures-not-pretended-materialized | PASS |  |
| main-workflow-failure-blocks | PASS |  |
| all-BLOCKER-cases-block | PASS |  |
| nonblocking-HIGH-documented | PASS |  |
| general-and-incident-modes | PASS |  |
| tool-action-states-present | PASS |  |
| new-statuses-present | PASS |  |
| validation-status-has-UNKNOWN | PASS |  |
| schema-conditionals-present | PASS |  |
| authorization-crypto-evidence-required-for-allow | PASS |  |
| exception-independent-approval-enforced | PASS |  |
| non-waivable-condition-registry-explicit | PASS |  |
| unknown-outcome-cannot-submit | PASS |  |
| tool-action-skip-is-rejected | PASS |  |
| canonical-workflow-registry-valid | PASS | [] |
| canonical-workflow-covers-all-modes | PASS |  |
| workflow-retry-bounded-and-strategy-pivoted | PASS |  |
| retry-policy-explicitly-enforces-no-progress-and-repeated-failure | PASS |  |
| north-star-subrequirement-map-valid-and-canonical | PASS | [] |
| north-star-map-references-existing-requirements-and-tests | PASS |  |
| workflow-coverage-report-valid-and-current | PASS | [] |
| workflow-retry-edges-fail-closed-on-cycle-mutation | PASS |  |
| annex-b-policy-registry-hash-bound | PASS |  |
| new-modules-registered | PASS |  |
| release-schema-requires-evidence | PASS |  |
| lifecycle-operability-crossfield-invariants | PASS |  |
| security-posture-pass-requires-independent-review | PASS |  |
| lifecycle-security-semantic-validators-wired | PASS |  |
| invalid-route-enum-rejected | PASS |  |
| ALLOW-without-verified-signature-rejected | PASS |  |
| duplicate-json-keys-rejected | PASS |  |
| self-approved-exception-rejected | PASS |  |
| all-test-cases-schema-valid | PASS | [] |
| embedded-schema-equals-companion | PASS |  |
| annex-order | PASS |  |
| INP-threshold-corrected | PASS |  |
| obsolete-T-011-not-used | PASS |  |
| no-stale-v19-test-count-claims | PASS |  |
| quality-score-weights-sum-100 | PASS | weights=[8, 10, 10, 10, 10, 10, 8, 8, 5, 5, 8, 4, 4]; total=100 |
