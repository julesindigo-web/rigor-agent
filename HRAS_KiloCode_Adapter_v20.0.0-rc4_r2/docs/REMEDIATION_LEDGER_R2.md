# HRAS Kilo Adapter R2 — Remediation Evidence Ledger

**Baseline:** R1 ZIP SHA-256 `5fe05ddbeafe98c2dfddfaaa4c34027f4b4ab4de36f4cf5fa67d5a3cdc9a6c5e`  
**Date:** 2026-10-29  
**Execution environment:** Python 3.13.x; PyYAML 6.0.3; pytest 9.0.2; Linux build container; local disposable copy. Exact environment and timestamps for the final archive run are in the external verification JSON.

| Evidence ID | Slice | Command/probe | Exit/result | Interpretation |
|---|---|---|---|---|
| R2-E01 | Baseline replay | `python scripts/validate_adapter.py` on R1 | `0`; `102 PASS, 0 FAIL` | Reproduced the prior audit's count discrepancy: R1 output is 102, not 92. |
| R2-E02 | Manifest drift | Append marker to README in temporary copy; run validator without manifest refresh | non-zero; `FAIL manifest:sha256-content` | Stale content hash is detected. |
| R2-E03 | Rule removal | Remove required rule from `kilo.jsonc`, refresh manifest in temp copy, validate | non-zero; `FAIL config:exact-instruction-sources` | Semantic exact-list control catches removal after hashes are refreshed. |
| R2-E04 | YAML mutation | Corrupt builder YAML frontmatter, refresh manifest in temp copy, validate | non-zero; `FAIL frontmatter:valid-agent:hras-builder.md` | Real parser catches malformed YAML. |
| R2-E05 | Permission-order mutation | Move `bash['*'] = ask` after named denies, refresh manifest, validate | non-zero; `FAIL config:effective-deny:git push origin main` (and other protected probes) | Static effective evaluator catches Kilo's documented last-match behavior. Live runtime remains untested. |
| R2-E06 | Trust guard deletion | Remove required marker/sentence from rule 00, refresh manifest, validate | non-zero; marker/contract failure | Static invariant is required in adapter-owned policy source. |
| R2-E07 | Hostile instruction | Append direct authority override to builder, refresh manifest, validate | non-zero; `FAIL instruction:no-hostile-override-directives` | Narrow static signature catches this mutation; not a general proof against all natural-language attacks. |
| R2-E08 | Test-code drift | Alter test assertion in temporary copy without refreshing manifest, validate | non-zero; `FAIL manifest:sha256-content` | Test file is included in the artifact integrity inventory. This does not protect against an actor who changes both code and the manifest; external artifact signature/attestation is the stronger trust anchor. |
| R2-E09 | Adapter unit/mutation suite | `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v` | `15 tests; OK` | All normal and mutation tests pass in final working tree. Final clean-archive repetition appears in external verification JSON. |
| R2-E10 | Adapter static validator | `PYTHONDONTWRITEBYTECODE=1 python scripts/validate_adapter.py` | `272 PASS, 0 FAIL` | Static package/config/provenance contracts pass. Does not certify Kilo runtime. |
| R2-E11 | Upstream package integrity | `PYTHONDONTWRITEBYTECODE=1 python HRAS_v20_package_tool.py --check --strict-root --report /tmp/hras-r2-pretests/upstream-package-check.json` | `PASS`, all 7 groups | Confirms embedded upstream source package integrity at this build stage. |
| R2-E12 | Upstream static validation | `PYTHONDONTWRITEBYTECODE=1 python HRAS_v20_static_validator.py --report-dir /tmp/hras-r2-pretests/static` | `83/83 PASS` | Source validator rerun; separate layer from adapter tests. |
| R2-E13 | Upstream regression | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m pytest -q -p no:cacheprovider tests/test_rc4_plan_closure.py` | `37 passed in 6.92s` | Local regression success only; not 139-case runtime conformance. |
| R2-E14 | Kilo runtime | Install/pick agent, command, skill and effective permissions | `NOT_RUN` | No Kilo runtime was available in this environment. |
| R2-E15 | HRAS runtime conformance | Execute 139 source cases with bound fixtures, env IDs and tool adapters | `NOT_RUN` | Fixtures and adapter/environment bindings remain incomplete in upstream source. |
| R2-E16 | Preserved audit source integrity | Append a mutation to embedded `docs/source-audits/HRAS_KiloCode_Integration_Audit_2026-10-29.md`, refresh general adapter manifest, rerun validator | non-zero; `FAIL source-audits:byte-provenance` | The independent source-audit provenance record catches altered audit input even when the general adapter manifest is refreshed. |

## Failed-attempt history (preserved)

1. Initial R2 validator run failed because the source compiled core prompt had been modified during invariant work and because builder/test-engineer permission maps lacked some explicit denies. The upstream prompt was restored byte-for-byte; only adapter-owned configs were changed.
2. Initial R2 test run had five failures caused by assertions matching the label in both `PASS` and `FAIL` lines. Assertions were tightened to include result prefixes. A subsequent run had one positive-case assertion accidentally expecting `FAIL`; it was corrected to expect `PASS`.
3. Initial upstream package validation flagged two generated `__pycache__/*.pyc` files in the temporary build copy. They were removed as generated artifacts and the checks were rerun with bytecode writing disabled; the package checker passed.
4. The first clean-archive evidence-run invocation timed out at the outer command boundary and left the previous JSON unchanged. That record was treated as stale and not reused. Individual gates were rerun successfully, followed by a complete runner rerun from a clean extraction; the final JSON binds the current ZIP hash and reports six of six commands PASS.

## Evidence semantics

- `PASS` above refers only to the command and artifact described by that row.
- Final archive identity and raw command output must be read from `HRAS_KiloCode_Adapter_R2_Verification.json`; do not substitute the build-worktree values above for the clean archive run.
- No deploy, push, external action, Kilo live session or production authorization was attempted.
