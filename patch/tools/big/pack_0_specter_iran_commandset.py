#!/usr/bin/env python3
"""Pack Data\\INI\\CommandSet.ini into 0_SPECTER_IranCommandSet.big (first-win vs INIZH)."""
from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--commandset-ini", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    cs = args.commandset_ini.read_bytes()
    if b"CommandSet IranMissileFireCommandSet" not in cs:
        raise SystemExit("CommandSet.ini missing IranMissileFireCommandSet")
    if b"CommandSet IranWarfactoryCommandSet" not in cs:
        raise SystemExit("CommandSet.ini missing IranWarfactoryCommandSet")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    big = build_big({r"Data\INI\CommandSet.ini": cs})
    out = args.out_dir / "0_SPECTER_IranCommandSet.big"
    out.write_bytes(big)
    (args.out_dir / "0_SPECTER_IranCommandSet.big.sha256").write_text(
        hashlib.sha256(big).hexdigest() + "\n"
    )
    print(out, len(big), hashlib.sha256(big).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
