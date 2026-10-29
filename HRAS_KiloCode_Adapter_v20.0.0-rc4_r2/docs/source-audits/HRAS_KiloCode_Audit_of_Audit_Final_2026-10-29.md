# HRAS Kilo Code — Final Adversarial Audit of Audit

**Audit type:** `AUDIT.FINAL_ADVERSARIAL` · **Mode:** attachment-driven, report-only · **As-of:** 29 October 2026  
**Verdict:** `DELIVERY_WITH_GAPS` — the prior report is **partially reliable, not accepted as final proof**. No audited artifact was changed, repaired, committed, deployed, or pushed during this audit.

## 0. BINDING — inputs, identity, and constraints

Inputs actually inspected:

| Input | Identity / disposition |
|---|---|
| Prior report `HRAS_KiloCode_Integration_Audit_2026-10-29.md` | SHA-256 `8024844b0428f134b3bad9693287bad1bc791bd6abb52fa03ae057c1662425da`; 286 lines; read as an untrusted claim-set. |
| Adapter `HRAS_KiloCode_Adapter_v20.0.0-rc4_r1.zip` | SHA-256 `5fe05ddbeafe98c2dfddfaaa4c34027f4b4ab4de36f4cf5fa67d5a3cdc9a6c5e`; sidecar matches. |
| Upstream HRAS candidate `HRAS_v20.0.0-rc4-candidate-remediated-2026-10-29-r1.zip` | SHA-256 `1c48c7dc3e4a127e8512f9e376f02f2893886f14ca4016aacd4edb5c40be002b`. |
| Upstream remediation artifacts | Worklist F-01–F-14, remediation report, ledger, gap register and final MR/D status CSVs were present and consulted for cross-plan mapping. |
| Execution environment | Python 3.13.5; PyYAML available; `kilo` and `kilocode` executables absent from PATH. Temporary clean extraction and mutation copies only. |

**Scope discipline:** all fault injection used disposable copies under `/tmp`. The adapter ZIP and upstream source ZIP were read-only. No Kilo UI/CLI session, production credential, external write, or external service was touched. The report does not claim to prove a clean secret state: the heuristic scan found zero hits for selected common token patterns, but dedicated scanners (`gitleaks`, `trufflehog`, `detect-secrets`, `semgrep`, `bandit`) were unavailable.

## 1. Verdict on the previous report

The user's suspicion is **justified**. The report correctly states the most important release limitation—Kilo runtime is not tested and all 139 upstream conformance cases are still `NOT_RUN`. Its source inventory, hashes, static validation and local regression results were largely reproducible. However, there is at least one exact numerical claim that is wrong for the exact ZIP hash it cites, and the adapter’s own validator/tests have material fake-green gaps.

Claim-set contains **53 material claims**. Dispositions, based on current evidence:

| Disposition | Count |
|---|---:|
| `VERIFIED_REPRODUCED` | 35 |
| `REFUTED` | 1 |
| `PARTIALLY_TRUE` | 17 |
| `UNVERIFIABLE` | 0 |

The per-claim disposition ledger is [here](sandbox:/mnt/data/HRAS_KiloCode_Audit_of_Audit_Claim_Disposition_2026-10-29.csv). Counts are a classification of claims material to the report, not a proof that every sentence or every possible behavior has been enumerated.

### The refuted numeric claim

The old report §7.1 states that `python scripts/validate_adapter.py` yielded **92 PASS, 0 FAIL**. The exact adapter ZIP hash in its §7.3 was reproduced and the current script prints **102 PASS, 0 FAIL**, exit code 0. The 92 count is therefore `REFUTED` for the artifact supplied now. There is no evidence in the supplied package that a different version with 92 assertions was the intended artifact; the report’s value should be corrected in its evidence history, not silently treated as equivalent.

### What held up under re-check

