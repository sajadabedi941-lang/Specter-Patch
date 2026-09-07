#!/usr/bin/env python3
"""Full Japan aircraft final-completion audit against packed BIGs."""

from __future__ import annotations

import io
import re
import struct
import sys
from pathlib import Path

DATA = Path("/tmp/japan_aircraft_final/_SPEC_DATA_ONE.big")
ART = Path("/tmp/japan_aircraft_final/_SPEC_ART_ONE.big")
SRC = Path("/tmp/japan_f35_ew/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/japan_aircraft_final_audit.txt")

FORBIDDEN_MODELS = {
    "ENF35A",
    "JP_F35B",
    "JP_F35B_D",
    "LSFUSAF35A",
    "LSFUSAF35Ad",
    "LSFUSAF35Ak",
    "JPF35A",
    "JPF35Ad",
    "JPF35Ak",
    "LSFSX2",
    "LSFF22",
}
F35B = (
    "BritainJetF35B",
    "ItalyJetF35B",
    "NatoJetF35B",
    "JapanJetF35B",
    "SouthKoreaJetF35B",
    "AmericaJetF35BJSF",
)
F35A = (
    "GermanyJetF35A",
    "ItalyJetF35A",
    "JapanJetF35A",
    "SouthKoreaJetF35A",
    "TurkeyJetF35A",
)
LOCKED_CS = (
    "Japan_VT72BCommandSet",
    "SouthKorea_VT72BCommandSet",
    "Vietnam_VT72BCommandSet",
    "Japan_CommandCenterCommandSet",
    "SouthKorea_CommandCenterCommandSet",
    "Vietnam_CommandCenterCommandSet",
)
AA_ONLY = {
    "JapanJetF35B": {"AmericaF35C_AA_AIM120", "AIM9X_HOBS_SRAAM_F35C"},
    "JapanJetF15J": {"AmericaF35C_AA_AIM120", "AIM9X_HOBS_SRAAM_F22A"},
}
UNIQUE_AG = {
    "JapanJetF35A": "GBU_31V2_JDAM_F35C",
    "JapanJetF15DJ": "GBU_31V2_JDAM_F15E",
    "JapanJetF2A": "Gbu-12II_Paveway",
    "JapanJetF2B": "2x_GBU12II_F16CMB50",
    "JapanJetF2Kai": "Japan_Weapon_ASM2_F2A",
    "JapanJetF4EJKai": "1x_AGM65F_FA18F",
    "JapanJetX2Shinshin": "2x_GBU24_2000lb_F16CMB50",
    "JapanJetF16": "GBU_31V1_JDAM_F16C",
    "JapanJetF18G": "AGM88G_AARGM-ER",
    "JapanJetF35Japon": "GBU38_JDAM_F16C",
    "JapanJetEA6B": "GermanyJetTornadoIDS_WpnBombHvy",
}
FIGHTER_SLOTS = {
    1: "Command_ConstructJapanJetF35A",
    2: "Command_ConstructJapanJetF35B",
    3: "Command_ConstructJapanJetF15J",
    4: "Command_ConstructJapanJetF15DJ",
    5: "Command_ConstructJapanJetF2A",
    6: "Command_ConstructJapanJetF2B",
    7: "Command_ConstructJapanJetF2Kai",
    8: "Command_ConstructJapanJetF4EJKai",
    9: "Command_ConstructJapanJetX2Shinshin",
    10: "Command_ConstructJapanJetF16",
    11: "Command_ConstructJapanJetF18G",
    12: "Command_ConstructJapanJetEA6B",
    13: "Command_ConstructJapanJetF35Japon",
    14: "Command_ConstructJapanJetF14Tomcat",
}
CSF_KEYS = (
    b"CONTROLBAR:ConstructJapanJetEA6B",
    b"CONTROLBAR:ToolTipJapanJetEA6B",
    b"CONTROLBAR:ConstructJapanJetF18G",
    b"CONTROLBAR:ToolTipJapanJetF18G",
    b"CONTROLBAR:ConstructJapanJetF35Japon",
    b"CONTROLBAR:ToolTipJapanJetF35Japon",
    b"CONTROLBAR:ConstructJapanJetF14Tomcat",
    b"CONTROLBAR:ToolTipJapanJetF14Tomcat",
)


