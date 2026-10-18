#!/usr/bin/env python3
"""Pack 0_SPECTER_ABMDedicatedRadar.big on paths the engine actually parses.

The previous pack used Data\\INI\\zzz_SpecterABMDedicatedRadar\\ which is not
under Object\\ and is not a Data\\INI root extra file. SPEC and working
overlays in this repo load:

  Data\\INI\\Object\\**          (ThingFactory InitPath)
  Data\\INI\\Weapon_*.ini        (root extra weapons, same pattern as Weapon_Egypt.ini)
  Data\\INI\\ObjectCreationList_*.ini  (root extra OCL, same pattern as ObjectCreationList_ZZZZ_*)

0_ first-wins duplicate PATHS only. Unique filenames do not hide SPEC
Weapon.ini / ObjectCreationList.ini.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

REPO = Path("/workspace")
SRC = REPO / "patch/Data/INI"
OUT = REPO / "patch/tools/installer/0_SPECTER_ABMDedicatedRadar.big"
SHA_OUT = Path(str(OUT) + ".sha256")
# zzzz_ sorts after Object\Specter\United States Of America\ so THAAD last-wins.
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
    fcs = (SRC / "Object/Specter/PatchSystems/ABMDedicatedRadar/ABM_FCS.ini").read_bytes()
    files: dict[str, bytes] = {
        rf"{OBJ}\ABM_FCS.ini": fcs,
        # Root extra Object_ZZZZ_ pattern (SPEC GlobalStore last-wins).
        r"Data\INI\Object_ZZZZ_SpecterABMDedicatedRadar.ini": fcs,
        r"Data\INI\Weapon_SpecterABMDedicatedRadar.ini": (
            SRC / "Weapon_SpecterABMDedicatedRadar.ini"
        ).read_bytes(),
        r"Data\INI\ObjectCreationList_SpecterABMDedicatedRadar.ini": (
            SRC / "ObjectCreationList_SpecterABMDedicatedRadar.ini"
        ).read_bytes(),
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