- Adapter ZIP and sidecar hashes match.
- The ZIP contains 81 unique regular files, with counts: 6 agents, 6 rules, 15 commands, 4 skills, 34 embedded HRAS source files, 6 docs, 3 templates, 1 validator, 1 adapter test file, and 5 root files.
- All 80 entries in `ADAPTER_MANIFEST.sha256` match the file bytes; all 80 refer to existing files; there are no unlisted regular files other than the self-manifest itself. **This was independently checked here; it is not checked by the adapter’s own validator.**
- The 34 files in the upstream source ZIP are byte-identical to the 34 files under `.hras/source/` in the adapter ZIP.
- The upstream manifest has 31 hashed inventory entries and explicitly scopes out three support/receipt files to avoid self-referential hashes. Strict-root validation passes, so that count difference is explained by the source manifest rather than an invented mismatch.
- Upstream source facts (53 requirements, 63 schema `$defs`, 139 cases, 695 oracle assertions, 75 release-blocking cases, status and null fixture/environment fields) reproduce.
- All 25 Markdown frontmatter blocks parse under an independent YAML parser in the unmutated package. The key qualification is that the parser is absent from the adapter validation/test path.

## 2. Reproduction ledger — clean extraction

Commands below ran against the fresh ZIP extraction, Python 3.13.5, with bytecode/cache output kept outside source and reports directed to `/tmp`:

| Evidence ID | Command / action | Exit | Observed output |
|---|---|---:|---|
| E-01 | `sha256sum` of prior report, adapter ZIP, upstream ZIP | 0 | Hashes match the identities above. |
| E-02 | `python scripts/validate_adapter.py` | 0 | `HRAS Kilo adapter validation: 102 PASS, 0 FAIL`. |
| E-03 | `python -m unittest discover -s tests -v` | 0 | 6 tests ran; all passed. |
| E-04 | Independent PyYAML parse of agent/command/skill frontmatter | 0 | 25 files; zero parse errors. |
| E-05 | `python HRAS_v20_package_tool.py --check --strict-root --report /tmp/...json` | 0 | PASS; 7/7 groups; zero failures. |
| E-06 | `python HRAS_v20_static_validator.py --report-dir /tmp/...` | 0 | PASS; 83 assertions; 83 passed; 0 failed. |
| E-07 | `PYTHONPATH=. pytest -q -p no:cacheprovider tests/test_rc4_plan_closure.py` | 0 | `37 passed` (about 6 seconds). |
| E-08 | `py_compile` across all six Python files in the clean adapter/source tree | 0 | 6 files; 0 compile errors. |
| E-09 | Internal adapter manifest vs ZIP bytes (independent Python check) | 0 | 80 entries; missing 0; hash mismatch 0; unlisted regular files 0 (excluding self-manifest). |
| E-10 | Upstream source archive ↔ `.hras/source/` byte comparison | 0 | 34 vs 34; missing 0; extra 0; byte differences 0. |
| E-11 | Secret heuristic scan for private-key markers, common AWS/GitHub/Slack tokens and long Bearer literals | 0 | 0 hits. This is a limited heuristic, not a comprehensive secrets clearance. |
| E-12 | `command -v kilo` and `command -v kilocode` | n/a | Both not found; live Kilo runtime remains untestable in this environment. |

The original source corpus is **not** rewritten by the local regression suite. The 37 tests and 83 static assertions are separate verification layers and must not be relabelled as 139-case HRAS runtime conformance.

## 3. New findings from adversarial probes

### KFA-01 — HIGH — Cross-document gap IDs are not a stable registry

**Evidence:** the submitted report §5 defines 13 meanings under `KG-001…KG-013`. `docs/IMPLEMENTATION_ROADMAP.md` defines only 12 gaps and reuses IDs for different meanings; `docs/HRAS_KILO_INTEGRATION_AUDIT.md` also defines an `IK-01…IK-11` register without a mapping table to either `KG` register.

Examples of collisions:

- Report `KG-002` = durable operation ledger/reconciliation; roadmap `KG-002` = 139-case runtime conformance.
- Report `KG-003` = runtime conformance; roadmap `KG-003` = tool observability.
- Report `KG-004` = release/status controller; roadmap `KG-004` = durable operation record.
- Report `KG-010` = CI and independent review; roadmap `KG-010` = product/UX/engineering benchmark.
- Report `KG-012` = product/model benchmark; roadmap `KG-012` = baseline-version ambiguity. Report `KG-013` has no same-numbered roadmap row.

**Impact:** closure evidence can be attached to the wrong obligation; dashboards or future agents cannot infer cross-file identity from `KG-00x` alone. **Fix recommendation:** adopt one canonical versioned gap registry (stable UUID or namespaced ID), assign each report/roadmap row a common canonical ID, and include an explicit migration map for legacy `KG` and `IK` references. Until then, treat every `KG-00x` reference as document-local.

