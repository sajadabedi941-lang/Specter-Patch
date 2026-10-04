#!/usr/bin/env python3
from __future__ import annotations

import re
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/BUILDING_FLAG_HS_10x4/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/BARRACKS_FLAG_COMPLETE/_SPEC_ART_ONE.big")
NEW_DATA = Path("/workspace/patch/Release/BUILDING_FLAG_SIZE_CC/_SPEC_DATA_ONE.big")
NEW_ART = Path("/workspace/patch/Release/BUILDING_FLAG_SIZE_CC/_SPEC_ART_ONE.big")
OBJ_RE = re.compile(r"(?im)^Object\s+(\S+)")
PIVOTS = 0x00000102
HALF_POLE = 17.492
LINE01 = {
    "PP": (-14.342, -32.269, 36.448),
    "SC": (56.662, 29.918, 8.617 + HALF_POLE),
    "WF": (53.595, 36.922, 5.945 + HALF_POLE),
    "CU": (61.513, -64.028, 0.767 + HALF_POLE),
    "CK": (14.259, -10.538, 19.156),
}
EXPECT = {
    "India_PowerPlant": ("IN__INFlag_HsPP", "BOX08", "LINE01"),
    "Pakistan_PowerPlant": ("PK__PKFlag_HsPP", "BOX08", "LINE01"),
    "Libya_PowerPlant": ("LY__LYFlag_HsPP", "BOX08", "LINE01"),
    "Syria_PowerPlant": ("SY__SYFlag_HsPP", "BOX08", "LINE01"),
    "UAE_PowerPlant": ("AE__AEFlag_HsPP", "BOX08", "LINE01"),
    "SaudiArabia_PowerPlant": ("SA__SAFlag_HsPP", "BOX08", "LINE01"),
    "SouthAfrica_PowerPlant": ("ZA__ZAFlag_HsPP", "BOX08", "LINE01"),
    "Japan_PowerPlant": ("JP__JPFlag_HsPP", "BOX08", "LINE01"),
    "SouthKorea_PowerPlant": ("SK__SKFlag_HsPP", "BOX08", "LINE01"),
    "Vietnam_PowerPlant": ("VN__VNFlag_HsPP", "BOX08", "LINE01"),
    "India_SupplyCenter": ("IN__INFlag_HsSC", "FLAG01", "LINE01"),
    "Pakistan_SupplyCenter": ("PK__PKFlag_HsSC", "FLAG01", "LINE01"),
    "Libya_SupplyCenter": ("LY__LYFlag_HsSC", "FLAG01", "LINE01"),
    "Syria_SupplyCenter": ("SY__SYFlag_HsSC", "FLAG01", "LINE01"),
    "UAE_SupplyCenter": ("AE__AEFlag_HsSC", "FLAG01", "LINE01"),
    "SaudiArabia_SupplyCenter": ("SA__SAFlag_HsSC", "FLAG01", "LINE01"),
    "SouthAfrica_SupplyCenter": ("ZA__ZAFlag_HsSC", "FLAG01", "LINE01"),
    "Japan_SupplyCenter": ("JP__JPFlag_HsSC", "FLAG01", "LINE01"),
    "SouthKorea_SupplyCenter": ("SK__SKFlag_HsSC", "FLAG01", "LINE01"),
    "Vietnam_SupplyCenter": ("VN__VNFlag_HsSC", "FLAG01", "LINE01"),
    "India_WarFactory_T": ("IN__INFlag_HsWF", "FLAG01", "LINE01"),
    "Pakistan_WarFactory_T": ("PK__PKFlag_HsWF", "FLAG01", "LINE01"),
    "Libya_WarFactory_T": ("LY__LYFlag_HsWF", "FLAG01", "LINE01"),
    "Syria_WarFactory_T": ("SY__SYFlag_HsWF", "FLAG01", "LINE01"),
    "UAE_WarFactory_T": ("AE__AEFlag_HsWF", "FLAG01", "LINE01"),
    "SaudiArabia_WarFactory_T": ("SA__SAFlag_HsWF", "FLAG01", "LINE01"),
    "SouthAfrica_WarFactory_T": ("ZA__ZAFlag_HsWF", "FLAG01", "LINE01"),
    "Japan_WarFactory": ("JP__JPFlag_HsWF", "FLAG01", "LINE01"),
    "SouthKorea_WarFactory": ("SK__SKFlag_HsWF", "FLAG01", "LINE01"),
    "Vietnam_WarFactory": ("VN__VNFlag_HsWF", "FLAG01", "LINE01"),
    "India_CommandCenter": ("IN__INFlag_HsCU", "F1", "FPOLE"),
    "Pakistan_CommandCenter": ("PK__PKFlag_HsCU", "F1", "FPOLE"),
    "Libya_CommandCenter": ("LY__LYFlag_HsCU", "F1", "FPOLE"),
    "Syria_CommandCenter": ("SY__SYFlag_HsCU", "F1", "FPOLE"),
    "UAE_CommandCenter": ("AE__AEFlag_HsCU", "F1", "FPOLE"),
    "SaudiArabia_CommandCenter": ("SA__SAFlag_HsCU", "F1", "FPOLE"),
    "SouthAfrica_CommandCenter": ("ZA__ZAFlag_HsCU", "F1", "FPOLE"),
    "Japan_CommandCenter": ("JP__JPFlag_HsCK", "FLAG01", "LINE01"),
    "SouthKorea_CommandCenter": ("SK__SKFlag_HsCK", "FLAG01", "LINE01"),
    "Vietnam_CommandCenter": ("VN__VNFlag_HsCK", "FLAG01", "LINE01"),
}


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


