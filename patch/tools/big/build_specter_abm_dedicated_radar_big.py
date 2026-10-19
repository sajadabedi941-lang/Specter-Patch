#!/usr/bin/env python3
"""Pack 0_SPECTER_ABMDedicatedRadar.big as a restore overlay.

v4 last-won existing OCL/FCS names and in-game broke HQ-9 and S-400.
This pack only ships a unique unused marker on the same Object paths
v4 used, so replacing the BIG drops those last-wins. It does not pack
Weapon_* or ObjectCreationList_* extras.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

REPO = Path("/workspace")
SRC = REPO / "patch/Data/INI"
OUT = REPO / "patch/tools/installer/0_SPECTER_ABMDedicatedRadar.big"
SHA_OUT = Path(str(OUT) + ".sha256")
OBJ = r"Data\INI\Object\zzzz_SpecterABMDedicatedRadar"


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


def main() -> None:
    marker = (
        SRC / "Object/Specter/PatchSystems/ABMDedicatedRadar/ABM_FCS.ini"
    ).read_bytes()
    files: dict[str, bytes] = {
        rf"{OBJ}\ABM_FCS.ini": marker,
        r"Data\INI\Object_ZZZZ_SpecterABMDedicatedRadar.ini": marker,
    }
    blob = build_big(files)
    OUT.write_bytes(blob)
    digest = hashlib.sha256(blob).hexdigest()
    SHA_OUT.write_text(digest + "\n", encoding="ascii")
    print(f"wrote {OUT} size={len(blob)} sha256={digest} files={len(files)}")
    for name in sorted(files, key=str.lower):
        print(f"  {name} {len(files[name])}")


if __name__ == "__main__":
    main()
