#!/usr/bin/env python3
"""Packed-BIG audit for F-35B lock and F35Japon / F-18G / EA-6B ControlBar fix."""

from __future__ import annotations

import io
import re
import struct
import sys
from pathlib import Path

DATA = Path("/tmp/usa_jp_visual_buttons/_SPEC_DATA_ONE.big")
ART = Path("/tmp/japan_aircraft_final/_SPEC_ART_ONE.big")
SRC = Path("/tmp/japan_aircraft_final/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/usa_jp_visual_buttons_audit.txt")

F35B = (
    "BritainJetF35B",
    "ItalyJetF35B",
    "NatoJetF35B",
    "JapanJetF35B",
    "SouthKoreaJetF35B",
    "AmericaJetF35BJSF",
)
FORBIDDEN_F35B = {"ENF35A", "JP_F35B", "JP_F35B_D", "LSFUSAF35A", "JPF35A", "US_F35A"}
CSF_REQUIRED = (
    "CONTROLBAR:F18G",
    "CONTROLBAR:autreF18Gif",
    "CONTROLBAR:EA6Prowler",
    "CONTROLBAR:EA6Prowleri",
    "CONTROLBAR:F35BJSF",
    "CONTROLBAR:F35BJSFif",
    "CONTROLBAR:ConstructJapanJetF18G",
    "CONTROLBAR:ToolTipJapanJetF18G",
    "CONTROLBAR:ConstructJapanJetEA6B",
    "CONTROLBAR:ToolTipJapanJetEA6B",
    "CONTROLBAR:ConstructJapanJetF35Japon",
    "CONTROLBAR:ToolTipJapanJetF35Japon",
    "CONTROLBAR:ToolTipUSABuildF35C_AA",
    "CONTROLBAR:EA18G",
    "CONTROLBAR:AmericaF35BJSF",
    "OBJECT:JapanJetF18G",
    "OBJECT:JapanJetEA6B",
    "OBJECT:JapanJetF35Japon",
    "OBJECT:AmericaJetF35BJSF",
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


def walk_csf(blob):
    pos = 24
    nlab = struct.unpack_from("<I", blob, 8)[0]
    out = {}
    for _ in range(nlab):
        if blob[pos : pos + 4] != b" LBL":
            break
        nstr, namelen = struct.unpack_from("<II", blob, pos + 4)
        pos += 12
        name = blob[pos : pos + namelen].decode("latin1", "replace")
        pos += namelen
        vals = []
        for _s in range(nstr):
            mag = blob[pos : pos + 4]
            slen = struct.unpack_from("<I", blob, pos + 4)[0]
            pos += 8
            raw = blob[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(x ^ 0xFF for x in raw).decode("utf-16-le", "replace")
            if mag == b"WRTS":
                elen = struct.unpack_from("<I", blob, pos)[0]
                pos += 4 + elen
            vals.append(val)
        out[name] = vals[0] if vals else ""
    return out


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
        r"data\ini\commandset.ini",
    ):
        if p == r"data\ini\commandset.ini":
            continue
        if src_idx.get(p) != dst_idx.get(p):
            errors.append(f"LOCKED CHANGED {p}")
        else:
            print("locked ok", p)

    src_cs = src_idx[r"data\ini\commandset.ini"].decode("latin1")
    dst_cs = dst_idx[r"data\ini\commandset.ini"].decode("latin1")
    if src_cs != dst_cs:
        errors.append("CommandSet.ini changed")
    else:
        print("locked ok commandset.ini")

    cb = dst_idx[r"data\ini\commandbutton.ini"].decode("latin1")
    mi = dst_idx[r"data\ini\mappedimages\handcreated\handcreatedmappedimages.ini"].decode("latin1")
    wini = dst_idx[r"data\ini\weapon.ini"].decode("latin1")
    labels = walk_csf(dst_idx[r"data\english\generals.csf"])

    print("\n=== SOURCE TABLE ===")
    rows = [
        ("F-35B", "AVF-35 / _D / _E", "JP_F35B, ENF35A, JPF35A, LSFUSAF35A", "housecolor-only or non-JSF"),
        ("F35Japon", "JPF35A / JPF35Ad / JPF35Ak + f35.dds", "US_F35A, JP_F35B, ENF35A, SPEC_OLD_F35, AVF-35", "Japan-named F-35A donor, distinct from US_F35A"),
        ("F-18G", "US_EA18G + F18G/autreF18G -> EA18GTB.tga", "F18SEA, AmF18A, Nat_ea18g-only", "exact Growler mesh used by AmericaJetEA18G"),
        ("EA-6B", "EA6 + EA6Prowler -> USAEA6Prowler.tga", "US_EA18G, F18SEA", "exact packed Prowler mesh"),
    ]
    for need, chosen, rejected, reason in rows:
        print(f"{need:10} | {chosen}")
        print(f"{'':10} | rejected: {rejected}")
        print(f"{'':10} | {reason}")

    print("\n=== F-35B AUDIT ===")
    f35b_ok = True
    for obj in F35B:
        hit = last_object(data, obj)
        if not hit:
            errors.append(f"missing {obj}")
            f35b_ok = False
            continue
        models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", hit[1]))
        weps = set(re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", hit[1]))
        print(obj, sorted(models), sorted(weps))
        if models - {"AVF-35", "AVF-35_D", "AVF-35_E"}:
            errors.append(f"{obj} not AVF-35 family {models}")
            f35b_ok = False
        if models & FORBIDDEN_F35B:
            errors.append(f"{obj} forbidden {models & FORBIDDEN_F35B}")
            f35b_ok = False
        for m in models:
            if m not in stems:
                errors.append(f"{obj} Model={m} missing ART")
                f35b_ok = False
        if any(re.search(r"GBU|JDAM|Paveway|ASM|Bomb|AGM65|AGM88", w, re.I) for w in weps):
            errors.append(f"{obj} F-35B still has AG {weps}")
            f35b_ok = False
        if "AmericaF35C_AA_AIM120" not in weps or not any("AIM9X" in w for w in weps):
            errors.append(f"{obj} F-35B missing AIM-120/AIM-9X {weps}")
            f35b_ok = False
        src_hit = last_object(src, obj)
        if src_hit and re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", src_hit[1]) != re.findall(
            r"(?m)^\s*Model\s*=\s*(\S+)", hit[1]
        ):
            errors.append(f"{obj} F-35B model changed this pass")
            f35b_ok = False
    print("F-35B", "AUDIT_OK" if f35b_ok and not any("F-35B" in e or e.startswith(F35B[0][:4]) for e in errors) else "FAIL")
    if f35b_ok:
        print("AUDIT_OK F-35B remains AVF-35 JSF air-to-air on USA/Japan/SK/Britain/Italy/NATO")

    print("\n=== F35JAPON ===")
    hit = last_object(data, "JapanJetF35Japon")
    if not hit:
        errors.append("missing JapanJetF35Japon")
    else:
        models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", hit[1]))
        weps = set(re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", hit[1]))
        bones = set(re.findall(r"(?m)^\s*WeaponLaunchBone\s*=\s*\S+\s+(\S+)", hit[1]))
        print("models", sorted(models), "bones", sorted(bones), "weps", sorted(weps))
        if models != {"JPF35A", "JPF35Ad", "JPF35Ak"}:
            errors.append(f"F35Japon models {models}")
        if "US_F35A" in models:
            errors.append("F35Japon still generic US_F35A")
        if bones and bones != {"MISSILEA01"}:
            errors.append(f"F35Japon bones {bones}")
        for m in models:
            if m not in stems:
                errors.append(f"F35Japon Model={m} missing ART")
        for texname in ("f35.dds", "f35d.dds", "f35k.dds"):
            if texname not in tex:
                errors.append(f"missing {texname}")
        if "GBU38_JDAM_F16C" not in weps:
            errors.append("F35Japon lost AG loadout")

    print("\n=== F-18G ===")
    hit = last_object(data, "JapanJetF18G")
    if not hit:
        errors.append("missing JapanJetF18G")
    else:
        models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", hit[1]))
        weps = set(re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", hit[1]))
        port = re.search(r"(?m)^\s*SelectPortrait\s*=\s*(\S+)", hit[1])
        img = re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", hit[1])
        print("models", sorted(models), "portrait", port.group(1) if port else None, "image", img.group(1) if img else None, "weps", sorted(weps))
        if models != {"US_EA18G"}:
            errors.append(f"F-18G models {models}")
        if "US_EA18G" not in stems:
            errors.append("US_EA18G missing ART")
        if "ALQ_99_RadarJamming" not in weps or "AGM88G_AARGM-ER" not in weps:
            errors.append(f"F-18G lost EW loadout {weps}")
        if any(re.search(r"GBU|JDAM|Paveway|Bomb", w, re.I) for w in weps):
            errors.append(f"F-18G became a bomber {weps}")
        if not port or port.group(1) != "F18G":
            errors.append("F-18G SelectPortrait != F18G")
        if not img or img.group(1) != "autreF18G":
            errors.append("F-18G ButtonImage != autreF18G")

    print("\n=== EA-6B ===")
    hit = last_object(data, "JapanJetEA6B")
    if not hit:
        errors.append("missing JapanJetEA6B")
    else:
        models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", hit[1]))
        weps = set(re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+(\S+)", hit[1]))
        port = re.search(r"(?m)^\s*SelectPortrait\s*=\s*(\S+)", hit[1])
        print("models", sorted(models), "portrait", port.group(1) if port else None, "weps", sorted(weps))
        if models != {"EA6"}:
            errors.append(f"EA-6B models {models}")
        if "EA6" not in stems:
            errors.append("EA6 missing ART")
        if weps != {"Japan_Weapon_EA6B_GuidedBomb"}:
            errors.append(f"EA-6B weapons {weps}")
        if "GermanyJetTornadoIDS_WpnBombHvy" in weps:
            errors.append("EA-6B still uses Tornado weapon name")
        if not named(wini, "Weapon", "Japan_Weapon_EA6B_GuidedBomb"):
            errors.append("Japan_Weapon_EA6B_GuidedBomb missing")
        else:
            wblk = named(wini, "Weapon", "Japan_Weapon_EA6B_GuidedBomb")
            if "ClipSize = 6" not in wblk and "ClipSize=6" not in wblk.replace(" ", ""):
                errors.append("EA-6B weapon clip != 6")
            if "GBU24_GuidedBombObject" not in wblk:
                errors.append("EA-6B weapon lost GBU-24 projectile")
        if not port or port.group(1) != "EA6Prowler":
            errors.append("EA-6B portrait != EA6Prowler")

    print("\n=== BUTTONS / MAPPED / CSF ===")
    for btn, obj, img in (
        ("Command_ConstructJapanJetF18G", "JapanJetF18G", "F18G"),
        ("Command_ConstructJapanJetEA6B", "JapanJetEA6B", "EA6Prowler"),
        ("Command_ConstructJapanJetF35Japon", "JapanJetF35Japon", "SPEC_JapanJetF35A"),
    ):
        blk = named(cb, "CommandButton", btn)
        if not blk:
            errors.append(f"missing button {btn}")
            continue
        if f"Object        = {obj}" not in blk and f"Object = {obj}" not in blk.replace(" ", ""):
            if not re.search(rf"(?m)^\s*Object\s*=\s*{re.escape(obj)}\s*$", blk):
                errors.append(f"{btn} Object != {obj}")
        if not re.search(rf"(?m)^\s*ButtonImage\s*=\s*{re.escape(img)}\s*$", blk):
            errors.append(f"{btn} ButtonImage != {img}")
        print("button", btn, "ok")
    for name in ("F18G", "autreF18G", "EA6Prowler", "F35BJSF", "SPEC_JapanJetF35A", "EA18G", "AmericaF35BJSF"):
        found = named(mi, "MappedImage", name)
        if not found:
            # EA18G / AmericaF35BJSF live in other mapped files
            found = False
            for _, n, b in data:
                if "mappedimage" in n.lower():
                    t = b.decode("latin1", "replace")
                    if named(t, "MappedImage", name):
                        found = True
                        break
        if not found:
            errors.append(f"missing MappedImage {name}")
        else:
            print("mapped", name, "ok")
    for key in CSF_REQUIRED:
        if key not in labels:
            errors.append(f"missing CSF {key}")
        else:
            print("csf", key, "=", labels[key][:70])

    if r"data\ini\commandset_japan.ini" in dst_idx:
        errors.append("packed overlay CommandSet_Japan.ini")

    print("\n=== RESULT ===")
    if errors:
        for e in errors:
            print("FAIL", e)
        return 1
    print("PASS usa/japan visual button fix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
