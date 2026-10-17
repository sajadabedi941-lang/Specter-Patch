#!/usr/bin/env python3
"""Fix smashed ObjectCreationList.ini End+next-OCL token only.

The correction-pass regex left:
  EndObjectCreationList OCL_AmericaC17TargetParaDrop
which is a parse error. No other INIs are modified.
"""

from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/usa_correction_pass/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/usa_b52_ocl_fix")

CLEAN_B52_OCL = (
    "ObjectCreationList OCL_AmericaB52TargetCarpetLine\r\n"
    "  CreateObject\r\n"
    "    Offset = X:0 Y:0 Z:90\r\n"
    "    ObjectNames = Mk82_B52H\r\n"
    "    IgnorePrimaryObstacle = Yes\r\n"
    "    Disposition = LIKE_EXISTING\r\n"
    "    Count = 12\r\n"
    "  End\r\n"
    "End\r\n"
    "\r\n"
)


def parse_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
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


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded = [(name.encode("latin1"), blob) for name, blob in entries]
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


def patch_ocl(text: str) -> str:
    start = text.find("ObjectCreationList OCL_AmericaB52TargetCarpetLine")
    if start < 0:
        raise SystemExit("OCL_AmericaB52TargetCarpetLine not found")
    nxt = text.find("ObjectCreationList OCL_AmericaC17TargetParaDrop", start + 1)
    if nxt < 0:
        raise SystemExit("following C17 OCL not found")
    # The broken file is "...EndObjectCreationList...". Keep from the
    # C17 ObjectCreationList token; CLEAN_B52_OCL already supplies End+newlines.
    new = text[:start] + CLEAN_B52_OCL + text[nxt:]
    if "EndObjectCreationList" in new:
        raise SystemExit("smashed EndObjectCreationList still present")
    if new.count("ObjectCreationList OCL_AmericaB52TargetCarpetLine") != 1:
        raise SystemExit("B52 OCL count wrong")
    if new.count("ObjectCreationList OCL_AmericaC17TargetParaDrop") != 1:
        raise SystemExit("C17 OCL count wrong")
    if "Count = 12" not in new[new.find("OCL_AmericaB52TargetCarpetLine") :]:
        raise SystemExit("Count = 12 missing")
    return new


def main() -> int:
    entries = parse_big(SRC_DATA)
    original_count = len(entries)
    original_names = [n for n, _ in entries]
    key = r"data\ini\objectcreationlist.ini"
    idx = next(
        i
        for i, (n, _) in enumerate(entries)
        if n.replace("/", "\\").lower() == key
    )
    name, blob = entries[idx]
    text = blob.decode("latin1")
    new = patch_ocl(text)
    if new == text:
        raise SystemExit("no change")
    entries[idx] = (name, new.encode("latin1"))
    if len(entries) != original_count or [n for n, _ in entries] != original_names:
        raise SystemExit("entry order/count changed")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "_SPEC_DATA_ONE.big"
    packed = build_big_ordered(entries)
    out.write_bytes(packed)
    print(
        "wrote",
        out,
        "size",
        len(packed),
        "files",
        len(entries),
        "sha",
        hashlib.sha256(packed).hexdigest(),
        "ocl delta",
        len(new) - len(text),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
