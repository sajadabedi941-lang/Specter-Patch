#!/usr/bin/env python3
"""Validate A/B pack: original A intact, B isolates Draw only."""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
AB = ROOT / "docs/specter-usapac3/abtest"
MERGED = ROOT / "docs/specter-usapac3/merged"
ORIGINAL = ROOT / "patch/Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini"
A_INI = AB / "USAPAC3_EXPERIMENT_A.ini"
B_INI = AB / "USAPAC3_EXPERIMENT_B.ini"
A_DATA = MERGED / "_SPEC_DATA_ONE.big"
B_DATA = AB / "_SPEC_DATA_ONE.big"
ART2 = MERGED / "_SPEC_ART_TWO.big"

A_DATA_SHA = "7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343"
ART2_SHA = "81d9a4aa10550ef8b3f4a58842f159fda3f54a1af32fcef37df185eb9b9995bf"
CS_SHA = "f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"
CB_SHA = "4eb2c95a9415d081bb5fbf508f25883c5afe598448f4ca70bbc6dac8b2ef6b2d"
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
        fail(f"not BIGF {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name.replace("/", "\\"), off, size))
    return data, entries


def main() -> int:
    orig = ORIGINAL.read_bytes()
    a = A_INI.read_bytes()
    b = B_INI.read_bytes()
    if orig != a:
        fail("EXPERIMENT_A.ini != original overlay USAPAC3.ini")
    if b"UsaPac3F" not in orig or b"UsaPac3Car" not in orig:
        fail("original A lost New Donor models")
    if re.search(rb"(?m)^\s+(Model|Animation)\s+=\s+UsaPac3", b):
        fail("experiment B still names New Donor models")
    if b"Model             = US_M1120" not in b:
        fail("B missing US_M1120")
    if b"Model             = US_M1120_A" not in b:
        fail("B missing US_M1120_A")
    for token in [
        b"BuildCost           = 3876",
        b"BuildTime           = 18.6",
        b"Weapon             = SECONDARY USAPAC3_Weapon",
        b"Weapon             = TERTIARY  USAPAC3_Weapon",
        b"Locomotor = SET_NORMAL Generic8x8Locomotor",
        b"CommandSet           = USAPAC3CommandSet",
        b"Object USAPAC3",
    ]:
        if token not in orig or token not in b:
            fail(f"gameplay token missing {token!r}")
    if sha_file(A_DATA) != A_DATA_SHA:
        fail("merged DATA (experiment A / spawnfix3) was overwritten")
    if sha_file(ART2) != ART2_SHA:
        fail("ART TWO changed")
    if sha_file(MERGED / "CommandSet.ini") != CS_SHA:
        fail("CommandSet.ini changed")
    if sha_file(MERGED / "CommandButton.ini") != CB_SHA:
        fail("CommandButton.ini changed")
    cs = (MERGED / "CommandSet.ini").read_text(encoding="latin-1")
    m = re.search(r"CommandSet AmericaCommandCenterCommandSet\s*(.*?)\nEnd", cs, re.S)
    if not m or "6  = Command_ConstructUSAPAC3" not in m.group(1):
        fail("slot 6")
    if "Command_ConstructAmerica_AD_NASAMS" in m.group(1):
        fail("NASAMS inserted into live CC")

    a_raw, a_ents = read_big(A_DATA)
    b_raw, b_ents = read_big(B_DATA)
    a_map = {n.replace("/", "\\").lower(): a_raw[o : o + s] for n, o, s in a_ents}
    b_map = {n.replace("/", "\\").lower(): (n, b_raw[o : o + s]) for n, o, s in b_ents}
    if a_map[KEY] != orig:
        fail("packed A object != original overlay")
    if b_map[KEY][1] != b:
        fail("packed B object != EXPERIMENT_B.ini")
    if len(a_ents) != len(b_ents):
        fail(f"entry count A {len(a_ents)} B {len(b_ents)}")
    # only USAPAC3.ini may differ
    diffs = []
    for n, o, s in a_ents:
        key = n.replace("/", "\\").lower()
        if b_map[key][1] != a_raw[o : o + s]:
            diffs.append(n)
    if diffs != [b_map[KEY][0]]:
        fail(f"unexpected B DATA diffs {diffs}")
    art_raw, art_ents = read_big(ART2)
    art_map = {n.replace("/", "\\").lower() for n, o, s in art_ents}
    for model in ["US_M1120", "US_M1120D", "US_M1120_A", "US_M1120_AD"]:
        if f"art\\w3d\\{model.lower()}.w3d" not in art_map:
            fail(f"missing {model} in ART TWO")
    print("STATIC_OK")
    print("A_original_intact", sha_file(ORIGINAL))
    print("A_DATA", A_DATA_SHA, A_DATA.stat().st_size)
    print("B_DATA", sha_file(B_DATA), B_DATA.stat().st_size)
    print("ART2_unchanged", ART2_SHA)
    print("CommandSet_unchanged", CS_SHA)
    print("CommandButton_unchanged", CB_SHA)
    print("INGAME_ZH: not executed")
    print("CRASH_FIXED: not claimed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
