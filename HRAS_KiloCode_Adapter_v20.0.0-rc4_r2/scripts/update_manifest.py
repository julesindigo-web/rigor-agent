#!/usr/bin/env python3
"""Explicitly regenerate the adapter SHA-256 inventory for a release build.

This command writes ADAPTER_MANIFEST.sha256 only when --write is supplied.
The manifest excludes itself to avoid a hash cycle; release integrity must be
anchored by the externally distributed archive SHA-256 (and ideally a signature).
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ADAPTER_MANIFEST.sha256"
IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}

def iter_files():
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT)
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        if p.is_symlink():
            raise SystemExit(f"refusing symlink in release inventory: {rel.as_posix()}")
        if p.is_file() and p != MANIFEST and p.suffix not in IGNORED_SUFFIXES:
            yield p

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def content() -> str:
    lines = [f"{sha256(p)}  {p.relative_to(ROOT).as_posix()}" for p in iter_files()]
    return "\n".join(lines) + "\n"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="replace the manifest; otherwise print candidate contents")
    args = ap.parse_args()
    rendered = content()
    if args.write:
        tmp = MANIFEST.with_suffix(".sha256.tmp")
        tmp.write_text(rendered, encoding="utf-8")
        tmp.replace(MANIFEST)
        print(f"wrote {MANIFEST.relative_to(ROOT)} with {len(rendered.splitlines())} entries")
    else:
        print(rendered, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