### KFA-02 — HIGH — Adapter manifest drift is a false green

**Evidence:** in a disposable copy, appending a marker to `README.md` makes its `ADAPTER_MANIFEST.sha256` hash stale. The validator still returns `102 PASS, 0 FAIL`, and the unit suite remains green. The manifest is internally correct in the pristine ZIP, but the verification path does not enforce it.

**Impact:** the validator can certify an edited adapter tree whose stated file manifest no longer matches. This affects agent instructions, permissions, tests, docs and scripts—not only harmless README changes. **Fix recommendation:** verify `ADAPTER_MANIFEST.sha256` on every run; fail on missing, extra, duplicated, or changed files; verify the validator and tests themselves are included; define a deterministic self-manifest exclusion rule. Add mutations for manifest hash drift, unlisted files and deleted manifest entries.

### KFA-03 — HIGH — Permission-order mutation is not detected

**Evidence:** Kilo’s current documentation says the last matching permission rule wins. citeturn277846search0turn277846search1 In a disposable copy of `hras-builder.md`, moving the catch-all `"*": ask` after `"git push*": deny` causes a static last-match simulation for `git push origin main` to resolve to `ask`, not `deny`. The adapter validator still returns `102 PASS, 0 FAIL`; all 6 unit tests pass.

**Scope qualification:** no Kilo binary/runtime is available here, so this proves a static semantic inconsistency using the documented precedence rule, not a live runtime permission event. **Impact:** a sensitive-command deny can be weakened silently. **Fix recommendation:** parse frontmatter into an AST, calculate effective decisions for a frozen list of representative command strings, assert every mandatory-deny command remains denied after rule-order resolution, and repeat those probes in the actual pinned Kilo build.

### KFA-04 — HIGH — Invalid YAML frontmatter is not rejected by the adapter gate

**Evidence:** indenting the builder frontmatter’s `bash:` key incorrectly causes independent PyYAML to raise `ScannerError: mapping values are not allowed here`. Yet adapter validation remains `102 PASS, 0 FAIL` and the 6-test suite passes.

**Impact:** a malformed agent can fail to load or have permission metadata interpreted differently by a particular Kilo build without the preflight gate catching it. **Fix recommendation:** parse every frontmatter block using a real YAML parser in validator and tests, validate the agent/command/skill schema and allowed fields, and add a malformed YAML regression mutation.

### KFA-05 — MOD — Required always-loaded rules are counted permissively, not identity-checked

**Evidence:** removing `.kilo/rules/50-hras-research-and-citations.md` from `kilo.jsonc` with valid JSON leaves five rules. The validator returns `101 PASS, 0 FAIL`, and all 6 tests pass because checks accept `len(instructions) >= 5`, not the exact required set. A citation/research invariant can therefore disappear and still be green.

**Fix recommendation:** assert the exact six paths or an explicit versioned rule registry; test content hashes or policy identifiers for critical rules; fail when any required rule is absent, duplicated, replaced or reordered contrary to specification.

### KFA-06 — MOD — Critical instruction content is not mutation-protected

**Evidence:** each of these isolated mutations stayed green: removing the embedded-instruction guard sentence from rule 00; adding an instruction telling the builder to ignore restrictions; and altering the adapter README without refreshing the manifest. In the first two cases, validator output remains `102 PASS, 0 FAIL` and 6 tests pass.

**Impact:** the suite checks that some files and markers exist, but not that crucial trust-boundary policy remains present or unambiguous. **Fix recommendation:** add policy contract assertions on stable rule IDs/invariant statements, independent prompt-injection test cases, and manifest enforcement. A text check alone cannot prove model behavior; runtime adversarial evaluation still remains required.

### KFA-07 — MOD — Core prompt is referenced, not configured as a direct instruction source

**Evidence:** `hras.md` tells the agent to use `.hras/source/HRAS_v20_Compiled_Core_Prompt.md` and the canonical spec. The `kilo.jsonc` `instructions` list itself contains the six `.kilo/rules/*.md` files, not those two HRAS files. Kilo documentation states that explicit `instructions` entries are injected as instructions, while root `AGENTS.md` is a different instruction source. citeturn277846search5turn277846search6turn277846search7

