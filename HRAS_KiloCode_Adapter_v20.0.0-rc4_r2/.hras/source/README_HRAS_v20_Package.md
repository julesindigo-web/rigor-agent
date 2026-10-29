# HRAS v20.0.0-rc4 — Package README

This is a candidate specification-and-contract package for autonomous production-grade software engineering. It is not a ready-to-install agent and carries no runtime certification.

**Schema registry status:** `OPEN_NOT_FROZEN`  

## Start here

1. `HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md` — normative full spec.
2. `HRAS_v20_Compiled_Core_Prompt.md` — compact instruction subset; not sufficient without the trusted controller.
3. `HRAS_v20_Contract_Schemas.json` — Draft 2020-12 machine-readable contracts.
4. `HRAS_v20_Policy_Registry.json` — non-waivable rules, restricted actions, blocking policy and case hash policy.
5. `HRAS_v20_Requirement_Traceability.json` and `HRAS_v20_Test_Cases.json` — source for two-way requirement/test links, 53 requirements, 139 cases and 695 typed oracle assertions.
6. `HRAS_v20_reference_controller.py` — reference primitives only, not a production security boundary.
7. `HRAS_v20_static_validator.py` — static artifact validator; requires Python 3.13.5 and dependencies pinned in `requirements-lock.txt`.
8. `HRAS_v20_Static_Validation_Report.md` — hash-bound static result for this package snapshot; its assertion count is recorded in the generated package manifest and must not be hard-coded elsewhere.
9. `HRAS_v20_Package_Manifest.md` — file SHA-256 manifest (excluding the manifest itself and ZIP archive).
10. `Visi HRAS.md`, `HRAS_v20_Vision_Provenance.json`, and `HRAS_v20_Vision_Clause_Inventory.csv` — pinned source vision and line-level inventory; semantic one-to-one mapping remains pending independent review.
11. `.python-version` and `requirements-lock.txt` — build interpreter and dependency pins.

## Validate locally

Extract the ZIP, use Python 3.13.5, and install the pinned validation/test dependencies with `python -m pip install -r requirements-lock.txt`; then run:

```bash
# Run from the extracted package root. Keep generated files/caches outside this root.
# The validator writes to a new temporary directory by default; specify --report-dir only when intentionally choosing an output destination.
RUN_DIR="$(pwd)/../hras-v20-rc4-validation-run"
mkdir -p "$RUN_DIR"
PYTHONDONTWRITEBYTECODE=1 python HRAS_v20_static_validator.py --report-dir "$RUN_DIR/static"
PYTHONDONTWRITEBYTECODE=1 python HRAS_v20_package_tool.py --check --strict-root --report "$RUN_DIR/package-check.json"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider tests/test_rc4_plan_closure.py
PYTHONPYCACHEPREFIX="$RUN_DIR/pycache" python -m py_compile HRAS_v20_reference_controller.py HRAS_v20_static_validator.py HRAS_v20_package_tool.py
# Run strict-root package check again after all checks.
PYTHONDONTWRITEBYTECODE=1 python HRAS_v20_package_tool.py --check --strict-root --report "$RUN_DIR/package-check-final.json"
```

The validator dynamically computes its assertion count and writes to a fresh temporary directory by default, leaving packaged evidence untouched. Use `--report-dir` outside the package for a stable evidence location. An explicit `--report-dir` pointing at the package root intentionally replaces the bundled report and requires the package manifest/checksums to be regenerated afterward. Always disable bytecode generation for package checks and keep `py_compile` cache outside the root. A static PASS does not mean the target LLM, tools, authorization service, memory backend or deployment was tested.

## Important boundaries

- All 139 cases are `NOT_RUN` and their fixtures are `UNMATERIALIZED`.
- Traceability edges are proposed and require independent semantic approval.
- The bundled hash helper supports the present integer-only test corpus and rejects float values; production must integrate and test a full RFC 8785 JCS implementation.
- A real deployment requires trusted authorization, key management, transactional state/operation records, provider reconciliation, sandboxing, evidence storage, CI/CD policy and independent security review.
- Candidate status: `20.0.0-rc4`; do not label production-ready.


Fixture integrity semantics: `fixture_declaration_hash` identifies the fixture declaration, not actual fixture bytes. `fixture_hash` and `environment_id` remain null until fixture contents and a real environment are materialized and hashed. All 139 source cases remain `NOT_RUN`; these counts describe the current package inventory, not test execution.
