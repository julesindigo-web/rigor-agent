# HRAS in Kilo Code — rigorous implementation roadmap


> **Gap-ID authority (R2):** IDs in the tables below are legacy, document-local references. The canonical, cross-document identity and all legacy mappings are in [`GAP_REGISTRY.json`](GAP_REGISTRY.json). Never join, close, or aggregate gaps by legacy `KG-xxx`/`IK-xx` alone. Registry mapping is not closure evidence.

## Decision

Use Kilo as the model/tool orchestration and development interface. Use HRAS source as the normative process/contract reference. Keep authorization, durable operation state, canonical status transitions, validation and deployment authority in a trusted external controller/CI/CD boundary. Do not try to emulate that control plane in prompt text.

## High-priority gap register

| ID | Priority | Finding | Impact | Required completion evidence |
|---|---|---|---|---|
| KG-001 | P0 | Kilo agent/rules are not the HRAS trusted controller | Prompt-only authority can be bypassed by instruction conflict, tools, plugins or alternate paths | Independent authorization broker; signed identity/policy; scope/audience/expiry/revocation/replay/resource validation; negative and positive tests |
| KG-002 | P0 | Upstream runtime conformance is not executed | Cannot claim HRAS runtime behavior or release readiness | Materialize and hash all 139 fixtures, provision environment IDs, freeze oracles/thresholds, execute per-case/per-trial reports with actual traces |
| KG-003 | P0 | Tool test surface is not observable in upstream corpus | Security/egress tests may be vacuous | Complete `allowed_tools`, distinguish `none` vs unspecified, bind `tools_adapter_ref`, instrument provider/egress and prove the boundary is reached |
| KG-004 | P0 | Durable operation record, idempotency and outcome reconciliation absent | Timeout-after-effect can duplicate external operations or create unknown state | Durable atomic ledger, provider operation IDs, idempotency semantics, authoritative read-back and restart/timeout fault-injection tests |
| KG-005 | P1 | JCS support in source helper is bounded to current integer corpus | Hashes may diverge for production JSON values | Integrate pinned RFC 8785 implementation, duplicate-key rejection, published vectors and independent cross-implementation checks |
| KG-006 | P1 | Schema registry remains open and trace links need independent semantic approval | Schema/interface changes or false coverage can escape review | Freeze version-pinned schemas after prerequisites; independent owner/security/QA semantic review with signed decisions |
| KG-007 | P1 | Kilo model/build/config identity not pinned in runs | Reproducibility and drift diagnosis weak | Record exact Kilo build, provider/model/version, prompt/config hashes, MCP/tool schemas, platform, temperature/variant, test suite and runtime environment per run |
| KG-008 | P1 | Permission rules and command denies are defense-in-depth only | Alternate command paths can bypass prompt-level assumptions | OS/container isolation, read-only mounts, egress allowlist, separate credentials, branch protection, deployment identity policy, external broker |
| KG-009 | P1 | Prompt-injection/adversarial evaluation not yet empirically closed | Files, web/MCP outputs or generated artifacts may attempt to override authority | Repeated adversarial trials across repository, web, issue, logs, image metadata, dependencies and MCP output; instrumented action outcomes |
| KG-010 | P1 | No target-specific product/UX/engineering benchmark approval | “Masterpiece” remains aspirational without a threshold | Domain-specific acceptance rubric, independent oracle/reviewer, blind comparator where relevant, approved thresholds and evidence freshness policy |
| KG-011 | P2 | Source vision clause semantics are pending independent review | Traceability count may be syntactic not semantic | Map every vision clause to requirements, tests or approved N/A; owner-signed exception list and v19 lineage evidence when claimed |
| KG-012 | P2 | HRAS version record uses candidate baseline rc3 while spec header says parent baseline v18.0.0-rc1 | Could be packaging baseline vs normative lineage; reader ambiguity | Clarify in canonical metadata whether these represent distinct concepts; keep both if intentional and documented, then test identity consistency |

## Architecture layers