**Impact:** compliance with the core prompt depends on the model choosing to read and apply a referenced file; it is not yet established that the normative core prompt always enters the instruction context. This is a risk, not proof of a live failure. **Fix recommendation:** add a concise, version-pinned core-invariant file directly to `instructions` (after checking precedence/size effects) and/or add a deterministic boot/read verification step; prove the final effective prompt sources in a Kilo runtime diagnostic.

### KFA-08 — MOD — Prior numeric test evidence has no test artifact version bound to the result

**Evidence:** the report states 92 validator passes while the exact ZIP SHA listed in that report currently yields 102. The package itself includes a manifest, but the previous report did not bind its execution statement to the validator file hash + raw output artifact + runner environment. The discrepancy could be a stale transcription or an unreconciled intermediate run; the available evidence does not resolve which.

**Impact:** result counts can be copied between package iterations without proving which code produced them. **Fix recommendation:** every proof record must include command, environment, exit code, raw stdout/stderr, validator/test file hashes, package SHA-256 and timestamp; generate the report from the captured evidence automatically.

## 4. Coverage inversion — real universe vs prior report surface

Adapter ZIP inventory, from scratch: **81 unique files**. It is not sufficient to say “the adapter package passed” without distinguishing each surface:

| Surface | Current audit verdict | What was actually checked | Residual limitation |
|---|---|---|---|
| Archive/sidecar hash | `VERIFIED_REPRODUCED` | SHA-256 of exact ZIP equals sidecar. | Hash authenticity still depends on trustworthy distribution channel/signature; no signature was supplied. |
| Adapter internal manifest | `VERIFIED_REPRODUCED` for pristine ZIP; **validator enforcement absent** | 80 hashes match 80 files; no unlisted regular files except manifest. Mutation fails to alert. | KFA-02. |
| HRAS source copy and upstream manifest | `VERIFIED_REPRODUCED` | 34/34 byte-identical; strict-root 7/7, source checks catch drift. | Source package is still a candidate spec, not a runtime control plane. |
| Agent frontmatter | `PARTIAL` | Six files, independent YAML parse. | Permission semantics and prompt adherence not live-tested; rule-order mutation is green. |
| Rules | `PARTIAL` | Six rules exist and are named in config. | Removal/content mutation can pass. No effective prompt trace. |
| Commands | `PARTIAL` | 15 Markdown files; 13 canonical route command names checked. | Syntax/frontmatter mutation not covered by built-in tests; no execution in Kilo. |
| Skills | `PARTIAL` | Four skill files, frontmatter parse. | On-demand discovery/context selection not tested live. |
| Templates | `PARTIAL` | Three templates present and inventoried. | No template semantic/acceptance tests. |
| Validator and unit tests | `VERIFIED_REPRODUCED` for current result; **test adequacy insufficient** | Script and all six tests rerun; mutations applied to independent copies. | Multiple critical config/policy mutations remain green. |
| Docs/gap registers | `FINDING` | Audit report, roadmap and embedded audit compared independently. | KG/IK ID registry has conflicting semantics and no canonical map (KFA-01). |
| Manifest, source provenance and vision CSV | `PARTIAL` | Source hashes; 146 vision inventory rows including header=147. | Semantic mapping remains unapproved. |
| Secrets/supply chain | `UNVERIFIABLE` beyond heuristic | Common token/private-key patterns: zero hits. | No dedicated secret/dependency scanner available; no claim of “secret-free”. |
| Live Kilo permissions, subagent, slash commands and skills | `UNVERIFIABLE / NOT_RUN` | No `kilo`/`kilocode` executable or live session. | Requires pinned Kilo installation/runtime environment. |
| MCP, plugins, hooks and external providers | `UNVERIFIABLE / NOT_CONFIGURED_IN_ARTIFACT` | Adapter contains no MCP/plugin config/code. | User-global runtime plugins or MCP cannot be excluded from this artifact-only inspection. |
| Shell chaining, alternate interpreters, egress and credential isolation | `UNVERIFIABLE` | No live boundary, sandbox or provider instrumentation. | Must be tested in disposable runtime; do not infer safety from text patterns. |
| Idempotency, timeout-after-effect, reconciliation, release status controller | `UNVERIFIABLE / EXTERNAL COMPONENTS ABSENT` | Architecture documents describe required boundaries; no such live external control plane supplied. | P0 external blocker remains. |

