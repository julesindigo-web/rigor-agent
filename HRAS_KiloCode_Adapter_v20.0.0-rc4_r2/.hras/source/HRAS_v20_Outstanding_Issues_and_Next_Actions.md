# HRAS v20 Outstanding Issues and Next Actions

## Required before deployment / release

| ID | Required action | Dependency | Closure evidence |
|---|---|---|---|
| NEXT-001 | Implement trusted authorization broker validating signature bytes, identity, audience, scope, expiry, revocation, replay and resource binding. | Key registry / identity provider / policy owner | Negative and positive tests plus signed audit evidence in a pinned runtime. |
| NEXT-002 | Implement durable state machine and atomic operation ledger with idempotency/read-back and recovery after restart. | Selected tool/provider contracts and persistence guarantees | Fault-injection test proving timeout-after-effect does not duplicate side effect. |
| NEXT-003 | Provision isolated test fixtures and freeze thresholds/oracles, then execute all release-blocking cases. | Runtime build, model/provider version, tools and fixture data | Per-test/per-trial results and evidence IDs; all mandatory gates have valid results. |
| NEXT-004 | Independently review semantic requirement-to-test links and release-blocking classifications. | QA/security/product owners | Signed review decisions recorded in trace registry and threshold manifest. |
| NEXT-005 | Replace bounded corpus JCS helper with a fully conforming, version-pinned RFC 8785 implementation. | Selected maintained library/toolchain | Published test vectors pass, duplicate keys reject, hash reproducibility verified across two implementations. |
| NEXT-006 | Make release controller and deployment adapter consume spec/schema/policy/validator/test hashes from a signed manifest. | CI/CD and trusted deployment control | Identity mismatch mutation tests block deployment/release statuses. |
| NEXT-007 | Implement actual logging/evidence sink, secret redaction, access controls, retention/deletion and audit integrity. | Storage provider and privacy owner | Privacy-isolation, deletion, tampering and incident investigation tests. |

## Recommended before deployment

| ID | Action | Closure evidence |
|---|---|---|
| NEXT-008 | Run security red-team tests across document, browser, source files, build logs, memory, image metadata and tool responses. | Multi-source prompt-injection report; no unauthorized action across approved repeated trials. |
| NEXT-009 | Conduct independent scoring and specification review. | Signed audit report with disposition and verified source citations. |
| NEXT-010 | Render all Markdown and JSON artifacts in target UI/build pipeline. | Link checker, JSON parser/schema run, Markdown render screenshot or CI artifact. |

## Suitable for later optimization

Improve throughput/load budgets, cost-aware planning, model comparison and domain-specific UX benchmarks after baseline conformance and security release gates pass.

## Accepted limitations

A single natural-language specification cannot guarantee perfect outcomes. v20 provides a candidate contract and reference primitives; production-grade status depends on the target model, external controller, tools, data, infrastructure and empirical evaluation. No runtime behavior has been certified in this package.


Fixture integrity semantics: `fixture_declaration_hash` identifies the declared fixture; `fixture_hash` remains null until actual fixture materialization and content hashing. `environment_id` remains null until a real environment instance is provisioned. All current cases remain NOT_RUN.
