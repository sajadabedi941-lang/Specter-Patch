#!/usr/bin/env python3
"""Rebuild SPECTER1 Iraq-controlled DATA BIG from a staged DATA tree.

Preserves original SPECTER1 BIGF path order (offset+size+name).
"""
from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pack(stage: Path, order_file: Path, out: Path) -> None:
    names = [ln.strip() for ln in order_file.read_text().splitlines() if ln.strip()]
    blobs = []
    for name in names:
        p = stage / name.replace("\\", "/")
        if not p.is_file():
            raise SystemExit(f"missing staged file: {name}")
        blobs.append((name, p.read_bytes()))
    header_size = 16
    for name, _ in blobs:
        header_size += 8 + len(name.encode("latin1")) + 1
    offset = header_size
    index = []
    for name, content in blobs:
        index.append((name, offset, len(content)))
        offset += len(content)
    out_bytes = bytearray()
    out_bytes += b"BIGF"
    out_bytes += struct.pack(">I", offset)
    out_bytes += struct.pack(">I", len(blobs))
    out_bytes += struct.pack(">I", header_size)
    for name, off, size in index:
        out_bytes += struct.pack(">II", off, size)
        out_bytes += name.encode("latin1") + b"\x00"
    for _, content in blobs:
        out_bytes += content
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(out_bytes))
    print(out, out.stat().st_size, sha256(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--order", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    pack(Path(args.stage), Path(args.order), Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