The universe-minus-coverage delta is not empty. The first report did not demonstrate effective permission order, YAML failure detection, adapter self-manifest enforcement, prompt-instruction mutation resistance, or cross-document ID reconciliation. The mutation probes turn these coverage gaps into evidence-backed findings rather than speculative audit breadth claims.

## 5. Test adequacy and FAKE-GREEN report

All mutations below used fresh copies of the clean extraction under `/tmp`; none touched the supplied ZIPs. “Suite” means the adapter’s own six tests. There was no Kilo LLM/runtime execution.

| Mutation | Validator result | Adapter test suite | Independent probe/result | Verdict |
|---|---|---|---|---|
| Remove one required rule, leaving 5 of 6 | `101 PASS, 0 FAIL`, exit 0 | 6/6, exit 0 | `len(instructions) >= 5` permits it | **MISSED** |
| Move catch-all bash `ask` after named `git push* deny` | `102 PASS, 0 FAIL`, exit 0 | 6/6, exit 0 | Documented last-match semantics make effective result `ask` in static simulation | **MISSED** |
| Malform builder YAML frontmatter indentation | `102 PASS, 0 FAIL`, exit 0 | 6/6, exit 0 | PyYAML raises `ScannerError` | **MISSED** |
| Remove prompt-injection trust sentence from rule 00 | `102 PASS, 0 FAIL`, exit 0 | 6/6, exit 0 | Critical invariant removed | **MISSED** |
| Append hostile authority-changing instruction to builder | `102 PASS, 0 FAIL`, exit 0 | 6/6, exit 0 | Instruction text changes; adapter manifest becomes stale | **MISSED** (runtime adherence not tested) |
| Change README without refreshing adapter manifest | `102 PASS, 0 FAIL`, exit 0 | 6/6, exit 0 | Independent manifest recomputation detects stale hash | **MISSED** |
| Weaken unit test rule-count assertion from `>=5` to `>=0` | Not applicable to test-only mutation | 6/6, exit 0 | No test/CI gate detects weakened test source | **MISSED BY TEST-INTEGRITY CONTROL** |
| Alter embedded `Visi HRAS.md` without updating upstream package manifest | `101 PASS, 1 FAIL`, exit **1** | Not needed to establish validator effect | `source:manifest-hashes` reports byte-size and SHA mismatch | **CAUGHT** |

**Interpretation:** the source manifest check is effective for embedded upstream files, but the adapter itself is not protected by equivalent enforced integrity checks. For five security/configuration mutations plus test weakening, green tests do not establish the claimed safety properties. This is strong evidence of test inadequacy. It does not prove the Kilo runtime would obey a hostile instruction; it proves the available preflight and tests would not detect that package mutation.

## 6. Assumption archaeology and counterfactual challenge

| Foundational assumption / old verdict | Strongest counterargument | Current resolution |
|---|---|---|
| “Package validated” could be read as “Kilo-compatible and safe” | Static file checks do not load the agent, parse effective config in Kilo, execute tool calls, or test instruction precedence. | **Narrowed:** `PACKAGE_STRUCTURE_VALIDATED`; keep `KILO_RUNTIME_NOT_RUN`. |
| 6/6 tests prove adapter policy is robust | Tests assert presence/count thresholds and source corpus statuses, not all critical rule semantics. | **Refuted as a broad inference:** multiple mutations remain green. |
| Read-only review agent is safe because `edit`/`bash` say deny | Rules can be reordered; permissions have runtime-specific matching/precedence and alternate tools can exist. | **Partially supported:** file config is restrictive; runtime enforcement unverified. |
| Source provenance is integrity-protected | Embedded upstream manifest catches source file drift. | **Verified for source subtree; not adapter tree.** Distinct trust domains; don't generalize. |
| No MCP/plugin config means no extra tool surface exists | User/global Kilo configuration can still add plugins/MCP and tools outside this repo. | **Only artifact-local absence verified.** Must inventory runtime-global config at installation time. |
| 37 regression tests mean the 139-case HRAS corpus is covered | They are a separate test file and leave 139 corpus entries `NOT_RUN`. | **Refuted;** both figures can be true only as distinct test layers. |
| Current docs say last-match-wins means effective permission is known | Docs establish intended semantics, but no target Kilo build was installed; one official source description elsewhere is inconsistent. | **Static rule interpretation supported, target runtime still UNVERIFIABLE.** |
| Version-baseline fields conflict | `baseline_version=rc3` and “parent baseline v18” could describe packaging vs normative lineage. | **Conflict not established:** preserve both and seek owner semantics. |