def walk(blob, start=0, end=None):
    if end is None:
        end = len(blob)
    pos = start
    while pos + 8 <= end:
        ctype, raw = struct.unpack_from("<II", blob, pos)
        size = raw & 0x7FFFFFFF
        has = bool(raw & 0x80000000)
        ds, de = pos + 8, min(pos + 8 + size, end)
        yield ctype, ds, de, has
        if has:
            yield from walk(blob, ds, de)
        pos = de


def line01(blob):
    for ctype, ds, de, has in walk(blob):
        if ctype != PIVOTS or has:
            continue
        for i in range((de - ds) // 60):
            off = ds + i * 60
            name = blob[off : off + 16].split(b"\x00", 1)[0]
            if name == b"LINE01":
                return struct.unpack_from("<fff", blob, off + 20)
    raise SystemExit("LINE01 missing")


src_d = {k: (n, b) for k, n, b in read_big(SRC_DATA)}
new_d = {k: (n, b) for k, n, b in read_big(NEW_DATA)}
src_a = {k: (n, b) for k, n, b in read_big(SRC_ART)}
new_a = {k: (n, b) for k, n, b in read_big(NEW_ART)}

assert set(src_d) == set(new_d)
changed = [src_d[k][0] for k in src_d if src_d[k][1] != new_d[k][1]]
print("data_changed", len(changed))
assert len(changed) == 40

added = [new_a[k][0] for k in new_a if k not in src_a]
print("art_added", len(added))
assert len(added) == 40
for k in src_a:
    assert src_a[k][1] == new_a[k][1], k
print("OK existing ART byte-identical")

for name in (
    r"art\w3d\in__inflag_hs.w3d",
    r"art\w3d\jp__jpflag_hs.w3d",
    r"art\w3d\irq_camp.w3d",
    r"art\w3d\us_command.w3d",
    r"art\w3d\nkr_command.w3d",
):
    assert src_a[name][1] == new_a[name][1]

last_s = last_objects([(k, *src_d[k]) for k in src_d])
last_n = last_objects([(k, *new_d[k]) for k in new_d])
for obj, (flag, tok_a, tok_b) in EXPECT.items():
    body = last_n[obj]
    assert flag in body and "ModuleTag_03" in body, obj
    assert tok_a in body and tok_b in body and "HideSubObject" in body, obj
    print("OK", obj, flag, tok_a, tok_b)

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

for obj, body in last_s.items():
    if obj in EXPECT:
        continue
    if obj.startswith(("Japan_", "SouthKorea_", "Vietnam_", "JapanFinal", "SouthKoreaFinal", "VietnamFinal", "JapanDrone", "SouthKoreaDrone", "VietnamDrone")):
        assert last_s[obj] == last_n[obj], obj
print("OK systems non-targets")

# LINE01 on new W3Ds
kind_of = {}
for obj, (flag, *_r) in EXPECT.items():
    kind_of[flag.lower()] = flag[-2:]
for k, (n, b) in new_a.items():
    if k not in src_a:
        kind = n[-6:-4]  # PP/SC/WF/CU/CK before .W3D
        xyz = line01(b)
        expect = LINE01[kind]
        assert all(abs(a - b) < 1e-2 for a, b in zip(xyz, expect)), (n, xyz, expect)
        assert len(b) == 20341, n
print("OK 40 LINE01 positions")

# barracks still use camp Flag_Hs
assert "IN__INFlag_Hs" in last_n["India_Barracks"]
assert "IN__INFlag_HsPP" not in last_n["India_Barracks"]
print("OK barracks still camp Flag_Hs")
print("REEXTRACT_PASS")
