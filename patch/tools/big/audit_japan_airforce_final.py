#!/usr/bin/env python3
"""Validate Japan air-force final pack against packed ART and locked faction files."""

from __future__ import annotations

import io
import re
import struct
import sys
from pathlib import Path

DATA = Path("/tmp/japan_airforce_final/_SPEC_DATA_ONE.big")
ART = Path("/tmp/japan_airforce_final/_SPEC_ART_ONE.big")
SRC_DATA = Path("/tmp/jp_sk_vn_donor_art/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/japan_airforce_final_audit.txt")

PURE_AA = {
    "JapanJetF15J": ("AIM120D_BVR_MRAAM_F22A", "AIM9X_HOBS_SRAAM_F22A"),
    "JapanJetF14Tomcat": ("AIM54A_BVR_AALRM", "AIM9M_Sidewinder_HSSRAAM"),
}

AG_BOMBISH = (
    "GBU",
    "JDAM",
    "Paveway",
    "ASM2",
    "AGM65",
    "AARGM",
    "AGM88",
    "Bomb",
    "Hydra",
    "Hellfire",
    "AGM114",
)

LOCKED_PATHS = (
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\Science.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_CommandCenter.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\Japan_VT72B.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\VT72B.ini",
)

LOCKED_CS = (
    "Japan_VT72BCommandSet",
    "SouthKorea_VT72BCommandSet",
    "Vietnam_VT72BCommandSet",
)

FORBIDDEN_MODELS = ("JP_F35B", "ENF35A", "LSFSX2", "Irq_", "Iraq_")


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


