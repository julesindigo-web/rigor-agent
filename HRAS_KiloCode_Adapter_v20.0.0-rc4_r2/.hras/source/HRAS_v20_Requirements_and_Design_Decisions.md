# HRAS v20 — Requirement Inventory and Design Decisions

## Executive context
The current intended mission is autonomous end-to-end software engineering from a short idea through a production-grade artifact, while the model remains subordinate to trusted authorization, state, evidence and release controls. This is a candidate specification package, not a deployed/verified agent.

## Requirement inventory

| Requirement ID | Priority | Source | Intended treatment | Status |
|---|---|---|---|---|
| HRAS-R001 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Short full-product ideas enter autonomous idea-to-production flow | Proposed mapping; owner review required |
| HRAS-R002 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | User intent and hard constraints remain traceable | Proposed mapping; owner review required |
| HRAS-R003 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Requirements have stable IDs and testable acceptance criteria | Proposed mapping; owner review required |
| HRAS-R004 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Architecture defines interfaces, trust boundaries, risks and trade-offs | Proposed mapping; owner review required |
| HRAS-R005 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Implementation continues through validation when requested and permitted | Proposed mapping; owner review required |
| HRAS-R006 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | In-scope UI controls and workflows are genuinely wired | Proposed mapping; owner review required |
| HRAS-R007 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | QualityProfile is domain/risk-specific | Proposed mapping; owner review required |
| HRAS-R008 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Hard gates cannot be offset by average score | Proposed mapping; owner review required |
| HRAS-R009 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | UI/UX and visual claims require appropriate evidence | Proposed mapping; owner review required |
| HRAS-R010 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Accessibility checks include manual review when applicable | Proposed mapping; owner review required |
| HRAS-R011 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | User-facing copy and assets are truthful and license-aware | Proposed mapping; owner review required |
| HRAS-R012 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Web performance evidence distinguishes lab and field measurements | Proposed mapping; owner review required |
| HRAS-R013 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Authentication, authorization, data protection and threat controls are risk-based | Proposed mapping; owner review required |
| HRAS-R014 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | External side effects require trusted scoped authorization | Proposed mapping; owner review required |
| HRAS-R015 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Secret use is separated from secret disclosure | Proposed mapping; owner review required |
| HRAS-R016 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Untrusted content cannot change policy or authorize tools | Proposed mapping; owner review required |
| HRAS-R017 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Tool results and execution claims are truthful and traceable | Proposed mapping; owner review required |
| HRAS-R018 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Tests are meaningful and not tampered with to pass | Proposed mapping; owner review required |
| HRAS-R019 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Required unexecuted tests block unsupported status claims | Proposed mapping; owner review required |
| HRAS-R020 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Production readiness and actual deployment are distinct | Proposed mapping; owner review required |
| HRAS-R021 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Operational readiness includes observability and recovery appropriate to risk | Proposed mapping; owner review required |
| HRAS-R022 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Memory is scoped, privacy-aware and policy-inert | Proposed mapping; owner review required |
| HRAS-R023 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Policy changes require controlled approval and regression tests | Proposed mapping; owner review required |
| HRAS-R024 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Concurrent memory/evidence changes preserve conflicts and provenance | Proposed mapping; owner review required |
| HRAS-R025 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Resource use and retries are bounded by consistent aggregate budgets | Proposed mapping; owner review required |
| HRAS-R026 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Context compaction and resume preserve authorization, evidence and counters | Proposed mapping; owner review required |
| HRAS-R027 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Parallel execution is isolated and integrated work is revalidated | Proposed mapping; owner review required |
| HRAS-R028 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Agent-level evaluation is separate from product testing | Proposed mapping; owner review required |
| HRAS-R029 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Release-critical authorization/evidence failures block regardless of average score | Proposed mapping; owner review required |
| HRAS-R030 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | State machine enforces preconditions for terminal statuses | Proposed mapping; owner review required |
| HRAS-R031 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Masterpiece status requires applicable gates and evidence | Proposed mapping; owner review required |
| HRAS-R032 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | The final validator detects missing modules, invalid enums and gate bindings | Proposed mapping; owner review required |
| HRAS-R033 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Evidence freshness follows the final artifact/code state | Proposed mapping; owner review required |
| HRAS-R034 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Product handoff names changes, results, assumptions and gaps | Proposed mapping; owner review required |
| HRAS-R035 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Version identity and release claims are consistent and governed | Proposed mapping; owner review required |
| HRAS-R036 | CONDITIONAL | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | External standards are versioned and not treated as automatic certification | Proposed mapping; owner review required |
| HRAS-R037 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Data migration handles integrity, backup and recovery | Proposed mapping; owner review required |
| HRAS-R038 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Domain-specific AI products use representative safety/quality evaluations | Proposed mapping; owner review required |
| HRAS-R039 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Product status reflects best feasible work without concealing blockers | Proposed mapping; owner review required |
| HRAS-R040 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Static consistency and runtime conformance are separately reported | Proposed mapping; owner review required |
| HRAS-R041 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Core interface contracts use complete, versioned machine-readable schemas | Proposed mapping; owner review required |
| HRAS-R042 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | External side effects reconcile unknown outcomes before retry | Proposed mapping; owner review required |
| HRAS-R043 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Primary routes are unique and route-specific state paths are enforced | Proposed mapping; owner review required |
| HRAS-R044 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Non-waivable gates and approved exceptions have distinct semantics | Proposed mapping; owner review required |
| HRAS-R045 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | State transitions and delivery status are separate, typed, and enforced | Proposed mapping; owner review required |
| HRAS-R046 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Test suite and run report require per-case metadata, result, evidence, and identity | Proposed mapping; owner review required |
| HRAS-R047 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Evidence is bound to final artifact identity and profile-based freshness/invalidation | Proposed mapping; owner review required |
| HRAS-R048 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | QualityProfile applicability and threshold changes cannot self-waive gates | Proposed mapping; owner review required |
| HRAS-R049 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Memory deletion/retention is reconciled with integrity-preserving audit history | Proposed mapping; owner review required |
| HRAS-R050 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Release requires identical active spec/schema/validator/test identity | Proposed mapping; owner review required |
| HRAS-R051 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Traceability verification assesses semantic mapping, not ID existence only | Proposed mapping; owner review required |
| HRAS-R052 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Issue severity and release-blocking decisions use a canonical rule | Proposed mapping; owner review required |
| HRAS-R053 | MUST | HRAS v19 §27 legacy requirement, semantic link re-proposed for v20 | Primary mode and final delivery status have an explicit decision oracle | Proposed mapping; owner review required |

