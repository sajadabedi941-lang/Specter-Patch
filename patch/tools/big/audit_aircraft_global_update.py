#!/usr/bin/env python3
"""Packed-BIG audit for the global aircraft + Iraq/NK/Iran pass."""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from collections import Counter
from pathlib import Path

DATA = Path("/tmp/aircraft_global_update/_SPEC_DATA_ONE.big")
ART = Path("/tmp/aircraft_global_update/_SPEC_ART_ONE.big")
SRC = Path("/tmp/aircraft_donor_update/_SPEC_DATA_ONE.big")


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


def field(part, name):
    m = re.search(rf"(?im)^\s*{re.escape(name)}\s*=\s*(.+)$", part)
    return m.group(1).strip() if m else None


def scales(part):
    return [float(x) for x in re.findall(r"(?im)^\s*Scale\s*=\s*([0-9.]+)", part)]


def main() -> int:
    errors = []
    data = parse_big(DATA)
    art = parse_big(ART)
    art_keys = {n.replace("/", "\\").lower() for n, _ in art}

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
    btn = ""
    for n, b in data:
        ln = n.replace("/", "\\").lower()
        if ln.endswith("\\commandset.ini"):
            cs += decode(b) + "\n"
        if ln.endswith("\\commandbutton.ini"):
            btn += decode(b) + "\n"

    print("=== ART ===")
    for k in (
        r"art\textures\f14tb.tga",
        r"art\w3d\lsfirf14a.w3d",
        r"art\textures\lsff14a.dds",
        r"art\w3d\avreaper.w3d",
        r"art\w3d\rus_tu22m3m.w3d",
        r"art\w3d\lsfrussiayr76.w3d",
        r"art\w3d\chjh7a.w3d",
    ):
        ok = k in art_keys
        print(("OK" if ok else "MISSING"), k)
        if not ok:
            errors.append(f"missing ART {k}")

    print("\n=== SCALE / WEAPON ===")
    expect_scale = {
        "IranJetMig21Bis": 0.92,
        "VietnamJetMig21bis": 0.90,
        "IndiaJetMig21Bison": 1.00,
        "NorthKoreaJetMig21PF": 0.90,
        "IraqJetF16IQ": 0.98,
        "NorthKoreaJetJ7": 0.94,
        "NorthKoreaJetJ7B": 0.92,
        "NorthKoreaJetMig29UB": 0.98,
        "ChinaJetJ7": 1.22,  # unchanged
    }
    for obj, sc in expect_scale.items():
        part, src = find_obj(obj)
        if not part:
            errors.append(f"missing {obj}")
            print("MISSING", obj)
            continue
        scs = scales(part)
        print(obj, "scale", scs, "weps", weapons(part)[:5])
        if scs and abs(scs[0] - sc) > 0.02:
            errors.append(f"{obj} scale {scs} != {sc}")
        if obj == "ChinaJetJ7" and "China_Weapon_FAB_J7" not in weapons(part) and "China_Weapon_FAB_J7" not in part:
            errors.append("China J-7 weapon changed")
        if obj == "IranJetMig21Bis" and "Iran_Weapon_Bomb_Mig21" not in part:
            errors.append("Iran MiG-21bis weapon changed")
        if obj == "NorthKoreaJetMig29UB" and "Kab500_LeaserGuidedBomb" not in part:
            errors.append("NK MiG-29UB missing guided bomb")
        if obj == "VietnamJetMig21bis" and "China_Weapon_Bomb_Q5" not in part:
            errors.append("Vietnam bis bomb not swapped")

    print("\n=== NEW / CLONE OBJECTS ===")
    clones = {
        "IraqJetF14Tomcat": ({"LSFIRF14A", "LSFIRF14Ad"}, "Specter_Weapon_JH7A2_Bomb6"),
        "NorthKoreaBomberIl28": ({"RUS_TU22M3M"}, "Specter_Weapon_SU34MF_Bomb6"),
        "NorthKoreaJetIL76": ({"LSFRussiaYR76", "LSFRussiaYR76d", "LSFRussiaYR76k"}, None),
        "NorthKoreaUAVSaetbyol": ({"AVReaper"}, None),
    }
    for obj, (md_ok, wep) in clones.items():
        part, src = find_obj(obj)
        if not part:
            errors.append(f"missing clone {obj}")
            print("MISSING", obj)
            continue
        md = models(part)
        print(obj, "models", sorted(md), "weps", weapons(part)[:4], src)
        extra = md - md_ok - {""}
        if extra:
            errors.append(f"{obj} unexpected models {extra}")
        if wep and wep not in weapons(part) and wep not in part:
            errors.append(f"{obj} missing weapon {wep}")
        if obj == "NorthKoreaBomberIl28" and "KH101" in part:
            errors.append("Il-28 still has Tu-22 cruise missile")
        if obj == "NorthKoreaUAVSaetbyol":
            if "CAN_ATTACK" in (field(part, "KindOf") or ""):
                errors.append("Saetbyol still CAN_ATTACK")
            if weapons(part):
                errors.append(f"Saetbyol has weapons {weapons(part)}")
            if "StealthDetectorUpdate" not in part:
                errors.append("Saetbyol missing stealth detect")
            if "REVEALS_ENEMY_PATHS" not in (field(part, "KindOf") or ""):
                errors.append("Saetbyol missing REVEALS_ENEMY_PATHS")

    # Russia Tu-22 and China J-7 untouched vs source
    src_entries = parse_big(SRC)
    def src_obj(name):
        hit = None
        for n, b in src_entries:
            if n.lower().endswith(".ini") and "\\object\\" in n.replace("/", "\\").lower():
                p = last_object(decode(b), name)
                if p:
                    hit = p
        return hit

    for locked in ("RussiaJetTu22M3M", "ChinaJetJ7", "IranJetSu35S"):
        a, b = find_obj(locked)[0], src_obj(locked)
        if a and b and locked == "RussiaJetTu22M3M":
            if models(a) != models(b):
                errors.append("Russia Tu-22M3 visual changed")
        if locked == "IranJetSu35S" and a:
            if "Iran_Weapon_R77_Su35" not in a:
                errors.append("Iran Su-35S weapons changed")

    print("\n=== COMMANDSETS ===")
    def slots_of(name):
        m = re.search(rf"(?ms)^CommandSet {re.escape(name)}\s*\n(.*?)(^End\s*$)", cs)
        if not m:
            return None
        return {int(a): b for a, b in re.findall(r"(?im)^\s*(\d+)\s*=\s*(\S+)", m.group(1))}

    iraq_ab = slots_of("Iraq_AirfieldCommandSet")
    iraq_hv = slots_of("Iraq_HeavyAirBaseCommandSet")
    nk_hv = slots_of("NorthKorea_HeavyAirBaseCommandSet")
    iran = slots_of("IranExpandedAirfieldCommandSet")
    print("Iraq airfield", iraq_ab)
    print("Iraq heavy", iraq_hv)
    print("NK heavy", nk_hv)
    print("Iran expanded", iran)
    if not iraq_ab or iraq_ab.get(15) != "Command_ConstructIraq_Su-24MR":
        errors.append("Iraq airfield missing Su-24MR unlock")
    if iraq_ab and any("Tu-22" in v or "Tu22" in v for v in iraq_ab.values()):
        errors.append("Iraq airfield still has Tu-22")
    if not iraq_hv or iraq_hv.get(1) != "Command_ConstructIraqJetF14Tomcat":
        errors.append("Iraq heavy missing Tomcat")
    if iraq_hv and any("Tu-22" in v or "Tu22" in v for v in iraq_hv.values()):
        errors.append("Iraq heavy still has Tu-22")
    if not nk_hv or nk_hv.get(4) != "Command_ConstructNorthKoreaBomberIl28":
        errors.append("NK heavy missing Il-28")
    if not nk_hv or nk_hv.get(6) != "Command_ConstructNorthKoreaUAVSaetbyol":
        errors.append("NK heavy missing Saetbyol")

    print("\n=== BUTTONS ===")
    names = re.findall(r"(?m)^CommandButton\s+(\S+)", btn)
    counts = Counter(names)
    for want in [
        "Command_ConstructIraqJetF16IQ",
        "Command_ConstructIraqJetF14Tomcat",
        "Command_ConstructIranJetF14AM",
        "Command_ConstructIranJetF4E",
        "Command_ConstructIranJetMig21Bis",
        "Command_ConstructIranJetF7N",
        "Command_ConstructIranJetSu35S",
        "Command_ConstructNorthKoreaJetMig21",
        "Command_ConstructNorthKoreaJetMig21PF",
        "Command_ConstructNorthKoreaJetJ7",
        "Command_ConstructNorthKoreaJetJ7B",
        "Command_ConstructNorthKoreaJetMig29UB",
        "Command_ConstructNorthKoreaBomberIl28",
        "Command_ConstructNorthKoreaJetIL76",
        "Command_ConstructNorthKoreaUAVSaetbyol",
        "Command_ConstructChinaJetJ11Flanker",
    ]:
        c = counts.get(want, 0)
        print(want, c)
        if c != 1:
            errors.append(f"{want} count={c}")

    # locked files
    src_h = {n.replace("/", "\\").lower(): hashlib.sha256(b).hexdigest() for n, b in src_entries}
    new_h = {n.replace("/", "\\").lower(): hashlib.sha256(b).hexdigest() for n, b in data}
    for lp in [r"data\ini\playertemplate.ini", r"data\ini\science.ini"]:
        if src_h.get(lp) != new_h.get(lp):
            errors.append(f"LOCKED changed {lp}")

    # Iraq airfield T unlocked
    part, _ = find_obj("Iraq_Airfield_T")
    if part:
        if "Iraq_AirfieldCommandSet_T" in part and field(part, "CommandSet") != "Iraq_AirfieldCommandSet":
            errors.append("Iraq_Airfield_T still tier-locked")
        if "CommandSetUpgrade" in part:
            errors.append("Iraq_Airfield_T still has CommandSetUpgrade")

    # China slots still donor-update
    pla = slots_of("PLAAirfieldCommandSet")
    if pla and pla.get(14) != "Command_ConstructChinaJetJ11Flanker":
        errors.append("China J-11 Flanker slot lost")

    status = "PACKED_AUDIT_OK" if not errors else "PACKED_AUDIT_FAIL"
    print("\n=== ERRORS ===")
    for e in errors:
        print(" ", e)
    print(status)
    dsha = hashlib.sha256(DATA.read_bytes()).hexdigest()
    asha = hashlib.sha256(ART.read_bytes()).hexdigest()
    report = [
        "SPECTER AIRCRAFT GLOBAL UPDATE — PACKED AUDIT",
        status,
        f"DATA SHA256 {dsha}",
        f"ART  SHA256 {asha}",
        "",
        "Static packed-BIG verification only. This environment cannot launch Zero Hour.",
        "In-game produce / fire / land tests remain with the user.",
        "",
        "Errors: none" if not errors else "Errors:\n" + "\n".join("  " + e for e in errors),
        "",
    ]
    text = "\n".join(report) + "\n"
    for p in [
        Path("/opt/cursor/artifacts/aircraft_global_update_audit.txt"),
        Path("/workspace/patch/Release/docs/AIRCRAFT_GLOBAL_AUDIT.txt"),
    ]:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        print("wrote", p)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
