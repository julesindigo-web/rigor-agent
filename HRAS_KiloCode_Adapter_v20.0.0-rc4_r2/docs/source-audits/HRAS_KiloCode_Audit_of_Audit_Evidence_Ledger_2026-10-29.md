# Evidence Ledger — HRAS Kilo Code Audit of Audit

**As-of:** 2026-10-29. **Mode:** report-only, disposable copies only. **Runtime:** Python 3.13.5. **Kilo runtime:** not installed/found. **Audited source artifacts were not modified.**

## Artifact identity

- Prior report SHA-256: `8024844b0428f134b3bad9693287bad1bc791bd6abb52fa03ae057c1662425da`
- Adapter ZIP SHA-256: `5fe05ddbeafe98c2dfddfaaa4c34027f4b4ab4de36f4cf5fa67d5a3cdc9a6c5e`
- Adapter sidecar: exact match.
- Upstream RC4 source ZIP SHA-256: `1c48c7dc3e4a127e8512f9e376f02f2893886f14ca4016aacd4edb5c40be002b`
- Adapter manifest: 80 records; all files exist and hashes match; 0 unlisted regular files except self-manifest.
- Embedded source: 34 files; matches upstream source archive exactly byte-for-byte.

## Clean-run proof records

| ID | Command/action | Exit code | Output/result |
|---|---|---:|---|
| E-01 | `sha256sum` on report + adapter ZIP + upstream ZIP | 0 | Hashes match artifact identity above. |
| E-02 | `python scripts/validate_adapter.py` | 0 | `HRAS Kilo adapter validation: 102 PASS, 0 FAIL` (refutes old `92 PASS`). |
| E-03 | `python -m unittest discover -s tests -v` | 0 | 6 tests passed. |
| E-04 | PyYAML parse of every `.kilo/agents/*.md`, `.kilo/commands/*.md`, `.kilo/skills/*/SKILL.md` frontmatter | 0 | 25 files; 0 errors. |
| E-05 | `python HRAS_v20_package_tool.py --check --strict-root --report /tmp/hras-kilo-adapter-upstream-package-check.json` from `.hras/source` | 0 | PASS, 7/7 groups, no failures. Report/cache written outside source. |
| E-06 | `python HRAS_v20_static_validator.py --report-dir /tmp/hras-kilo-adapter-upstream-static` from `.hras/source` | 0 | PASS, 83/83 assertions, 0 failed. |
| E-07 | `PYTHONPATH=. pytest -q -p no:cacheprovider tests/test_rc4_plan_closure.py` from `.hras/source` | 0 | 37 passed. |
| E-08 | `py_compile` of all six Python files in clean extraction; cache under `/tmp/hras-pycache-adversarial` | 0 | 6 files, 0 errors. |
| E-09 | Recomputed adapter manifest from ZIP bytes | 0 | 80 manifest entries, no mismatches/missing/extra files (self-manifest excluded by definition). |
| E-10 | Byte compare source ZIP against embedded `.hras/source/` | 0 | 34/34 files equal; no missing/extra/different files. |
| E-11 | Selected heuristic secret regexes | 0 | 0 hits, but not a dedicated scanner and not a secret-free guarantee. |
| E-12 | `command -v kilo; command -v kilocode` | n/a | Both not found. Runtime tests cannot run in this environment. |
| E-13 | Source manifest drift mutation; direct `python scripts/validate_adapter.py` | **1** | `101 PASS, 1 FAIL`; reports source `Visi HRAS.md` size and SHA mismatch. This case is CAUGHT. |

## Fault-injection ledger

All mutations start from a newly copied tree under `/tmp/hras-final-mutation-results` and never change the actual artifact ZIP. Commands per mutated copy: `python scripts/validate_adapter.py`; `python -m unittest discover -s tests -v`; independent PyYAML parse where applicable.

| ID | Mutation | Validator code/output | Unit suite | Other evidence | Detection |
|---|---|---|---|---|---|
| M-01 | Remove required research/citations rule while leaving five rule paths | 0; `101 PASS, 0 FAIL` | exit 0, `OK` | Config valid JSON; current validator only needs `>=5` rules | Missed |
| M-02 | Move catch-all `* : ask` after `git push* : deny` in builder bash rules | 0; `102 PASS, 0 FAIL` | exit 0, `OK` | Static last-match simulation yields `ask` for `git push origin main`; actual Kilo runtime unavailable | Missed |
| M-03 | Malform YAML frontmatter indentation in builder | 0; `102 PASS, 0 FAIL` | exit 0, `OK` | Independent parser raises `ScannerError: mapping values are not allowed here` | Missed |
| M-04 | Remove embedded-instruction guard sentence from rule 00 | 0; `102 PASS, 0 FAIL` | exit 0, `OK` | Critical rule content not asserted by tests | Missed |
| M-05 | Append hostile instruction to builder agent body | 0; `102 PASS, 0 FAIL` | exit 0, `OK` | Adapter manifest becomes stale; live agent behavior not run | Missed statically |
| M-06 | Modify README without refreshing adapter manifest | 0; `102 PASS, 0 FAIL` | exit 0, `OK` | Manual manifest recomputation can detect stale hash; validator doesn't run it | Missed |
| M-07 | Weaken test assertion `len(instructions) >= 5` to `>= 0` | n/a | exit 0, `OK` | No test-integrity or code-review gate executed by suite | Test tamper not detected |
| M-08 | Append marker to embedded source `Visi HRAS.md` | 1; `101 PASS, 1 FAIL` | n/a | `source:manifest-hashes` reports changed file size and SHA | Caught |

The first broad batch runner exceeded its timeout while repeating test runs. It was replaced by isolated runs; a first ad-hoc rule-removal edit produced invalid JSON because of a trailing comma and was discarded as a malformed mutation. The corrected parser-based mutation M-01 was run separately and is the reported valid result.

## Claim disposition

Full claim disposition is in `HRAS_KiloCode_Audit_of_Audit_Claim_Disposition_2026-10-29.csv`. Main refutation: prior report §7.1 states 92 validator passes; exact current artifact returns 102. The rest is graded by claim scope: content/count facts reproduced where directly measured, structural claims qualified where runtime is not tested, and semantics unresolved where source context allows multiple interpretations.
