#!/usr/bin/env python3
"""Generate or verify the deterministic Specter-Patch package manifest."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "SYNC_MANIFEST.sha256"


def package_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path == MANIFEST:
            continue
        rel = path.relative_to(ROOT)
        if "__pycache__" in rel.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def manifest_text() -> str:
    entries = []
    for path in package_files():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")
    payload = "\n".join(entries) + "\n"
    package_digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return (
        "# Specter-Patch deterministic package manifest v1\n"
        f"# PackageSHA256 {package_digest}\n"
        + payload
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the committed manifest instead of writing it",
    )
    args = parser.parse_args()
    expected = manifest_text()
    if args.check:
        if not MANIFEST.exists():
            print(f"FAIL: missing {MANIFEST}")
            return 1
        if MANIFEST.read_text(encoding="utf-8") != expected:
            print(f"FAIL: stale or mismatched {MANIFEST}")
            return 1
        print(expected.splitlines()[1])
        print(f"PASS: {len(package_files())} patch files match")
        return 0
    MANIFEST.write_text(expected, encoding="utf-8")
    print(expected.splitlines()[1])
    print(f"Wrote {MANIFEST} ({len(package_files())} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