## 7. CROSS_PLAN — HRAS remediation ledger vs Kilo roadmap

| Upstream remediation item | Related current Kilo report ID | Kilo roadmap ID | Cross-plan status |
|---|---|---|---|
| F-04 — 139 runtime cases/fixtures remain unrun | KG-003 | KG-002 | **OPEN/BLOCKED:** no fixture hashes/environment IDs, no runtime. Don't close on 37 local tests. |
| F-12 — `allowed_tools` and adapter refs / actual boundary absent | KG-006 | KG-003 | **OPEN/BLOCKED:** no per-case actual tool/provider boundary or runtime traces. |
| F-10 — source/provenance documents unresolved | Source provenance and registry consistency | No stable mapped ID | **OPEN/UNMAPPED:** add explicit crosswalk; do not close by renaming IDs. |
| F-14 — vision semantic traceability independent review | KG-011 | KG-011 | **OPEN:** 146 rows establish inventory/byte binding, not semantic acceptance. |
| F-13 — validator/runtime/dependency identity | KG-007 | KG-007 | **PARTIAL:** upstream runtime pins Python and local checks are reproducible; Kilo build/model/config/provider still not pinned. |
| F-05 and F-11 — upstream local regression fixes | External broker/ledger controls | KG-001/KG-004 depending on register | **PARTIAL:** 37 local tests pass, but they do not create an external trusted broker, durable ledger or release controller. |
| F-06 — stale release-state identity guard | Source integrity/provenance | No exact one-to-one ID | **LOCAL REGRESSION REPRODUCED:** upstream 37 tests pass; not equivalent to adapter manifest validation. |

**Registry defect:** the same `KG-00x` token cannot be used as a cross-document primary key while semantics differ. Until KFA-01 is corrected, the mapping above is intentionally document-qualified and should not be ingested as if the numeric IDs were globally stable.

## 8. Corrected remediation roadmap

### P0 — before any external/high-impact autonomy

1. Keep external operations, write-capable MCP, publish, push, deploy and migrations blocked until the trusted broker, durable operation ledger, provider read-back/reconciliation and independent release controller are implemented and tested. This remains upstream of Kilo prompt policy.
2. Fix KFA-01: publish a canonical gap registry and map `KG`/`IK` references in the report, roadmap and source remediation plan.
3. Fix KFA-02: make `validate_adapter.py` verify the adapter manifest, reject extra/missing files and test source drift, plus bind result outputs to the exact artifact hash.
4. Fix KFA-03: implement static effective-permission evaluation for every mandatory deny/allow case and a live Kilo conformance probe on a pinned build. Do not assume that a pattern string alone proves the effective decision.
5. Fix KFA-04: parse and schema-validate all YAML frontmatter as part of the official gate; malformed YAML must fail before Kilo is opened.
6. Complete F-04/F-12 runtime prerequisites: materialize/hash fixtures; provision environment IDs and approved oracles; set per-case allowed tool surfaces and bind `tools_adapter_ref`; capture observed tool/provider traces.

### P1 — before release candidate approval

7. Assert the exact required rules/skills/agents, stable critical policy IDs and command coverage; do not use permissive `>=` thresholds where the contract requires exact membership.
8. Add mutation testing to CI: missing rule, weakened deny, reversed rule order, malformed frontmatter, deleted guard, hostile injected instructions, stale manifest, source drift, unlisted file, changed test assertion. Require expected detection for each mutation class.
9. Pin Kilo extension/CLI build, model/provider/version, effective config/permissions, tool/plugin/MCP inventories and OS/container policy in every run record.
10. Add live tests for read-only boundaries, command chaining/interpreter alternatives, external-directory access, prompt injection from repository/web/tool outputs, plugin hooks and user-global config. Test in a disposable workspace with no production credentials.
11. Preserve raw output with `command + environment + exit + stdout/stderr + code hashes + artifact SHA + fixture/environment IDs` instead of manually transcribed counts.

### P2 — before any “maximum/rigorous” quality claim

