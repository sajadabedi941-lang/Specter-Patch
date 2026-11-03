#!/usr/bin/env python3
"""Validate USAPAC3-only cleanup of active SPECTER packs."""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
MERGED = ROOT / "docs/specter-usapac3/merged"
DATA = MERGED / "_SPEC_DATA_ONE.big"
ART2 = MERGED / "_SPEC_ART_TWO.big"
PATCH = ROOT / "patch"


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


def main() -> int:
    if (PATCH / "Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini").exists():
        fail("overlay USAPAC3.ini still in live patch tree")
    data, ents = read_big(DATA)
    art, aents = read_big(ART2)
    forbidden = [
        b"Object USAPAC3\n",
        b"Object USAPAC3\r\n",
        b"Weapon USAPAC3_Weapon",
        b"Object USAPAC3_Projectile",
        b"Command_ConstructUSAPAC3",
        b"CommandSet USAPAC3CommandSet",
        b"UsaPac3Car",
        b"UsaPac3F",
        b"pac3mis_m",
    ]
    for needle in forbidden:
        hits = [n for n, o, s in ents if needle in data[o : o + s]]
        # generals.csf may still hold unused labels
        hits = [h for h in hits if not h.lower().endswith("generals.csf")]
        if hits:
            fail(f"DATA still has {needle!r} in {hits}")
    for n, o, s in aents:
        low = n.lower()
        if "usapac3" in low or "pac3mis_m" in low or "ampac3" in low:
            fail(f"ART TWO still has {n}")
    # shared kept
    keys = {n.replace("/", "\\").lower() for n, o, s in aents}
    for keep in [
        "art\\w3d\\pac3_sudarb.w3d",
        "art\\w3d\\abpatriot.w3d",
        "art\\textures\\abnpatriot02.dds",
        "art\\w3d\\us_m1120.w3d",
    ]:
        if keep not in keys:
            fail(f"shared art missing {keep}")
    # live CC restored
    cs = (MERGED / "CommandSet.ini").read_text("latin-1")
    m = re.search(r"CommandSet AmericaCommandCenterCommandSet\s*(.*?)\nEnd", cs, re.S)
    if not m:
        fail("CC missing")
    block = m.group(1)
    if "Command_ConstructUSAPAC3" in block or "6  = " in block:
        fail("CC slot 6 not restored")
    if "Command_ConstructAmericaDozer" not in block:
        fail("CC structure damaged")
    # THAAD / Patriot / NASAMS still present in DATA
    blob_all = data
    if b"Object US_THAAD" not in blob_all:
        fail("live US_THAAD missing")
    if b"Object AmericaMobileSamSiteMIM104F" not in blob_all:
        fail("live Patriot truck missing")
    hq = None
    for n, o, s in ents:
        if n.lower().endswith("commandset_factionexpansion_armies.ini"):
            hq = data[o : o + s].decode("latin-1")
    if not hq or "6 = Command_ConstructAmerica_AD_NASAMS" not in hq:
        fail("HQ NASAMS slot 6 not restored")
    if "Command_ConstructAmerica_AD_THAAD" not in hq or "Command_ConstructAmerica_AD_Patriot" not in hq:
        fail("HQ THAAD/Patriot lost")
    if "Command_ConstructUSAPAC3" in hq:
        fail("HQ still has USAPAC3")
    print("STATIC_OK")
    print("DATA", sha_file(DATA), DATA.stat().st_size, "entries", len(ents))
    print("ART2", sha_file(ART2), ART2.stat().st_size, "entries", len(aents))
    print("CommandSet", sha_file(MERGED / "CommandSet.ini"))
    print("CommandButton", sha_file(MERGED / "CommandButton.ini"))
    print("INGAME_ZH: not executed")
    print("PAC3_REBUILD: not started")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
