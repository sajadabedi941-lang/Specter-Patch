#!/usr/bin/env python3
from __future__ import annotations

import re
import struct
from pathlib import Path

SRC = Path("/workspace/patch/Release/BARRACKS_FLAG_COMPLETE/_SPEC_DATA_ONE.big")
NEW = Path("/workspace/patch/Release/BUILDING_FLAG_HS_10x4/_SPEC_DATA_ONE.big")
OBJ_RE = re.compile(r"(?im)^Object\s+(\S+)")


def read_big(path: Path):
    data = path.read_bytes()
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name.replace("/", "\\").lower(), name, data[off : off + size]))
    return entries


def last_objects(entries):
    last = {}
    for _, name, blob in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        ms = list(OBJ_RE.finditer(text))
        for i, m in enumerate(ms):
            end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
            last[m.group(1)] = text[m.start() : end]
    return last


src = {k: (n, b) for k, n, b in read_big(SRC)}
new = {k: (n, b) for k, n, b in read_big(NEW)}
assert set(src) == set(new)
changed = [src[k][0] for k in src if src[k][1] != new[k][1]]
print("changed_count", len(changed))
for n in changed:
    print("CHANGED", n)

last_s = last_objects([(k, *src[k]) for k in src])
last_n = last_objects([(k, *new[k]) for k in new])

# Systems.ini non-power objects must match
for obj in last_s:
    if obj.startswith(("Japan_", "SouthKorea_", "Vietnam_")) and obj.endswith(
        ("_ChonmaHo", "_MIC", "_DefenseSite", "_Sam2")
    ):
        assert last_s[obj] == last_n[obj], obj

expect = {
    "India_PowerPlant": ("IN__INFlag_Hs", "BOX08"),
    "Pakistan_PowerPlant": ("PK__PKFlag_Hs", "BOX08"),
    "Libya_PowerPlant": ("LY__LYFlag_Hs", "BOX08"),
    "Syria_PowerPlant": ("SY__SYFlag_Hs", "BOX08"),
    "UAE_PowerPlant": ("AE__AEFlag_Hs", "BOX08"),
    "SaudiArabia_PowerPlant": ("SA__SAFlag_Hs", "BOX08"),
    "SouthAfrica_PowerPlant": ("ZA__ZAFlag_Hs", "BOX08"),
    "Japan_PowerPlant": ("JP__JPFlag_Hs", "BOX08"),
    "SouthKorea_PowerPlant": ("SK__SKFlag_Hs", "BOX08"),
    "Vietnam_PowerPlant": ("VN__VNFlag_Hs", "BOX08"),
    "India_SupplyCenter": ("IN__INFlag_Hs", "FLAG01"),
    "Pakistan_SupplyCenter": ("PK__PKFlag_Hs", "FLAG01"),
    "Libya_SupplyCenter": ("LY__LYFlag_Hs", "FLAG01"),
    "Syria_SupplyCenter": ("SY__SYFlag_Hs", "FLAG01"),
    "UAE_SupplyCenter": ("AE__AEFlag_Hs", "FLAG01"),
    "SaudiArabia_SupplyCenter": ("SA__SAFlag_Hs", "FLAG01"),
    "SouthAfrica_SupplyCenter": ("ZA__ZAFlag_Hs", "FLAG01"),
    "Japan_SupplyCenter": ("JP__JPFlag_Hs", "FLAG01"),
    "SouthKorea_SupplyCenter": ("SK__SKFlag_Hs", "FLAG01"),
    "Vietnam_SupplyCenter": ("VN__VNFlag_Hs", "FLAG01"),
    "India_WarFactory_T": ("IN__INFlag_Hs", "FLAG01"),
    "Pakistan_WarFactory_T": ("PK__PKFlag_Hs", "FLAG01"),
    "Libya_WarFactory_T": ("LY__LYFlag_Hs", "FLAG01"),
    "Syria_WarFactory_T": ("SY__SYFlag_Hs", "FLAG01"),
    "UAE_WarFactory_T": ("AE__AEFlag_Hs", "FLAG01"),
    "SaudiArabia_WarFactory_T": ("SA__SAFlag_Hs", "FLAG01"),
    "SouthAfrica_WarFactory_T": ("ZA__ZAFlag_Hs", "FLAG01"),
    "Japan_WarFactory": ("JP__JPFlag_Hs", "FLAG01"),
    "SouthKorea_WarFactory": ("SK__SKFlag_Hs", "FLAG01"),
    "Vietnam_WarFactory": ("VN__VNFlag_Hs", "FLAG01"),
    "India_CommandCenter": ("IN__INFlag_Hs", None),
    "Pakistan_CommandCenter": ("PK__PKFlag_Hs", None),
    "Libya_CommandCenter": ("LY__LYFlag_Hs", None),
    "Syria_CommandCenter": ("SY__SYFlag_Hs", None),
    "UAE_CommandCenter": ("AE__AEFlag_Hs", None),
    "SaudiArabia_CommandCenter": ("SA__SAFlag_Hs", None),
    "SouthAfrica_CommandCenter": ("ZA__ZAFlag_Hs", None),
    "Japan_CommandCenter": ("JP__JPFlag_Hs", "FLAG01"),
    "SouthKorea_CommandCenter": ("SK__SKFlag_Hs", "FLAG01"),
    "Vietnam_CommandCenter": ("VN__VNFlag_Hs", "FLAG01"),
}
for obj, (flag, hide_tok) in expect.items():
    body = last_n[obj]
    assert flag in body and "ModuleTag_03" in body, obj
    if hide_tok:
        assert hide_tok in body and "HideSubObject" in body, obj
    else:
        assert "HideSubObject" not in body, obj
    print("OK", obj, flag, "hide" if hide_tok else "nohide")

for obj in (
    "India_Barracks",
    "Pakistan_Barracks",
    "Japan_Barracks",
    "SouthKorea_Barracks",
    "Vietnam_Barracks",
    "Libya_Barracks",
    "Iraq_Barracks",
    "Iraq_PowerPlant",
    "Iraq_CommandCenter",
    "Egypt_PowerPlant",
):
    assert last_s[obj] == last_n[obj], obj
    print("OK frozen", obj)

# systems non-target
for obj, body in last_s.items():
    if obj in expect:
        continue
    if obj.startswith(("Japan_", "SouthKorea_", "Vietnam_", "JapanFinal", "SouthKoreaFinal", "VietnamFinal", "JapanDrone", "SouthKoreaDrone", "VietnamDrone")):
        if last_s[obj] != last_n[obj]:
            raise SystemExit(f"systems object drifted: {obj}")
print("OK systems non-targets")
print("REEXTRACT_PASS", "files_changed", len(changed))