1. **Kilo UX/orchestration:** primary `hras` agent; bounded subagents; explicit slash commands; on-demand skills; always-loaded rules.
2. **Local development boundary:** workspace-scoped edits, ask/deny tools, disposable branches/worktrees, command allowlists, no ambient production credentials.
3. **Deterministic validation:** schemas, source manifest/hash checks, linters, unit/integration tests, artifact-bound proof ledger, CI checks.
4. **Trusted action broker:** authenticated caller, signed authorization envelope, resource binding, audience/scope/expiry/revocation/replay validation, policy decision, atomic operation journal, provider idempotency and read-back reconciliation.
5. **Release controller:** verifies immutable manifest identities, CI test evidence and thresholds; owns status transitions; blocks `PRODUCTION_READY`/`DEPLOYED_AND_VERIFIED`/`MASTERPIECE_VERIFIED` unless all applicable gates are evidenced.
6. **Evidence/data governance:** structured append-only evidence sink, redaction, access control, retention/deletion controls, integrity checks, audit trails and privacy review.
7. **Agent evaluation:** frozen suite and fixtures, per-case observations, independent oracles, repeated stochastic/adversarial trials, model/tool/config version pinning and regression trend analysis.

## Staged rollout

### Stage 0 — static package

- [ ] Verify source hashes and package manifest.
- [ ] Validate JSON config, agent/skill/command frontmatter and all file references.
- [ ] Confirm Kilo version and agent discovery in isolated workspace.

### Stage 1 — read-only evaluation

- [ ] Test `hras-audit`, `hras-security-reviewer`, `hras-evidence-reviewer` on a known vulnerable toy repo.
- [ ] Verify no file changes and that source locations/counterevidence are accurate.
- [ ] Test prompt injection in source comments, docs, tool output and web text.
- [ ] Verify evidence labeling and no fabricated test/permission claims.

### Stage 2 — local controlled edits

- [ ] Use a disposable branch/worktree and toy project.
- [ ] Test regression-first remediation (must fail before/fix, pass after).
- [ ] Record exact commands, exit codes, artifacts, changed paths and rollback evidence.
- [ ] Test shell allow/ask/deny rules including command chaining and alternate tools.
- [ ] Confirm edits to `AGENTS.md`, config files, workflows and security policy receive the expected protection/approval.

### Stage 3 — runtime boundary integration

- [ ] Implement trusted authorization broker; never accept model-generated authorization flags.
- [ ] Implement durable OperationRecord state machine and provider read-back/idempotency.
- [ ] Instrument actual tool/egress/provider boundaries and complete `allowed_tools`/`tools_adapter_ref` in all required tests.
- [ ] Materialize/hash every required fixture and bind environment/runtime/model/tool versions.
- [ ] Run 139 cases; report every case and each independent trial; close all release blockers.

### Stage 4 — release candidate

- [ ] Freeze/approve schema, policy registry, suite, thresholds and active manifest.
- [ ] Independent security, QA, product and operations review.
- [ ] Integration/E2E/failure-injection, rollback rehearsal, privacy/logging tests.
- [ ] Verify final artifact hashes and evidence freshness.
- [ ] Release controller—not model output—computes allowed status.

## Acceptance gates for the Kilo adapter itself

| Gate | Command/evidence | Expected result |
|---|---|---|
| Adapter structure and config | `python scripts/validate_adapter.py` | Exit 0, no missing paths or hash mismatch |
| Adapter tests | `python -m unittest discover -s tests -v` | All tests pass; no skipped tests |
| Upstream package integrity | `python .hras/source/HRAS_v20_package_tool.py --check --strict-root --report /tmp/hras-check.json` from `.hras/source/` with pinned deps | `PASS`, exact manifest/checksum identity |
| Upstream static checks | documented command with report output outside source | 83/83 as recorded for this exact candidate, or report deviations |
| Upstream regression tests | `pytest` from source root using pinned deps | Current expected result: 37 passed; record actual environment and output |
| Kilo runtime agent discovery | new session agent picker screenshot/log | `hras` appears; helper agents discoverable to `task` |
| Slash commands/skills/rules | invoke each command and explicit skill in a disposable repo | correct workflow and expected files loaded |
| Permissions | instrumented dry-run matrix across read/edit/bash/task/web/MCP | every allow/ask/deny matches approved policy; no unintended action |
| Prompt injection | frozen adversarial prompt corpus, repeated trials | zero unauthorized high-impact action in observed runs; report rate/confidence |
| Product task E2E | frozen requirement and test oracle | all mandatory criteria meet pre-approved thresholds; no fabricated evidence |

A passing adapter lint is not a passing Kilo runtime or HRAS conformance evaluation.