## Design decisions

| ID | Decision | Rationale / defect addressed | Benefit | Trade-off / remaining proof |
|---|---|---|---|---|
| DD-001 | Schema-first enum/state/status contracts with `allOf` invariants | Prevent free-string mode/state/status drift and express conditional requirements | Validator can reject invalid combinations before execution | Cross-field trust/identity facts still need controller checks |
| DD-002 | One policy registry | Remove divergent non-waivable/restricted-action lists | Single hash-pinned source for policy enforcement | Registry lifecycle/approval must be operated by an owner |
| DD-003 | Authorization decision contains cryptographic evidence references | A boolean cannot prove signature verification | Enables evidence-linked signature validation | Real key registry/cryptographic verifier is an external adapter |
| DD-004 | Separate proposer and approver plus independence evidence | Prevent self-approval | Independently testable review separation | Identity and roles require trusted provider integration |
| DD-005 | TOOL_ACTION execution/reconciliation states and operation state machine | Address timeout-after-side-effect duplicate submissions | Prevents blind retries and exposes unknown outcomes | Provider idempotency/read-back may not exist |
| DD-006 | Canonical release statuses include deployed/action unverified and reconciliation required | Prevent status gaps from forcing false success/false failure | Truthful reporting of partial/external outcomes | Requires controller enforcement and observed side-effect proof |
| DD-007 | Explicit GENERAL_ASSISTANCE and INCIDENT_RESPONSE modes | General Q&A and incident workflows were outside prior primary-mode enum | Better routing and scope-specific gates | Incident actions still require authorization and incident owner policy |
| DD-008 | Typed oracle assertions + repeated trial policy | Separate descriptive expected behavior from observable pass/fail | More discriminating conformance evidence | Most fixtures remain unmaterialized and thresholds need approval |
| DD-009 | Two-way generated traceability and mutation tests | Catch missing reverse edges and unknown IDs | Structural coverage gaps become detectable | Semantic mapping still requires independent sign-off |
| DD-010 | RFC 8785/JCS plus strict duplicate-key parser | Avoid noncanonical hashes and ambiguous duplicate keys | Reproducible case hash identity | Reference helper rejects floats; production should use fully tested JCS library |
| DD-011 | Restricted-action policy | Cover force push/history rewrite, global/sudo, third-party upload, disabling security | Clear least-privilege default | Owner approval and environment capabilities must be configured |
| DD-012 | Compiled core prompt plus external controller contract | Full spec is too large to be a raw system prompt | Clear deployment partition: prompt, contracts, policy, controller | The core prompt alone cannot enforce trusted boundaries |
| DD-013 | Separate static validation from runtime evidence | Address prior score/pass-count assurance issue | Prevent structural PASS being called runtime conformance | Runtime suite still needs actual model/tool/backend |
| DD-014 | Normalized quality score with weights totaling exactly 100 | Avoid aggregation inflation from invalid weight sum | Reproducible arithmetic | Judgment remains provisional and not independent certification |

