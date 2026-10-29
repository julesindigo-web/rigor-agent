# HRAS v20 → Kilo Code integration audit


> **Gap-ID authority (R2):** IDs in the tables below are legacy, document-local references. The canonical, cross-document identity and all legacy mappings are in [`GAP_REGISTRY.json`](GAP_REGISTRY.json). Never join, close, or aggregate gaps by legacy `KG-xxx`/`IK-xx` alone. Registry mapping is not closure evidence.

**Research cutoff/as-of:** 2026-10-29.  
**Source inspected:** the complete clean extraction of the HRAS v20.0.0-rc4 candidate remediated archive distributed with this adapter.  
**Kilo compatibility basis:** official Kilo Code docs listed in `KILO_COMPATIBILITY_REVIEW.md`, inspected 2026-10-29.  
**Audit scope:** source/package contracts, Kilo customization surface, proposed mapping, configuration boundaries, testing/evaluation plan.  
**Not performed:** live Kilo installation/runtime session, target model benchmark, real project build, trusted external controller implementation, any push/deploy/infra action.

## Executive result

**Conclusion: technically feasible as a supervised Kilo Code agent adapter; not sufficient to certify HRAS as an autonomous production control plane.** Kilo offers native surfaces for custom Markdown agents, project rules/instructions, `AGENTS.md`, slash-command workflows, on-demand skills, permissions and MCP integrations. These support a good orchestration interface. The HRAS source, however, explicitly requires a trusted controller, an external authorization broker, durable operation state, verified release identity, real tool-boundary instrumentation, and artifact-bound runtime evidence. Those are not delivered merely by custom prompts, permissions, or workflows.

## Reproduced source evidence

The candidate package source manifest reports 53 requirements, 63 schema definitions, 139 test cases and 695 typed oracle assertions. The test registry is `PROPOSED_NOT_EXECUTED`; on inspection, all 139 case states are `NOT_RUN`, all 139 `fixture_hash` values are null, all 139 `environment_id` values are null, 136 cases have empty `allowed_tools`, and 0 cases have a `tools_adapter_ref`. The upstream package README states the schema registry is `OPEN_NOT_FROZEN`, the hash helper only supports its present integer-valued corpus and a production RFC 8785 JCS implementation is still required. The outstanding-issues document also calls for a trusted authorization broker, durable operation ledger, isolated fixtures/runtime tests, independently reviewed traceability, identity-bound release controller and evidence sink.

These are source/package facts, not live Kilo runtime results.

## Integration findings

| ID | Severity | Finding | Decision / mitigation |
|---|---|---|---|
| IK-01 | CRIT | The HRAS control plane cannot be implemented by prompt instructions alone | Keep Kilo as orchestration/UI; external trusted authorization broker and release controller are P0 before any autonomous high-impact operations. |
| IK-02 | HIGH | Runtime suite is unexecuted and fixtures/environment/tool interfaces are absent | Mark conformance `NOT_RUN`; materialize/hash fixtures and expose instrumented adapters before runtime claims. |
| IK-03 | HIGH | Empty `allowed_tools` and absent `tools_adapter_ref` risk vacuous tool-security tests | Populate every test's observed tool surface; distinguish no-tools from unspecified; prove target boundary is invoked. |
| IK-04 | HIGH | MCP and plugin paths expand capability beyond simple source permissions | No MCP auto-configuration. Add tools individually after owner/threat review; pin versions; test permissions and output prompt injection. Plugins that intercept tool calls are a potential control surface, but require runtime compatibility and adversarial testing. |
| IK-05 | HIGH | Side effect timeout/restart state cannot be safely reconciled by model text | Durable atomic OperationRecord ledger and provider read-back/idempotency are required; prohibit blind retries. |
| IK-06 | HIGH | Candidate state and source hashes are not a release certification | Pin Kilo build, model/provider/tool schemas, config hash and final artifact hash per run; release controller validates all gates. |
| IK-07 | MOD | Rules are best effort, and agent prompts sit higher in Kilo instruction precedence | Duplicate only the most important invariants in the `hras` primary prompt and always-loaded rules; adversarially test instruction conflicts. Never treat this as hard security enforcement. |
| IK-08 | MOD | HRAS route concepts do not map 1:1 to Kilo agent `mode` property | Use one primary HRAS orchestrator, bounded subagents and slash commands. Explicitly distinguish the HRAS route enum from Kilo's `primary/subagent/all`. |
| IK-09 | MOD | No model-specific evaluation or budget manifest supplied | Leave model unpinned; run a repeatable comparative eval across candidates and record quality, cost, latency, context, tool compatibility, and failure modes. |
| IK-10 | MOD | HRAS vision inventory is byte-bound, not semantically approved | Map every clause to requirement, test or approved N/A and independently review; don't claim coverage based on line counts. |
| IK-11 | MOD | Source version relationship is ambiguous to a reader | Owner should clarify whether spec's `Parent baseline v18` and version record `baseline_version rc3` have distinct meanings. Preserve source evidence until disposition. |

## Why this architecture

- **Primary agent:** carries HRAS mission, route choice, trust boundaries and required pipeline.
- **Read-only audit/security/evidence reviewers:** limit accidental edits and provide independent challenge.
- **Builder/test subagents:** allow changes only in response to bounded task/accepted findings; command permission remains conservative.
- **Always-loaded rules:** make evidence and security semantics available without requiring every skill to load.
- **Slash commands:** explicit repeatable process entry points; not a deterministic workflow engine.
- **Skills:** detailed on-demand procedures to avoid bloating every prompt.
- **CI/script validation:** objective structural and hash checks for adapter artifacts.
- **External controller:** all trust-sensitive authorization, operation journaling, status transitions and deployment gates.

## Verification performed for this adapter build

- Upstream clean extraction: static validator `83/83 PASS`; strict-root package verifier `7/7 groups PASS`; pytest `37 passed`; Python syntax compilation passed; final strict-root verification passed, all on Python 3.13.5, with report/cache outputs outside source root.
- Adapter-specific validation/tests are performed after build and described in the external delivery report. These checks do not exercise Kilo's live model/tool runtime.

## Official Kilo sources

See `KILO_COMPATIBILITY_REVIEW.md`; custom agents, rules, permissions, workflows, skills, AGENTS.md, MCP, auto-approval and plugins/hooks were checked against official Kilo Code documentation. Official docs note that permission patterns are order-sensitive and that broad auto-approval increases risk. The plugin API can intercept tool calls, but using it as an HRAS control-plane substitute would be an unsupported overclaim absent target-runtime tests and a trusted policy service.
