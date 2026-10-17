#!/usr/bin/env python3
"""Audit global F-35 visuals and Japan EW/Prowler roster."""

from __future__ import annotations

import io
import re
import struct
import sys
from pathlib import Path

DATA = Path("/tmp/japan_f35_ew/_SPEC_DATA_ONE.big")
ART = Path("/tmp/japan_f35_ew/_SPEC_ART_ONE.big")
SRC = Path("/tmp/japan_airforce_final/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/japan_f35_ew_audit.txt")

FORBIDDEN = {"ENF35A", "JP_F35B", "JP_F35B_D", "LSFUSAF35A", "LSFUSAF35Ad", "LSFUSAF35Ak", "JPF35A", "LSFSX2", "LSFF22"}
F35B = ("BritainJetF35B", "ItalyJetF35B", "NatoJetF35B", "JapanJetF35B", "SouthKoreaJetF35B", "AmericaJetF35BJSF")
F35A = ("GermanyJetF35A", "ItalyJetF35A", "JapanJetF35A", "SouthKoreaJetF35A", "TurkeyJetF35A")
LOCKED_CS = ("Japan_VT72BCommandSet", "SouthKorea_VT72BCommandSet", "Vietnam_VT72BCommandSet")


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
    ):
        if p in src_idx and src_idx[p] != dst_idx.get(p):
            errors.append(f"LOCKED CHANGED {p}")
        else:
            print("locked ok", p)

    cs = dst_idx[r"data\ini\commandset.ini"].decode("latin1")
    src_cs = src_idx[r"data\ini\commandset.ini"].decode("latin1")
    for name in LOCKED_CS:
        if named(cs, "CommandSet", name) != named(src_cs, "CommandSet", name):
            errors.append(f"locked CS {name}")
    air = named(cs, "CommandSet", "Japan_AirfieldCommandSet")
    heavy = named(cs, "CommandSet", "Japan_HeavyAirBaseCommandSet")
    print(air)
    print(heavy)
    if "E767" in (air + heavy):
        errors.append("E-767 still listed")
    if "Command_Sell" in air or "Command_SetRallyPoint" in air:
        errors.append("rally/sell on fighter bar")
    for need in ("F35Japon", "F18G", "EA6B", "F14Tomcat"):
        if need not in air:
            errors.append(f"missing {need} on fighter bar")
    if "LSFF22" in (last_object(data, "JapanJetX2Shinshin") or ("", ""))[1]:
        errors.append("X-2 still uses F-22 mesh")

    cb = dst_idx[r"data\ini\commandbutton.ini"].decode("latin1")
    for btn, obj in (
        ("Command_ConstructJapanJetF35Japon", "JapanJetF35Japon"),
        ("Command_ConstructJapanJetF18G", "JapanJetF18G"),
        ("Command_ConstructJapanJetEA6B", "JapanJetEA6B"),
        ("Command_ConstructJapanJetF14Tomcat", "JapanJetF14Tomcat"),
    ):
        blk = named(cb, "CommandButton", btn)
        if not blk:
            errors.append(f"missing button {btn}")
            continue
        if not re.search(rf"(?m)^\s*Object\s*=\s*{re.escape(obj)}\s*$", blk):
            errors.append(f"{btn} != {obj}")
        img = re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", blk)
        print("button", btn, img.group(1) if img else "?")
    if named(cb, "CommandButton", "Command_ConstructJapanJetE767"):
        errors.append("E-767 button remains")

    print("\n=== F-35 GLOBAL ===")
    for obj in (*F35A, *F35B):
        hit = last_object(data, obj)
        if not hit:
            errors.append(f"missing {obj}")
            continue
        models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", hit[1]))
        print(obj, sorted(models))
        bad = models & FORBIDDEN
        if bad:
            errors.append(f"{obj} forbidden models {bad}")
        for m in models:
            if m not in stems:
                errors.append(f"{obj} Model={m} not in ART")
        if obj in F35B:
            weps = set(re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", hit[1]))
            if any(re.search(r"GBU|JDAM|Paveway|ASM|Bomb", w, re.I) for w in weps):
                errors.append(f"{obj} F-35B still has AG {weps}")

    print("\n=== JAPAN KEY OBJECTS ===")
    checks = {
        "JapanJetF35Japon": {"US_F35A"},
        "JapanJetF18G": {"US_EA18G"},
        "JapanJetEA6B": {"EA6"},
        "JapanJetF14Tomcat": {"LSFIRF14A", "LSFIRF14Ad"},
        "JapanJetX2Shinshin": {"JP_X2Shinshin", "JP_X2Shinshin_D"},
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
        models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", hit[1]))
        print(obj, sorted(models), "weapons", re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", hit[1]))
        if not (need & models) and need:
            errors.append(f"{obj} missing donor models {need} have {models}")
        for m in models:
            if m not in stems:
                errors.append(f"{obj} Model={m} missing ART")
        if obj.startswith("JapanHelicopter") and "AnimationMode = LOOP" not in hit[1]:
            errors.append(f"{obj} rotor LOOP missing")
        if obj == "JapanJetX2Shinshin" and "LSFF22" in models:
            errors.append("duplicate F-22 mesh still on X-2")
        if obj == "JapanUAVRQ4" and "StealthDetectorUpdate" not in hit[1]:
            errors.append("RQ-4 missing recon detector")
        if obj == "JapanJetC130H" and "Japan_Weapon_C130H_HeavyBomb" not in hit[1]:
            errors.append("C-130 missing heavy bomb")
        if hit[1].count("AIUpdate") > 1:
            errors.append(f"{obj} multiple AIUpdate")

    if "EA6.tga" not in tex and "ea6.tga" not in {t.lower() for t in tex}:
        errors.append("EA6.tga not packed")
    if "USAEA6Prowler.tga" not in tex:
        errors.append("USAEA6Prowler.tga not packed")
    mi = dst_idx[r"data\ini\mappedimages\handcreated\handcreatedmappedimages.ini"].decode("latin1")
    if not named(mi, "MappedImage", "USAEA6Prowler"):
        errors.append("MappedImage USAEA6Prowler missing")
    if r"data\ini\commandset_japan.ini" in dst_idx:
        errors.append("packed overlay CommandSet_Japan.ini")

    e767 = last_object(data, "JapanJetE767")
    if e767 and not re.search(r"(?m)^\s*Buildable\s*=\s*No\s*$", e767[1]):
        errors.append("E-767 still buildable")

    print("\n=== RESULT ===")
    if errors:
        for e in errors:
            print("FAIL", e)
        return 1
    print("PASS japan F-35 / EW / Prowler")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
