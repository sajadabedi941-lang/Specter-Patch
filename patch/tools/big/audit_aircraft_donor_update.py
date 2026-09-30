#!/usr/bin/env python3
"""Packed-BIG audit for the aircraft donor update."""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from collections import Counter
from pathlib import Path

DATA = Path("/tmp/aircraft_donor_update/_SPEC_DATA_ONE.big")
ART = Path("/tmp/aircraft_donor_update/_SPEC_ART_ONE.big")
SRC = Path("/tmp/usa_donor_aircraft_visuals/_SPEC_DATA_ONE.big")


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


def decode(blob: bytes) -> str:
    if blob[:2] == b"\xff\xfe":
        return blob.decode("utf-16-le", "replace")
    return blob.decode("latin1", "replace")


def last_object(text, name):
    hit = None
    for p in re.split(r"(?m)(?=^Object(?:Reskin)?\s+\S+)", text):
        if re.match(rf"(?m)^Object(?:Reskin)?\s+{re.escape(name)}\b", p):
            hit = p
    return hit


def models(part):
    return set(re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", part))


def weapons(part):
    return re.findall(r"(?im)^\s*Weapon\s*=\s*\S+\s+(\S+)", part)


def main() -> int:
    errors = []
    data = parse_big(DATA)
    art = parse_big(ART)
    art_keys = {n.replace("/", "\\").lower() for n, _ in art}
    art_stems = {n.replace("/", "\\").split("\\")[-1].lower() for n, _ in art}

    def find_obj(name):
        hit = None
        src = None
        for n, b in data:
            if not n.lower().endswith(".ini"):
                continue
            if "\\object\\" not in n.replace("/", "\\").lower():
                continue
            part = last_object(decode(b), name)
            if part:
                hit, src = part, n
        return hit, src

    cs = ""
    wini = ""
    btn = ""
    for n, b in data:
        ln = n.replace("/", "\\").lower()
        if ln.endswith("\\commandset.ini"):
            cs = decode(b)
        if ln.endswith("\\weapon.ini"):
            wini = decode(b)
        if "commandbutton" in ln and ln.endswith(".ini"):
            btn += decode(b) + "\n"

    checks = [
        (r"art\w3d\ea6.w3d", "EA6"),
        (r"art\w3d\lsfusaf35a.w3d", "F35A"),
        (r"art\w3d\lsfusaf15e.w3d", "F15E"),
        (r"art\w3d\lsfsu35.w3d", "SU35"),
        (r"art\w3d\chjh7a.w3d", "JH7"),
        (r"art\textures\chfbc.dds", "chfbc"),
        (r"art\textures\feibaotb.tga", "FEIBAO"),
        (r"art\textures\jian11tb.tga", "JIAN11"),
    ]
    print("=== ART ===")
    for k, label in checks:
        ok = k in art_keys
        print(("OK" if ok else "MISSING"), k)
        if not ok:
            errors.append(f"missing ART {k}")

    expect = {
        "AmericaJetF18Prowler": ({"EA6"}, "Specter_Weapon_JH7A2_Bomb6"),
        "AmericaJetB52H": ({"US_B52H"}, "China_Weapon_FAB_H6K"),
        "AmericaJetC17Visual": ({"IUAC17HXNew"}, None),
        "AmericaJetAuterF22": ({"LSFUSAF15E", "LSFUSAF15Ed", "LSFUSAF15Ek"}, "China_Weapon_Bomb_Q5"),
        "AmericaJetF35C": ({"LSFUSAF35A", "LSFUSAF35Ad", "None"}, "Specter_Weapon_SU34MF_Bomb6"),
        "RussiaHelicopterKA52": ({"RUS_Ka52M2", "RUS_Ka52M2D"}, "12x_ATGM_9K121_Vikhr"),
        "RussiaJetTu95": ({"CWCruTu95", "CWCruTu95_d", "CWCruTu95_k"}, "China_Weapon_FAB_H6K"),
        "RussiaJetSu35S": ({"LSFSU35", "LSFSU35d"}, "Specter_Weapon_JH7A2_Bomb6"),
        "ChinaDroneCH5": ({"CHI_CH5", "CHI_CH5D", "CHI_CH5R"}, None),
        "ChinaHelicopterZ18A": ({"CHI_Z18A", "CHI_Z18A_D", "CHI_Z18A_R"}, None),
        "ChinaJetJ11Flanker": ({"LSFJ11B", "LSFJ11Bd", "LSFJ11Bk"}, "Specter_Weapon_SU34MF_Bomb6"),
        "ChinaJetJ15": ({"J15JZ"}, None),
        "ChinaJetFEIBAO": ({"CHJH7A", "ChJh7a_r"}, "Specter_Weapon_JH7A2_Bomb4"),
        "ChinaBomberH6K_B21A": ({"h6k"}, "Specter_Weapon_B21A_Bomb7"),
        "ChinaBomberH6K": ({"h6k"}, None),
    }
    print("\n=== OBJECTS ===")
    for obj, (md_ok, wep) in expect.items():
        part, src = find_obj(obj)
        if not part:
            errors.append(f"missing object {obj}")
            print("MISSING", obj)
            continue
        md = models(part)
        extra = md - md_ok - {""}
        print(f"{obj} models={sorted(md)} weapons={weapons(part)[:6]} src={src}")
        if extra:
            errors.append(f"{obj} unexpected models {extra}")
        if wep and wep not in weapons(part) and wep not in part:
            errors.append(f"{obj} missing weapon {wep}")
        if obj == "AmericaJetF18Prowler":
            if re.search(r"(?im)ParticleSysBone\s*=\s*Engine01", part):
                errors.append("Prowler still has Engine01 particles")
            if "PRIMARY ;SECONDARY" in part:
                errors.append("Prowler comment leftover")
        if obj == "RussiaHelicopterKA52":
            if "PRIMARY ;SECONDARY TERTIARY" in part:
                errors.append("KA52 still has commented weapon slots")
            if "PRIMARY SECONDARY TERTIARY" not in part:
                errors.append("KA52 slots not enabled")
        if obj == "ChinaDroneCH5":
            if "PRODUCED_AT_HELIPAD" in part or re.search(r"KindOf.*DRONE", part):
                errors.append("CH5 still helipad/drone")
            if "JetAIUpdate" not in part:
                errors.append("CH5 missing JetAIUpdate")
            if "AIRCRAFT" not in part:
                errors.append("CH5 KindOf missing AIRCRAFT")
        if obj == "AmericaJetC17Visual":
            if not re.search(r"(?im)^\s*Slots\s*=\s*64\b", part):
                errors.append("Starlifter Slots != 64")
        if obj == "ChinaHelicopterZ18A":
            if not re.search(r"(?im)AllowInsideKindOf\s*=\s*INFANTRY VEHICLE", part):
                errors.append("Z18A transport not Chinook-like")

    print("\n=== WEAPONS ===")
    for w, clip in [
        ("Specter_Weapon_JH7A2_Bomb6", "6"),
        ("Specter_Weapon_JH7A2_Bomb4", "4"),
        ("Specter_Weapon_SU34MF_Bomb6", "6"),
        ("Specter_Weapon_B21A_Bomb7", "7"),
    ]:
        m = re.search(rf"(?ms)^Weapon {re.escape(w)}\s*\n.*?^End\s*$", wini)
        if not m:
            errors.append(f"missing weapon {w}")
            continue
        cm = re.search(r"(?im)^\s*ClipSize\s*=\s*(\S+)", m.group(0))
        print(w, "ClipSize", cm.group(1) if cm else "?")
        if not cm or cm.group(1) != clip:
            errors.append(f"{w} ClipSize {cm.group(1) if cm else None} != {clip}")

    print("\n=== CHINA SLOTS ===")
    for csn, s13, s14 in [
        ("PLAAirfieldCommandSet", "Command_ConstructChinaJetJ15", "Command_ConstructChinaJetJ11Flanker"),
        ("China_LargeAirBaseCommandSet", "Command_ConstructChinaJetJ15", "Command_ConstructChinaJetJ11Flanker"),
        ("China_HeavyAirBaseCommandSet", "Command_ConstructChinaBomberH6K_B21A", "Command_ConstructChinaJetFEIBAO"),
    ]:
        m = re.search(rf"(?ms)^CommandSet {csn}\s*\n(.*?)(^End\s*$)", cs)
        if not m:
            errors.append(f"missing {csn}")
            continue
        slots = {int(a): b for a, b in re.findall(r"(?im)^\s*(\d+)\s*=\s*(\S+)", m.group(1))}
        print(csn, "13", slots.get(13), "14", slots.get(14))
        if slots.get(13) != s13:
            errors.append(f"{csn} 13={slots.get(13)}")
        if slots.get(14) != s14:
            errors.append(f"{csn} 14={slots.get(14)}")

    print("\n=== BUTTONS once ===")
    names = re.findall(r"(?m)^CommandButton\s+(\S+)", btn)
    counts = Counter(names)
    for want in NEW_EXPECT if False else [
        "Command_ConstructChinaJetJ11Flanker",
        "Command_ConstructChinaJetFEIBAO",
        "Command_ConstructChinaBomberH6K_B21A",
    ]:
        print(want, counts.get(want, 0))
        if counts.get(want, 0) != 1:
            errors.append(f"{want} count={counts.get(want, 0)}")

    # no CommandSet under Object
    for n, _ in data:
        ln = n.replace("/", "\\").lower()
        if "\\object\\" in ln and "commandset" in ln.split("\\")[-1]:
            errors.append(f"CommandSet under Object {n}")

    src = parse_big(SRC)
    src_h = {n.replace("/", "\\").lower(): hashlib.sha256(b).hexdigest() for n, b in src}
    new_h = {n.replace("/", "\\").lower(): hashlib.sha256(b).hexdigest() for n, b in data}
    for lp in [r"data\ini\playertemplate.ini", r"data\ini\science.ini"]:
        if src_h.get(lp) != new_h.get(lp):
            errors.append(f"LOCKED changed {lp}")

    status = "PACKED_AUDIT_OK" if not errors else "PACKED_AUDIT_FAIL"
    print("\n=== ERRORS ===")
    for e in errors:
        print(" ", e)
    print(status)
    dsha = hashlib.sha256(DATA.read_bytes()).hexdigest()
    asha = hashlib.sha256(ART.read_bytes()).hexdigest()
    report = [
        "SPECTER AIRCRAFT DONOR UPDATE — PACKED AUDIT",
        status,
        f"DATA SHA256 {dsha}",
        f"ART  SHA256 {asha}",
        "",
        "Static packed-BIG verification only. This environment cannot launch Zero Hour.",
        "In-game fire/land/produce tests remain with the user.",
        "",
        "Errors: none" if not errors else "Errors:\n" + "\n".join("  " + e for e in errors),
        "",
    ]
    text = "\n".join(report) + "\n"
    for p in [
        Path("/opt/cursor/artifacts/aircraft_donor_update_audit.txt"),
        Path("/workspace/patch/Release/docs/AIRCRAFT_DONOR_UPDATE_AUDIT.txt"),
    ]:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        print("wrote", p)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