### Candidate design addition — artifact lifecycle and intent contracts (ADR D-03 / D-01; approval pending)

- Artifact lifecycle is isolated in `ArtifactLifecycleStatus`: `DRAFT`, `IN_PROGRESS`, `REVIEW_READY`, `VALIDATED`, `SUPERSEDED`, `CANCELLED`. This is a proposed shared family for the 14 artifact envelope definitions because these fields own artifact lifecycle; it is deliberately not reused for module/test/workflow/validation/delivery statuses.
- Allowed transitions are in the schema annotation and controller: DRAFT→IN_PROGRESS/CANCELLED; IN_PROGRESS→REVIEW_READY/CANCELLED; REVIEW_READY→IN_PROGRESS/VALIDATED/CANCELLED; VALIDATED→SUPERSEDED; SUPERSEDED/CANCELLED are terminal. A semantic owner review remains required before any governance ratification.
- `INTENT` consumes `IntentCaptureRequest` and emits internal `IntentRecord`; `IntentRecordArtifact.payload` is typed as `IntentRecord`. `requirement_refs` describes coverage against active HRAS-R IDs; `source_requirement_refs` describes provenance and uses explicit source/version qualification when the active spec is not the origin.
- North Star impact check: improves auditability and prevents status coercion; protects existing requirement IDs, fail-closed evidence and route limits; does not expand autonomous scope or authorize external effects; no release gate is relaxed; new evidence required is lifecycle mutation coverage, typed payload positive/negative validation and producer/consumer registry validation.

## RC4 follow-on hardening note (candidate-only, not a production certification)

The reference controller was hardened against two previously reproduced status/authorization errors:

1. `authorize_decision` accepts an authorization callback only if it returns the literal boolean `True`; truthy strings, integers, collections, `None`, and callback exceptions do not authorize. The helper also fails closed for incomplete decision evidence, malformed SHA-256 payload digests, empty scope, malformed/naive temporal values, future-issued grants, and expired/non-positive-lifetime grants.
2. `allowed_delivery_status` rejects `DEPLOYED_AND_VERIFIED` unless `deployment_observed is True`, a provisional evidence object carries deployment/target/artifact/environment/authorization/observer identity, post-deploy health and smoke statuses are `PASS`, expected artifact/environment/target identities match the validation record, the observation timestamp is timezone-aware and not in the future, and a trusted verification callback returns the literal boolean `True`. Falsey, truthy-but-non-boolean, throwing, missing, or identity-mismatched verifier/evidence inputs fail closed.

These are **reference-controller invariants**, not an implementation of the missing production authorization broker, signed deployment evidence verifier, or durable operation state. The deployment evidence object is intentionally marked **provisional, not a canonical machine-readable contract**, because MR-06 is awaiting D-05/D-06 decisions and a reconciled schema/report contract. Regression tests establish only the helper behavior, not the trustworthiness of any real callback or deployment observer. MR-05 and MR-06 remain open because their complete closure evidence, dependent decisions, branch-specific schema contract, policy-bound freshness, trusted integrations, live target health/smoke evidence and independent verification are not yet satisfied. The patch does not assign policy semantics for exception waivers and does not modify the schema registry.