12. Close F-10 and F-14 with owner-reviewed provenance/semantic mapping. A 146-row inventory is not equivalent to 146 valid semantic trace links.
13. Resolve baseline semantics, freeze schema only after dependencies are closed, implement full RFC 8785/JCS support and independently test it if canonical hashes depend on it.
14. Run an approved, repeatable quality/UX/engineering benchmark with predeclared thresholds and independent review; do not elevate a label based on configuration volume.

## 9. Negative space and required blind-spot techniques

| Required technique | Executed? | Yield | What remains unknown |
|---|---|---|---|
| (a) Coverage inversion | **Yes, artifact-local** | 81-file inventory and category counts; newly examined validator, tests, rule semantics, frontmatter, manifest and cross-doc registers. Found KFA-01–KFA-07. | Runtime-global plugins/config and provider boundary absent from delivered artifacts. |
| (b) Assumption archaeology | **Yes** | Narrowed package-validity semantics; separated source manifest integrity from adapter manifest; confirmed version ambiguity without inventing a contradiction. | Owner decisions on baseline, semantic traceability and frozen policy. |
| (c) Counterfactual/falsify-first | **Yes** | Challenged “92 PASS”, read-only confidence, and inference from 6/6 tests. One numeric claim refuted; several broad conclusions narrowed. | Actual Kilo effective config cannot be observed here. |
| (d) Negative-space lenses | **Yes, bounded** | Security/rule ordering, prompt injection, provenance drift, frontmatter, secret heuristic, MCP/plugin presence, test integrity, concurrent external control-plane needs reviewed. | Dedicated secret/dependency scanner; live egress/credential isolation, concurrency, timeout-after-effect tests. |
| (e) Fault injection/mutation | **Yes** | 8 mutations; 7 policy/config/manifest/test mutations not caught; upstream source drift caught. | Live model behavior under injected hostile content not tested without runtime. |
| (f) Claim-scope check | **Yes** | Explicitly distinguishes structural, static semantic, documentation-derived, runtime and production claims. | Live Kilo/HRAS behavior, end-to-end security. |
| (g) Cross-plan reconciliation | **Yes** | Mapped F-04/F-12/F-10/F-14/F-13/F-05/F-11/F-06; found duplicated KG identifiers and IK register without crosswalk. | A single signed owner-approved canonical gap registry is not supplied. |

This is evidence of a broad attempted audit over the files and probes available—not a claim that every possible runtime failure has been exhausted. The final status remains `DELIVERY_WITH_GAPS`.

## 10. Out-of-scope observation

**Out-of-scope observation:** Kilo’s official current documentation pages say “last matching permission rule wins” and show the `findLast` model, but another instruction/support description in the broader Kilo documentation material has previously been worded as first-match in one passage. The current authoritative docs located for this audit consistently state last-match-wins. Because there is no Kilo runtime/build installed here, the resolution should be confirmed by an executable permission probe against the exact pinned build before deployment. This is a vendor-doc/runtime verification observation, not a claim that this adapter’s baseline config currently has incorrect order. citeturn277846search0turn277846search1

## 11. Gaps/limits

- `KILO_RUNTIME_NOT_RUN`: no agent-picker discovery, actual prompt source trace, command execution, skills discovery, or effective permission event was observed.
- `HRAS_RUNTIME_CONFORMANCE_NOT_RUN`: 139 cases remain `NOT_RUN`; all fixture hashes and environment IDs are null, and `allowed_tools`/`tools_adapter_ref` are incomplete.
- `SECRETS_SCAN_LIMITED`: zero hits among selected regexes is not a comprehensive secret clearance; no specialized scanners were present.
- `CONTROL_PLANE_NOT_PROVIDED`: no trusted authorization broker, durable operation ledger, provider read-back, release controller, or evidence sink was presented as a live component.
- `PRODUCTION_NOT_READY`: do not promote based on these local passes. A config file can be syntactically valid and still fail to load or enforce policy in Kilo.

## 12. Final status

**`DELIVERY_WITH_GAPS` — NOT `DONE`.** The previous report is useful as an architectural direction but not acceptable as a complete final adversarial audit. Its 92-pass figure is refuted; the adapter is green under multiple high-value fault injections; and its KG gap identifiers collide across artifacts. Package/source integrity, local tests and upstream validators are otherwise reproducible within scope. Close KFA-01–KFA-06 and perform the missing Kilo/runtime/conformance gates before considering higher assurance.
