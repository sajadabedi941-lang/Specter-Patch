#!/usr/bin/env python3
"""Pack patch/Data + patch/Art into standalone _SPECTER_PATCH_FINAL_V2.big overlay.

Does not modify original _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big.
Output is a separate patch BIG that loads after the original Specter BIGs.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        content = bytes(content)
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
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="Path to _SPECTER_PATCH_FINAL_V2.big")
    args = ap.parse_args()

    file_map: dict[str, bytes] = {}
    data_root = args.patch_root / "Data"
    for path in sorted(data_root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(data_root).as_posix()
            file_map["Data\\" + rel.replace("/", "\\")] = path.read_bytes()
    art_root = args.patch_root / "Art"
    if art_root.exists():
        for path in sorted(art_root.rglob("*")):
            if path.is_file():
                rel = path.relative_to(args.patch_root).as_posix()
                file_map[rel.replace("/", "\\")] = path.read_bytes()

    data = build_big(file_map)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    print(f"Wrote {args.out} entries={len(file_map)} bytes={len(data)} SHA256={digest}")
    (args.out.with_suffix(args.out.suffix + ".sha256")).write_text(digest + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