def last_object(entries, obj: str):
    hits = []
    for i, n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        if re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", t):
            m = re.search(rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)", t)
            hits.append((i, n, m.group(0) if m else t))
    return hits[-1] if hits else None


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
    src = parse_big(SRC_DATA)
    stems = set()
    for _, n, _ in art:
        base = n.replace("/", "\\").split("\\")[-1]
        if base.lower().endswith(".w3d"):
            stems.add(base[:-4])
    print("PACKED DATA", DATA, "files", len(data))
    print("PACKED ART", ART, "files", len(art), "w3d", len(stems))
    print()

    src_idx = {n.replace("/", "\\").lower(): b for _, n, b in src}
    dst_idx = {n.replace("/", "\\").lower(): b for _, n, b in data}
    for p in LOCKED_PATHS:
        key = p.replace("/", "\\").lower()
        if key in src_idx and src_idx[key] != dst_idx.get(key):
            errors.append(f"LOCKED FILE CHANGED {p}")
        else:
            print("locked file unchanged", p)

    cs = dst_idx[r"data\ini\commandset.ini".lower()].decode("latin1")
    src_cs = src_idx[r"data\ini\commandset.ini".lower()].decode("latin1")
    for name in LOCKED_CS:
        if named(cs, "CommandSet", name) != named(src_cs, "CommandSet", name):
            errors.append(f"LOCKED COMMANDSET CHANGED {name}")
        else:
            print("locked CommandSet unchanged", name)

    air = named(cs, "CommandSet", "Japan_AirfieldCommandSet")
    heavy = named(cs, "CommandSet", "Japan_HeavyAirBaseCommandSet")
    print("\nJapan_AirfieldCommandSet\n", air)
    print("\nJapan_HeavyAirBaseCommandSet\n", heavy)
    if "Command_ConstructJapanJetE767" in (air + heavy):
        errors.append("E-767 still in a Japan CommandSet")
    if "Command_SetRallyPoint" in air or "Command_Sell" in air:
        errors.append("fighter bar still has rally/sell")
    if "Command_ConstructJapanJetF35Japon" not in air:
        errors.append("F35Japon missing from fighter bar")
    if "Command_ConstructJapanJetF14Tomcat" not in air:
        errors.append("F-14 missing from fighter bar")
    if re.search(r"(?m)^\s+\d+\s*=\s*$", air or "") or re.search(r"(?m)^\s+\d+\s*=\s*$", heavy or ""):
        errors.append("empty CommandSet slot")

    cb = dst_idx[r"data\ini\commandbutton.ini".lower()].decode("latin1")
    if named(cb, "CommandButton", "Command_ConstructJapanJetE767"):
        errors.append("E-767 CommandButton still present")
    for btn, obj in (
        ("Command_ConstructJapanJetF35Japon", "JapanJetF35Japon"),
        ("Command_ConstructJapanJetF14Tomcat", "JapanJetF14Tomcat"),
        ("Command_FireJapanAH64Hydra", None),
    ):
        blk = named(cb, "CommandButton", btn)
        if not blk:
            errors.append(f"missing button {btn}")
            continue
        if obj and f"Object        = {obj}" not in blk and f"Object = {obj}" not in blk:
            if not re.search(rf"(?m)^\s*Object\s*=\s*{re.escape(obj)}\s*$", blk):
                errors.append(f"{btn} does not build {obj}")
        print("button ok", btn)

    weap = dst_idx[r"data\ini\weapon.ini".lower()].decode("latin1")
    if not named(weap, "Weapon", "Japan_Weapon_C130H_HeavyBomb"):
        errors.append("missing Japan_Weapon_C130H_HeavyBomb")
    else:
        bomb = named(weap, "Weapon", "Japan_Weapon_C130H_HeavyBomb")
        if "ClipSize                = 8" not in bomb and "ClipSize = 8" not in bomb:
            if "ClipSize" not in bomb or "8" not in bomb:
                errors.append("C-130 bomb clip is not 8")
        if "PrimaryDamageRadius     = 90.0" not in bomb and "PrimaryDamageRadius = 90.0" not in bomb:
            if "90.0" not in bomb:
                errors.append("C-130 bomb radius is not 90")
        print("C-130 heavy bomb ok")

    checks = {
        "JapanHelicopterCH47J": {
            "models": {"US_CH47F"},
            "anim": "US_CH47F.US_CH47F",
            "role": "TRANSPORT",
            "no_weapon": True,
            "cmd": "JapanCH47JTransportCommandSet",
        },
        "JapanHelicopterAH64D": {
            "models": {"LSFJapanAH64D", "LSFJapanAH64Dd"},
            "anim": "LSFJapanAH64D.LSFJapanAH64D",
            "role": "CAN_ATTACK",
            "weapons": {"30mm_M230E1_ChainGun", "8x_MRATGM_AGM114L", "70mm_Hydra_AH64E"},
            "forbid_weapons": {"GenericHeliGunnerSight"},
            "cmd": "JapanAH64DCommandSet",
            "not_transport": True,
        },
        "JapanHelicopterUH60J": {
            "models": {"US_UH60"},
            "anim": "US_UH60.US_UH60",
            "role": "CAN_ATTACK",
            "weapons": {"30mm_M230E1_ChainGun", "70mm_Hydra_AH64E"},
            "cmd": "JapanUH60JCommandSet",
            "not_transport": True,
        },
        "JapanJetE767": {
            "buildable_no": True,
        },
        "JapanUAVRQ4": {
            "models": {"US_RQ-4", "US_MQ-4"},
            "recon": True,
            "cmd": "JapanUAVRQ4CommandSet",
        },
        "JapanJetC130H": {
            "models": {"AVCargoPln", "AVCargoPln_D", "AVCargoPln_E"},
            "weapons": {"Japan_Weapon_C130H_HeavyBomb"},
            "cmd": "JapanC130HBomberCommandSet",
            "locomotor": "C130HLocomotor",
            "fire": True,
        },
        "JapanJetF35A": {
            "models": {"AVF-35", "AVF-35_D", "AVF-35_E"},
            "bone": "WEAPONA01",
            "weapons": {"AmericaF35C_AA_AIM120", "GBU_31V2_JDAM_F35C"},
        },
        "JapanJetF35Japon": {
            "models": {"US_F35A"},
            "bone": "WEAPONA01",
            "weapons": {"AIM120D_BVR_MRAAM_F35C", "GBU38_JDAM_F16C"},
        },
        "JapanJetX2Shinshin": {
            "models": {"LSFF22", "LSFF22d", "LSFF22k"},
            "bone": "MISSILEA01",
            "weapons": {"AIM120D_BVR_MRAAM_F22A", "AIM9X_HOBS_SRAAM_F22A"},
        },
        "JapanJetF14Tomcat": {
            "models": {"LSFIRF14A", "LSFIRF14Ad"},
            "bone": "MISSILEA01",
            "weapons": {"AIM54A_BVR_AALRM", "AIM9M_Sidewinder_HSSRAAM"},
        },
    }

    print("\n=== OBJECTS ===")
    for obj, spec in checks.items():
        hit = last_object(data, obj)
        if not hit:
            errors.append(f"missing object {obj}")
            continue
        _, path, text = hit
        models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text))
        weapons = set(re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", text))
        print(obj, "file", path)
        print("  models", sorted(models))
        print("  weapons", sorted(weapons))
        if spec.get("buildable_no"):
            if not re.search(r"(?m)^\s*Buildable\s*=\s*No\s*$", text):
                errors.append(f"{obj} not Buildable=No")
            if "IGNORED_IN_GUI" not in text:
                errors.append(f"{obj} not IGNORED_IN_GUI")
            print("  stubbed")
            continue
        missing_m = spec.get("models", set()) - models
        if missing_m:
            errors.append(f"{obj} missing models {missing_m}")
        for m in models:
            if m not in stems:
                errors.append(f"{obj} Model={m} not in packed ART")
            if m.startswith(FORBIDDEN_MODELS) or m in FORBIDDEN_MODELS:
                errors.append(f"{obj} forbidden model {m}")
        if spec.get("anim") and spec["anim"] not in text:
            errors.append(f"{obj} missing Animation {spec['anim']}")
        if spec.get("anim") and "AnimationMode = LOOP" not in text:
            errors.append(f"{obj} missing AnimationMode LOOP")
        if spec.get("role") and spec["role"] not in text:
            errors.append(f"{obj} missing KindOf {spec['role']}")
        if spec.get("not_transport") and re.search(r"(?m)^\s*KindOf\s*=.*\bTRANSPORT\b", text):
            errors.append(f"{obj} still TRANSPORT")
        if spec.get("no_weapon") and weapons:
            errors.append(f"{obj} should have no weapons, has {weapons}")
        need_w = spec.get("weapons", set())
        if need_w - weapons:
            errors.append(f"{obj} missing weapons {need_w - weapons}")
        bad_w = spec.get("forbid_weapons", set()) & weapons
        if bad_w:
            errors.append(f"{obj} still has forbidden weapons {bad_w}")
        if spec.get("cmd") and spec["cmd"] not in text:
            errors.append(f"{obj} CommandSet != {spec['cmd']}")
        if spec.get("bone") and spec["bone"] not in text:
            errors.append(f"{obj} missing launch bone {spec['bone']}")
        if spec.get("recon"):
            if "StealthDetectorUpdate" not in text:
                errors.append(f"{obj} missing StealthDetectorUpdate")
            if "REVEALS_ENEMY_PATHS" not in text:
                errors.append(f"{obj} missing REVEALS_ENEMY_PATHS")
        if spec.get("locomotor") and spec["locomotor"] not in text:
            errors.append(f"{obj} missing locomotor {spec['locomotor']}")
        if spec.get("fire") and "Command_FireMainWeapon" not in named(cs, "CommandSet", spec["cmd"]):
            errors.append(f"{obj} commandset missing FireMainWeapon")
        if text.count("AIUpdate") > 1:
            errors.append(f"{obj} has multiple AIUpdate modules")
        if "Buildable = NoScale" in text or "Buildable = NoScale =" in text:
            errors.append(f"{obj} glued Buildable/Scale")

    print("\n=== WEAPON DIVERSITY ===")
    fighter_objs = [
        "JapanJetF35A",
        "JapanJetF35B",
        "JapanJetF15J",
        "JapanJetF15DJ",
        "JapanJetF2A",
        "JapanJetF2B",
        "JapanJetF2Kai",
        "JapanJetF4EJKai",
        "JapanJetX2Shinshin",
        "JapanJetF16",
        "JapanJetFA18",
        "JapanJetFX",
        "JapanJetF35Japon",
        "JapanJetF14Tomcat",
    ]
    loadouts = {}
    for obj in fighter_objs:
        hit = last_object(data, obj)
        if not hit:
            errors.append(f"missing fighter {obj}")
            continue
        text = hit[2]
        weapons = tuple(re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", text))
        loadouts[obj] = weapons
        print(obj, weapons)
        if obj in PURE_AA:
            if any(any(k.lower() in w.lower() for k in ("GBU", "JDAM", "Paveway", "ASM", "AGM65", "Bomb")) for w in weapons):
                errors.append(f"{obj} is supposed to be pure AA but has AG weapon {weapons}")
        elif obj != "JapanJetX2Shinshin":
            if not any(any(k.lower() in w.lower() for k in ("GBU", "JDAM", "Paveway", "ASM", "AGM", "AARGM")) for w in weapons):
                errors.append(f"{obj} has no varied AG weapon {weapons}")
    sigs = list(loadouts.values())
    if len(set(sigs)) < 8:
        errors.append(f"fighter loadouts still too similar: {len(set(sigs))} unique of {len(sigs)}")

    overlay = r"data\ini\commandset_japan.ini"
    if overlay in dst_idx:
        errors.append("packed overlay CommandSet_Japan.ini")

    print("\n=== RESULT ===")
    if errors:
        for e in errors:
            print("FAIL", e)
        return 1
    print("PASS Japan air-force final")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
