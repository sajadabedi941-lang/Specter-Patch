#!/usr/bin/env python3
"""SPECTER1 isolation pass 1: unlock 3 Iraq aircraft only.

Source: /tmp/SPECTER1_ISO_COPY/_SPEC_DATA_ONE.big
Expected SHA256: 9629b6a092aaffb606a01af70e29b88d6c38c8dfc0958fe2d4c3a32c8d1da635

Surgical byte edits only. Does not rewrite CommandSet.ini, Weapon.ini,
WarFactory, MIC, or any other country.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

SRC = Path("/tmp/SPECTER1_ISO_COPY/_SPEC_DATA_ONE.big")
EXPECT_SRC = "9629b6a092aaffb606a01af70e29b88d6c38c8dfc0958fe2d4c3a32c8d1da635"
OUT = Path("/tmp/SPECTER1_ISO_WORK/_SPEC_DATA_ONE.big")

EDITS = {
    r"data\ini\object\specter\iraq army\airforce\iraq_miragef1-bq.ini": [
        (b"    Object = Iraq_RadarStation\r\n", b""),
    ],
    r"data\ini\object\specter\iraq army\airforce\iraq_su-24mk.ini": [
        (b"    Object = Iraq_RadarStation\r\n", b""),
        (b"    Object = Iraq_MIC\r\n", b""),
    ],
    r"data\ini\object\specter\iraq army\airforce\iraq_su-24mr.ini": [
        (b"    Object = Iraq_MIC\r\n", b""),
    ],
}


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
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECT_SRC:
        raise SystemExit(f"BASELINE HASH MISMATCH {sha}")
    src = parse_big(SRC)
    out = []
    changed = []
    for name, blob in src:
        key = name.replace("/", "\\").lower()
        new = blob
        if key in EDITS:
            for old, repl in EDITS[key]:
                n = new.count(old)
                if n != 1:
                    raise SystemExit(f"{name}: expected exactly 1 match for {old!r}, got {n}")
                new = new.replace(old, repl, 1)
        if new != blob:
            changed.append(name)
        out.append((name, new))
    if len(changed) > 6:
        raise SystemExit(f"STOP: too many files changed ({len(changed)})")
    for n in changed:
        low = n.replace("/", "\\").lower()
        if "iraq army\\airforce\\iraq_miragef1-bq.ini" not in low and "iraq army\\airforce\\iraq_su-24m" not in low:
            raise SystemExit(f"STOP: unrelated file changed {n}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    packed = build_big_ordered(out)
    OUT.write_bytes(packed)
    print("CHANGED")
    for n in changed:
        print(" ", n)
    print("DATA", hashlib.sha256(packed).hexdigest(), len(packed), "files", len(out))
    print("PACK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
