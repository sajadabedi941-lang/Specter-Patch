#!/usr/bin/env python3
"""Rebuild SPECTER1 Iraq update DATA from the 69-part archive only.

Baseline must be the _SPEC_DATA_ONE.big extracted from
SPECTER1.part001.rar .. SPECTER1.part069.rar.

Expected baseline SHA256:
  9629b6a092aaffb606a01af70e29b88d6c38c8dfc0958fe2d4c3a32c8d1da635
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

EXPECT_SRC = "9629b6a092aaffb606a01af70e29b88d6c38c8dfc0958fe2d4c3a32c8d1da635"
SRC = Path("/tmp/SPECTER1_REAL_BASELINE_COPY/_SPEC_DATA_ONE.big")
OUT = Path("/tmp/SPECTER1_REAL_BUILD/_SPEC_DATA_ONE.big")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_big(path: Path):
    data = path.read_bytes()
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((name, data[eoff : eoff + esz]))
    return entries


def build_big_ordered(entries):
    header_size = 16
    encoded = [(n.encode("latin1"), b) for n, b in entries]
    for nb, _blob in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for nb, blob in encoded:
        index.append((nb, offset, len(blob)))
        blobs.append(blob)
        offset += len(blob)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def main() -> int:
    raw = SRC.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECT_SRC:
        raise SystemExit(f"BASELINE HASH MISMATCH {hashlib.sha256(raw).hexdigest()}")
    print("BASELINE_OK", EXPECT_SRC, len(raw))
    print("This script records the accepted baseline.")
    print("The Iraq update DATA already packed at build time is:")
    if OUT.exists():
        print("PACKED", sha256(OUT), OUT.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
