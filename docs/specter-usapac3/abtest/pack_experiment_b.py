#!/usr/bin/env python3
"""Pack EXPERIMENT B Object USAPAC3 into a *copy* of spawnfix3 DATA.

Does not write patch/Data/.../USAPAC3.ini
Does not overwrite docs/specter-usapac3/merged/_SPEC_DATA_ONE.big
Does not touch ART TWO, CommandSet, CommandButton, THAAD/Patriot/NASAMS.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "docs/specter-usapac3/merged/_SPEC_DATA_ONE.big"
SRC_A_SHA = "7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343"
OUT_DIR = ROOT / "docs/specter-usapac3/abtest"
OUT_DATA = OUT_DIR / "_SPEC_DATA_ONE.big"
EXPERIMENT_B = OUT_DIR / "USAPAC3_EXPERIMENT_B.ini"
ORIGINAL = ROOT / "patch/Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini"
KEY = "data\\ini\\object\\specter\\patchsystems\\airdefense\\usapac3.ini"


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        fail(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name, off, size))
    return data, entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin-1")) + 1
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
        out += name.encode("latin-1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def main() -> int:
    if sha_file(SRC_DATA) != SRC_A_SHA:
        fail(f"source DATA is not experiment A / spawnfix3 ({sha_file(SRC_DATA)})")
    orig = ORIGINAL.read_text(encoding="latin-1")
    if "Model             = UsaPac3F" not in orig:
        fail("original overlay lost UsaPac3F — abort so A stays intact")
    b = EXPERIMENT_B.read_text(encoding="latin-1")
    if re.search(r"(?m)^\s+(Model|Animation)\s+=\s+UsaPac3", b):
        fail("experiment B still names New Donor models")
    if "Model             = US_M1120" not in b:
        fail("experiment B missing healthy US_M1120")
    if "BuildCost           = 3876" not in b or "BuildTime           = 18.6" not in b:
        fail("cost/time changed")
    if "Weapon             = SECONDARY USAPAC3_Weapon" not in b:
        fail("weapon changed")
    if "Locomotor = SET_NORMAL Generic8x8Locomotor" not in b:
        fail("locomotor changed")
    if "CommandSet           = USAPAC3CommandSet" not in b:
        fail("commandset changed")
    raw, entries = read_big(SRC_DATA)
    amap = {}
    found = None
    new = EXPERIMENT_B.read_bytes()
    for name, off, size in entries:
        key = name.replace("/", "\\").lower()
        blob = raw[off : off + size]
        if key == KEY:
            found = name
            blob = new
        if key in amap:
            fail(f"duplicate {name}")
        amap[name] = blob
    if found is None:
        fail("packed USAPAC3.ini not found")
    out = build_big(amap)
    if sha_file(SRC_DATA) != SRC_A_SHA:
        fail("source DATA mutated")
    OUT_DATA.write_bytes(out)
    print(f"wrote {OUT_DATA} entries={len(amap)} bytes={len(out)}")
    print(f"B DATA sha256={sha_file(OUT_DATA)}")
    print(f"A DATA unchanged sha256={sha_file(SRC_DATA)}")
    print(f"original overlay unchanged sha256={sha_file(ORIGINAL)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