def parse_big(path: Path):
    data = path.read_bytes()
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for i in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((i, name, data[eoff : eoff + esz]))
    return entries


def named(text, kind, name):
    m = re.search(rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$", text)
    return m.group(0) if m else None


def last_object(entries, obj):
    hits = []
    for i, n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        if re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", t):
            m = re.search(rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)", t)
            hits.append((n, m.group(0) if m else t))
    return hits[-1] if hits else None


def weapons(blk: str):
    return set(re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", blk))


def models(blk: str):
    return set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", blk))


def main() -> int:
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        code = _run()
    finally:
        sys.stdout = old
    text = buf.getvalue()
    print(text, end="")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text)
    print("wrote", REPORT)
    return code


def _run() -> int:
    errors = []
    data = parse_big(DATA)
    art = parse_big(ART)
    src = parse_big(SRC)
    stems = set()
    tex = set()
    for _, n, _ in art:
        base = n.replace("/", "\\").split("\\")[-1]
        if base.lower().endswith(".w3d"):
            stems.add(base[:-4])
        if base.lower().endswith((".tga", ".dds")):
            tex.add(base)
    print("DATA", len(data), "ART", len(art), "w3d", len(stems))

    src_idx = {n.replace("/", "\\").lower(): b for _, n, b in src}
    dst_idx = {n.replace("/", "\\").lower(): b for _, n, b in data}
    for p in (
        r"data\ini\playertemplate.ini",
        r"data\ini\science.ini",
        r"data\ini\object\specter\japan self-defense forces\buildings\japan_commandcenter.ini",
        r"data\ini\object\specter\japan self-defense forces\tracked\japan_vt72b.ini",
        r"data\ini\object\specter\japan self-defense forces\buildings\japan_largeairbase.ini",
        r"data\ini\object\specter\japan self-defense forces\buildings\japan_heavyairbase.ini",
    ):
        if p in src_idx and src_idx[p] != dst_idx.get(p):
            errors.append(f"LOCKED CHANGED {p}")
        else:
            print("locked ok", p)
    if r"data\ini\commandset_japan.ini" in dst_idx:
        errors.append("packed overlay CommandSet_Japan.ini")

    wini = dst_idx[r"data\ini\weapon.ini"].decode("latin1")
    weapon_names = set(re.findall(r"(?m)^Weapon\s+(\S+)\s*$", wini))
    cs = dst_idx[r"data\ini\commandset.ini"].decode("latin1")
    src_cs = src_idx[r"data\ini\commandset.ini"].decode("latin1")
    cb = dst_idx[r"data\ini\commandbutton.ini"].decode("latin1")
    for name in LOCKED_CS:
        if named(cs, "CommandSet", name) != named(src_cs, "CommandSet", name):
            errors.append(f"locked CS {name}")

    air = named(cs, "CommandSet", "Japan_AirfieldCommandSet")
    heavy = named(cs, "CommandSet", "Japan_HeavyAirBaseCommandSet")
    print(air)
    print(heavy)
    if not air or not heavy:
        errors.append("missing Japan air CommandSet")
        return 1
    if "E767" in (air + heavy):
        errors.append("E-767 still listed")
    if "Command_Sell" in air or "Command_SetRallyPoint" in air:
        errors.append("rally/sell on fighter bar")
    for slot, btn in FIGHTER_SLOTS.items():
        if not re.search(rf"(?m)^\s*{slot}\s*=\s*{re.escape(btn)}\s*$", air):
            errors.append(f"slot {slot} != {btn}")
    for slot in range(1, 15):
        if not re.search(rf"(?m)^\s*{slot}\s*=\s*\S+", air):
            errors.append(f"empty fighter slot {slot}")
    for slot, btn in re.findall(r"(?m)^\s*(\d+)\s*=\s*(\S+)", air):
        if not named(cb, "CommandButton", btn):
            errors.append(f"missing button {btn}")
        else:
            obj = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", named(cb, "CommandButton", btn))
            if obj and not last_object(data, obj.group(1)):
                errors.append(f"{btn} Object={obj.group(1)} missing")
    if named(cb, "CommandButton", "Command_ConstructJapanJetE767"):
        errors.append("E-767 button remains")
    if not named(cs, "CommandSet", "JapanEA6BBomberCommandSet"):
        errors.append("missing JapanEA6BBomberCommandSet")
    if not named(cs, "CommandSet", "JapanC130HBomberCommandSet"):
        errors.append("missing JapanC130HBomberCommandSet")

    csf = dst_idx[r"data\english\generals.csf"]
    for key in CSF_KEYS:
        if key.upper() not in csf.upper():
            errors.append(f"missing CSF {key.decode()}")

    print("\n=== F-35 GLOBAL ===")
    for obj in (*F35A, *F35B):
        hit = last_object(data, obj)
        if not hit:
            errors.append(f"missing {obj}")
            continue
        mods = models(hit[1])
        weps = weapons(hit[1])
        print(obj, sorted(mods), sorted(weps))
        bad = mods & FORBIDDEN_MODELS
        if bad:
            errors.append(f"{obj} forbidden models {bad}")
        for m in mods:
            if m not in stems:
                errors.append(f"{obj} Model={m} not in ART")
        if obj in F35A and mods != {"US_F35A"}:
            errors.append(f"{obj} F-35A must be US_F35A, have {mods}")
        if obj in F35B and (mods - {"AVF-35", "AVF-35_D", "AVF-35_E"}):
            errors.append(f"{obj} F-35B must stay AVF-35 JSF, have {mods}")
        if obj in F35B and any(re.search(r"GBU|JDAM|Paveway|ASM|Bomb|AGM65|AGM88", w, re.I) for w in weps):
            errors.append(f"{obj} F-35B still has AG {weps}")

    print("\n=== JAPAN LOADOUTS ===")
    ag_seen = {}
    for obj, need in UNIQUE_AG.items():
        hit = last_object(data, obj)
        if not hit:
            errors.append(f"missing {obj}")
            continue
        weps = weapons(hit[1])
        print(obj, sorted(weps))
        if need not in weps:
            errors.append(f"{obj} missing unique AG {need} have {weps}")
        if need not in weapon_names:
            errors.append(f"Weapon {need} not defined")
        ag_seen.setdefault(need, []).append(obj)
    for wpn, objs in ag_seen.items():
        if len(objs) > 1:
            errors.append(f"shared AG {wpn} on {objs}")
    for obj, need in AA_ONLY.items():
        hit = last_object(data, obj)
        weps = weapons(hit[1]) if hit else set()
        print(obj, "AA", sorted(weps))
        extra = weps - need
        if extra:
            errors.append(f"{obj} AA-only extra {extra}")
        missing = need - weps
        if missing:
            errors.append(f"{obj} AA-only missing {missing}")
        if any(re.search(r"GBU|JDAM|Paveway|ASM|Bomb|AGM", w, re.I) for w in weps):
            errors.append(f"{obj} AA-only still has AG {weps}")

    print("\n=== KEY OBJECTS ===")
    checks = {
        "JapanJetF35Japon": {"US_F35A"},
        "JapanJetF18G": {"US_EA18G"},
        "JapanJetEA6B": {"EA6"},
        "JapanJetF14Tomcat": {"LSFIRF14A", "LSFIRF14Ad"},
        "JapanJetX2Shinshin": {"JP_X2Shinshin", "JP_X2Shinshin_D"},
        "JapanJetF15DJ": {"LSFISF15E", "LSFISF15Ed"},
        "JapanHelicopterCH47J": {"US_CH47F"},
        "JapanHelicopterAH64D": {"LSFJapanAH64D", "LSFJapanAH64Dd"},
        "JapanHelicopterUH60J": {"US_UH60"},
        "JapanUAVRQ4": {"US_RQ-4"},
        "JapanJetC130H": {"AVCargoPln"},
    }
    for obj, need in checks.items():
        hit = last_object(data, obj)
        if not hit:
            errors.append(f"missing {obj}")
            continue
        mods = models(hit[1])
        weps = weapons(hit[1])
        cmd = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", hit[1])
        print(obj, sorted(mods), sorted(weps), cmd.group(1) if cmd else None)
        if not (need & mods):
            errors.append(f"{obj} missing donor models {need} have {mods}")
        if "LSFISF15ED" in mods:
            errors.append("F-15DJ damaged stem still LSFISF15ED")
        for m in mods:
            if m not in stems:
                errors.append(f"{obj} Model={m} missing ART")
            if m in FORBIDDEN_MODELS:
                errors.append(f"{obj} forbidden {m}")
        if obj.startswith("JapanHelicopter") and "AnimationMode = LOOP" not in hit[1]:
            errors.append(f"{obj} rotor LOOP missing")
        if obj.startswith("JapanHelicopter") and not re.search(r"(?m)^\s*Animation\s*=", hit[1]):
            errors.append(f"{obj} rotor Animation missing")
        if obj == "JapanHelicopterCH47J" and weps:
            errors.append(f"CH-47J must stay unarmed {weps}")
        if obj == "JapanHelicopterAH64D" and not {"30mm_M230E1_ChainGun", "8x_MRATGM_AGM114L", "70mm_Hydra_AH64E"} <= weps:
            errors.append(f"AH-64D incomplete combat load {weps}")
        if obj == "JapanHelicopterUH60J" and not {"30mm_M230E1_ChainGun", "70mm_Hydra_AH64E", "GenericHeliRWR"} <= weps:
            errors.append(f"UH-60J incomplete support load {weps}")
        if obj == "JapanUAVRQ4" and weps:
            errors.append(f"RQ-4 must stay unarmed {weps}")
        if obj == "JapanUAVRQ4" and "StealthDetectorUpdate" not in hit[1]:
            errors.append("RQ-4 missing recon detector")
        if obj == "JapanJetC130H" and "Japan_Weapon_C130H_HeavyBomb" not in weps:
            errors.append("C-130 missing heavy bomb")
        if obj == "JapanJetC130H" and cmd and cmd.group(1) != "JapanC130HBomberCommandSet":
            errors.append("C-130 wrong CommandSet")
        if obj == "JapanJetEA6B" and cmd and cmd.group(1) != "JapanEA6BBomberCommandSet":
            errors.append("EA-6B wrong CommandSet")
        if obj == "JapanJetF18G" and "ALQ_99_RadarJamming" not in weps:
            errors.append("F-18G missing EW jammer")
        if hit[1].count("AIUpdate") > 1:
            errors.append(f"{obj} multiple AIUpdate")

    e767 = last_object(data, "JapanJetE767")
    if e767 and not re.search(r"(?m)^\s*Buildable\s*=\s*No\s*$", e767[1]):
        errors.append("E-767 still buildable")

    if "EA6.tga" not in tex and "ea6.tga" not in {t.lower() for t in tex}:
        errors.append("EA6.tga not packed")
    if "USAEA6Prowler.tga" not in tex:
        errors.append("USAEA6Prowler.tga not packed")

    print("\n=== RESULT ===")
    if errors:
        for e in errors:
            print("FAIL", e)
        return 1
    print("PASS japan aircraft final")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
