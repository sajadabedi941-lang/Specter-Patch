#!/usr/bin/env python3
"""Extract Specter BIGF archives into loose Data/ Art/ folders."""
from __future__ import annotations

import argparse
import struct
from pathlib import Path


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not a BIGF archive: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def extract_big(big_path: Path, out_root: Path) -> int:
    entries, raw = read_big(big_path)
    written = 0
    for name, off, size in entries:
        rel = name.replace("\\", "/").lstrip("/")
        if not rel:
            continue
        dest = out_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw[off : off + size])
        written += 1
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-big", type=Path, required=True)
    ap.add_argument("--art-big", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    n1 = extract_big(args.data_big, args.out_dir)
    n2 = extract_big(args.art_big, args.out_dir)
    print(f"Extracted DATA files: {n1}")
    print(f"Extracted ART files:  {n2}")
    print(f"Output: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
