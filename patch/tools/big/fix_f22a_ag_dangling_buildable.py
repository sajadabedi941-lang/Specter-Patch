#!/usr/bin/env python3
"""Move dangling Buildable=No inside AmericaJetStealthFighter.

Correction-pass regex used ^End, which skipped the indented Prerequisites
End and appended `  Buildable = No` AFTER the object's closing End.
That is invalid file-scope INI and crashes startup parse of F22A_AG.ini.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/usa_b52_ocl_fix/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/usa_f22a_ag_parse_fix")
TARGET = r"data\ini\object\specter\united states of america\airforce\f22a_ag.ini"


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


def _prerequisites_end(text: str) -> int:
    """Byte offset after the first Prerequisites closer.

    Do not use greedy `[ \\t]+(?!End)`: it backtracks one space on `  End`
    and treats a later ArmorSet End as the Prerequisites closer.
    """
    start = re.search(r"(?m)^[ \t]+Prerequisites[ \t]*\r?\n", text)
    if not start:
        raise SystemExit("Prerequisites not found")
    closer = re.search(r"(?m)^[ \t]+End[ \t]*\r?\n", text[start.end() :])
    if not closer:
        raise SystemExit("Prerequisites End not found")
    return start.end() + closer.end()


def patch(text: str) -> str:
    new, n = re.subn(
        r"(\r?\n)[ \t]+Buildable[ \t]*=[ \t]*No[ \t]*(\r?\n)+\Z",
        r"\1",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"dangling Buildable not removed ({n})")
    insert_at = _prerequisites_end(new)
    nl = "\r\n" if new[insert_at - 2 : insert_at] == "\r\n" else "\n"
    new2 = new[:insert_at] + f"  Buildable = No{nl}" + new[insert_at:]
    if not new2.rstrip().endswith("End"):
        raise SystemExit("file no longer ends at object End")
    if re.search(r"^End\s*\r?\n\s*Buildable", new2, re.M):
        raise SystemExit("Buildable still after object End")
    window = new2[insert_at : insert_at + 24]
    if "Buildable = No" not in window:
        raise SystemExit(f"Buildable not immediately after Prerequisites End: {window!r}")
    return new2


def main() -> int:
    entries = parse_big(SRC_DATA)
    original_names = [n for n, _ in entries]
    idx = next(
        i
        for i, (n, _) in enumerate(entries)
        if n.replace("/", "\\").lower() == TARGET
    )
    name, blob = entries[idx]
    text = blob.decode("latin1")
    new = patch(text)
    entries[idx] = (name, new.encode("latin1"))
    if [n for n, _ in entries] != original_names:
        raise SystemExit("entry order changed")
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
        "delta",
        len(new) - len(text),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
