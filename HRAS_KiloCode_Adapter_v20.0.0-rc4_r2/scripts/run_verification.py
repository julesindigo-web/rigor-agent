#!/usr/bin/env python3
"""Run the reproducible local release gates and emit artifact-bound evidence JSON.

Example:
  python scripts/run_verification.py --archive ../HRAS_KiloCode_Adapter_R2.zip --output ../HRAS_KiloCode_Adapter_R2_Verification.json

The output should be stored outside the package to avoid a recursive archive-hash
cycle. Evidence binds results to the exact archive SHA-256 and test/validator hashes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def package_file_hashes() -> dict[str, str]:
    paths = [
        ROOT / "scripts/validate_adapter.py", ROOT / "scripts/update_manifest.py",
        ROOT / "scripts/run_verification.py", ROOT / "tests/test_adapter.py",
        ROOT / "kilo.jsonc", ROOT / "ADAPTER_MANIFEST.sha256",
        ROOT / "docs/GAP_REGISTRY.json", ROOT / "docs/SOURCE_AUDIT_PROVENANCE.json",
        ROOT / "docs/REMEDIATION_REPORT_R2.md", ROOT / "docs/REMEDIATION_LEDGER_R2.md",
        ROOT / ".kilo/agents/hras.md", ROOT / ".kilo/agents/hras-builder.md",
        ROOT / ".kilo/rules/00-hras-trust-and-precedence.md",
    ]
    return {p.relative_to(ROOT).as_posix(): sha256(p) for p in paths if p.is_file()}


def run(name: str, argv: list[str], cwd: Path, env_overrides: dict[str, str], timeout: int = 300) -> dict:
    env = os.environ.copy()
    env.update({"PYTHONDONTWRITEBYTECODE": "1", **env_overrides})
    started = datetime.now(timezone.utc).isoformat()
    begin = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        return {
            "id": name, "command": argv, "cwd_relative": str(cwd.relative_to(ROOT)),
            "started_at_utc": started, "duration_seconds": round(time.monotonic()-begin, 3),
            "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
            "status": "PASS" if p.returncode == 0 else "FAIL",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "id": name, "command": argv, "cwd_relative": str(cwd.relative_to(ROOT)),
            "started_at_utc": started, "duration_seconds": round(time.monotonic()-begin, 3),
            "exit_code": None, "stdout": exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
            "stderr": exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
            "status": "TIMEOUT",
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True, help="exact R2 ZIP to bind to this run")
    ap.add_argument("--output", type=Path, required=True, help="external JSON output path")
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()
    archive = args.archive.resolve()
    output = args.output.resolve()
    if not archive.is_file():
        raise SystemExit(f"archive does not exist: {archive}")
    if output == archive or output.is_relative_to(ROOT):
        raise SystemExit("evidence output must be outside the package/ZIP to avoid recursive identity claims")

    try:
        import yaml
        yaml_version = yaml.__version__
    except Exception as exc:
        yaml_version = f"unavailable: {type(exc).__name__}: {exc}"
    try:
        import pytest
        pytest_version = pytest.__version__
    except Exception as exc:
        pytest_version = f"unavailable: {type(exc).__name__}: {exc}"

    results = []
    with tempfile.TemporaryDirectory(prefix="hras-kilo-r2-evidence-") as tmp:
        tmpdir = Path(tmp)
        source = ROOT / ".hras/source"
        results.append(run("adapter-validator", [sys.executable, "scripts/validate_adapter.py"], ROOT, {}, args.timeout))
        results.append(run("adapter-unit-and-mutation-tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], ROOT, {}, args.timeout))
        results.append(run("upstream-package-integrity", [sys.executable, "HRAS_v20_package_tool.py", "--check", "--strict-root", "--report", str(tmpdir / "upstream-package-check.json")], source, {}, args.timeout))
        results.append(run("upstream-static-validator", [sys.executable, "HRAS_v20_static_validator.py", "--report-dir", str(tmpdir / "upstream-static")], source, {}, args.timeout))
        results.append(run("upstream-regression-tests", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_rc4_plan_closure.py"], source, {"PYTHONPATH": str(source)}, args.timeout))
        compile_code = (
            "from pathlib import Path; import sys; "
            f"root=Path({str(ROOT)!r}); "
            "files=sorted([p for p in root.rglob('*.py') if not any(x in {'.git','__pycache__','.pytest_cache','.mypy_cache'} for x in p.parts)]); "
            "[(compile(p.read_text(encoding='utf-8'),str(p),'exec')) for p in files]; "
            "print(f'compiled {len(files)} Python source files without writing bytecode')"
        )
        results.append(run("python-syntax-compile", [sys.executable, "-c", compile_code], ROOT, {}, args.timeout))

    all_pass = all(r["status"] == "PASS" for r in results)
    payload = {
        "evidence_id": "HRAS-KILO-ADAPTER-R2-LOCAL-VERIFY",
        "schema_version": "1.0.0",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "artifact": {
            "archive_name": archive.name, "archive_size_bytes": archive.stat().st_size,
            "archive_sha256": sha256(archive), "package_manifest_sha256": sha256(ROOT / "ADAPTER_MANIFEST.sha256"),
            "version_file_sha256": sha256(ROOT / "HRAS_KILO_ADAPTER_VERSION.json"),
        },
        "environment": {
            "python_version": sys.version, "python_implementation": platform.python_implementation(),
            "platform": platform.platform(), "machine": platform.machine(),
            "pyyaml_version": yaml_version, "pytest_version": pytest_version,
            "kilo_runtime": "NOT_RUN", "hras_runtime_conformance": "NOT_RUN",
        },
        "bound_file_hashes": package_file_hashes(),
        "commands": results,
        "summary": {
            "command_count": len(results), "passed": sum(r["status"] == "PASS" for r in results),
            "failed_or_timed_out": [r["id"] for r in results if r["status"] != "PASS"],
            "status": "PASS" if all_pass else "FAIL",
            "scope_note": "Local package/source checks only; does not certify Kilo runtime, external controls or 139-case HRAS runtime conformance.",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["summary"]["status"], "archive_sha256": payload["artifact"]["archive_sha256"], "output": str(output), "commands": payload["summary"]}, indent=2))
    return 0 if all_pass else 1

if __name__ == "__main__":
    raise SystemExit(main())
