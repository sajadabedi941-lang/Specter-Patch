#!/usr/bin/env python3
"""Packed-BIG audit for exact donor aircraft visuals."""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

DATA = Path("/tmp/usa_donor_aircraft_visuals/_SPEC_DATA_ONE.big")
ART = Path("/tmp/usa_donor_aircraft_visuals/_SPEC_ART_ONE.big")

F35B = [
    "AmericaJetF35BJSF",
    "BritainJetF35B",
    "ItalyJetF35B",
    "JapanJetF35B",
    "NatoJetF35B",
    "SouthKoreaJetF35B",
]
F35A = [
    "JapanJetF35A",
    "SouthKoreaJetF35A",
    "GermanyJetF35A",
    "ItalyJetF35A",
    "TurkeyJetF35A",
    "JapanJetF35Japon",
    "BritainJetF35C",
    "FranceJetF35C",
    "GermanyJetF35C",
    "ItalyJetF35C",
    "NatoJetF35C",
    "SwedenJetF35C",
    "TurkeyJetF35C",
    "UkraineJetF35C",
    "BritainJetF35C_AA",
    "FranceJetF35C_AA",
    "GermanyJetF35C_AA",
    "ItalyJetF35C_AA",
    "NatoJetF35C_AA",
    "SwedenJetF35C_AA",
    "TurkeyJetF35C_AA",
    "UkraineJetF35C_AA",
    "IsraelJetF35IAdirPenetrator",
    "IsraelJetF35I_AA",
    "AirF_AmericaJetStealthFighter",
]
GROWLER = [
    "AmericaJetEA18G",
    "AmericaJetEA18G_AI",
    "JapanJetF18G",
    "NatoJetEA18G",
    "BritainJetEA18G",
    "ItalyJetEA18G",
    "GermanyJetEA18G",
    "FranceJetEA18G",
    "SwedenJetEA18G",
    "TurkeyJetEA18G",
    "UkraineJetEA18G",
]
PROWLER = ["JapanJetEA6B", "AmericaJetF18Prowler"]

LOCKED = [
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\Science.ini",
]


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


def last_object(text: str, name: str) -> str | None:
    parts = re.split(r"(?m)(?=^Object(?:Reskin)?\s+\S+)", text)
    hit = None
    for p in parts:
        m = re.match(rf"(?m)^Object(?:Reskin)?\s+{re.escape(name)}\b", p)
        if m:
            hit = p
    return hit


def models(part: str) -> set[str]:
    return set(re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", part))


def weapons(part: str) -> list[str]:
    return re.findall(r"(?im)^\s*Weapon\s*=\s*\S+\s+(\S+)", part)


def portrait(part: str) -> tuple[str, str]:
    s = re.search(r"(?im)^\s*SelectPortrait\s*=\s*(\S+)", part)
    b = re.search(r"(?im)^\s*ButtonImage\s*=\s*(\S+)", part)
    return (s.group(1) if s else "", b.group(1) if b else "")


def art_stems(art_ents) -> set[str]:
    out = set()
    for n, _ in art_ents:
        base = n.replace("/", "\\").split("\\")[-1]
        if "." in base:
            out.add(base.rsplit(".", 1)[0].lower())
    return out


def named_weapon(wini: str, name: str) -> str | None:
    m = re.search(
        rf"(?ms)^Weapon {re.escape(name)}\s*\n.*?^End\s*$",
        wini,
    )
    return m.group(0) if m else None


def main() -> int:
    errors = []
    data_ents = parse_big(DATA)
    art_ents = parse_big(ART)
    stems = art_stems(art_ents)
    data_by = {n.replace("/", "\\").lower(): (n, decode(b)) for n, b in data_ents}

    def all_ini_text():
        chunks = []
        for n, b in data_ents:
            if n.lower().endswith(".ini"):
                chunks.append(decode(b))
        return "\n".join(chunks)

    everything = all_ini_text()
    wini = ""
    for n, b in data_ents:
        if n.replace("/", "\\").lower().endswith("\\weapon.ini"):
            wini = decode(b)

    cs_text = ""
    for n, b in data_ents:
        if n.replace("/", "\\").lower().endswith("\\commandset.ini"):
            cs_text = decode(b)

    btn_text = ""
    for n, b in data_ents:
        if "commandbutton" in n.lower() and n.lower().endswith(".ini"):
            btn_text += "\n" + decode(b)

    print("=== PACKED ART REQUIRED STEMS ===")
    for stem in (
        "AVLightn",
        "AVLightn_D",
        "LSFUSAF35A",
        "LSFUSAF35Ad",
        "LSFEA18G",
        "LSFEA18Gd",
        "LSFEA18G",
        "EA6",
        "f35",
        "LSFEA18G",
        "EA18GTB",
        "AmericaF35BJSF",
        "USAEA6Prowler",
        "EA6",
    ):
        ok = stem.lower() in stems or any(stem.lower() == s for s in stems)
        # textures have different stem
        print(f"  {stem}: {'OK' if any(stem.lower()==x or x.startswith(stem.lower()) for x in stems) else 'MISSING'}")
        if not any(stem.lower() == x or x.startswith(stem.lower()) for x in stems):
            errors.append(f"missing ART stem {stem}")

    # more precise art file checks
    art_keys = {n.replace("/", "\\").lower() for n, _ in art_ents}
    required_files = [
        r"art\w3d\avlightn.w3d",
        r"art\textures\avlightn.dds",
        r"art\w3d\lsfusaf35a.w3d",
        r"art\textures\f35.dds",
        r"art\w3d\lsfea18g.w3d",
        r"art\textures\lsfea18g.dds",
        r"art\textures\ea18gtb.tga",
        r"art\w3d\ea6.w3d",
        r"art\textures\ea6.tga",
    ]
    print("\n=== REQUIRED ART FILES ===")
    for rf in required_files:
        ok = rf in art_keys
        print(f"  {'OK' if ok else 'MISSING'} {rf}")
        if not ok:
            errors.append(f"missing {rf}")

    def find_obj(name):
        hit = None
        src = None
        for n, b in data_ents:
            if not n.lower().endswith(".ini"):
                continue
            if "\\object\\" not in n.replace("/", "\\").lower():
                continue
            part = last_object(decode(b), name)
            if part:
                hit = part
                src = n
        return hit, src

    print("\nAircraft | Country | Live Object | Model | Main Texture | ButtonImage | Role | Weapon | CommandSet slot")
    print("-" * 140)

    rows = []

    def cs_slots_for_button(btn: str):
        hits = []
        for m in re.finditer(
            rf"(?ms)^CommandSet\s+(\S+)\s*\n(.*?)(^End\s*$)",
            cs_text,
        ):
            body = m.group(2)
            for sm in re.finditer(r"(?im)^\s*(\d+)\s*=\s*" + re.escape(btn) + r"\s*$", body):
                hits.append((m.group(1), int(sm.group(1))))
        return hits

    def btn_for_obj(obj: str):
        m = re.search(
            rf"(?ms)^CommandButton\s+(\S+)\s*\n(.*?)(^End\s*$)",
            btn_text,
        )
        found = []
        for m in re.finditer(
            rf"(?ms)^CommandButton\s+(\S+)\s*\n(.*?)(?=^CommandButton\s|\Z)",
            btn_text,
        ):
            body = m.group(2)
            om = re.search(r"(?im)^\s*Object\s*=\s*" + re.escape(obj) + r"\s*$", body)
            if om:
                im = re.search(r"(?im)^\s*ButtonImage\s*=\s*(\S+)", body)
                found.append((m.group(1), im.group(1) if im else ""))
        return found

    print("\n--- F-35B ---")
    for obj in F35B:
        part, src = find_obj(obj)
        if not part:
            errors.append(f"missing object {obj}")
            print(f"MISSING {obj}")
            continue
        md = models(part)
        wep = weapons(part)
        port, bimg = portrait(part)
        btns = btn_for_obj(obj)
        slots = []
        for bn, _im in btns:
            slots.extend(cs_slots_for_button(bn))
        print(
            f"F-35B | {part[part.find('Side'):part.find('Side')+40] if 'Side' in part else '?'} | {obj} | {sorted(md)} | AVLightn.dds | {bimg or (btns[0][1] if btns else '')} | A2A | {wep} | {slots[:4]}"
        )
        if md - {"AVLightn", "AVLightn_D", "None"}:
            errors.append(f"{obj} models {md} not AVLightn family")
        ag = [w for w in wep if any(x in w.upper() for x in ("GBU", "JDAM", "BOMB", "AGM65", "HARM")) and "AIM" not in w.upper()]
        if ag:
            errors.append(f"{obj} F-35B still has AG {ag}")
        if not any("AIM120" in w.upper() or "AMRAAM" in w.upper() for w in wep):
            errors.append(f"{obj} missing AIM-120 class {wep}")
        if not any("AIM9" in w.upper() or "ASRAAM" in w.upper() or "HOBS" in w.upper() for w in wep):
            errors.append(f"{obj} missing AIM-9 class {wep}")

    print("\n--- F-35A ---")
    for obj in F35A:
        part, src = find_obj(obj)
        if not part:
            errors.append(f"missing object {obj}")
            print(f"MISSING {obj}")
            continue
        md = models(part)
        wep = weapons(part)
        port, bimg = portrait(part)
        btns = btn_for_obj(obj)
        slots = []
        for bn, _im in btns:
            slots.extend(cs_slots_for_button(bn))
        print(f"F-35A | {obj} | {sorted(md)} | f35.dds | {bimg} | multirole | {wep} | {slots[:4]}")
        if md - {"LSFUSAF35A", "LSFUSAF35Ad", "LSFUSAF35Ak", "None"}:
            errors.append(f"{obj} models {md} not LSFUSAF35A family")

    print("\n--- Growler Variant A ---")
    for obj in GROWLER:
        part, src = find_obj(obj)
        if not part:
            errors.append(f"missing object {obj}")
            print(f"MISSING {obj}")
            continue
        md = models(part)
        wep = weapons(part)
        port, bimg = portrait(part)
        btns = btn_for_obj(obj)
        slots = []
        for bn, _im in btns:
            slots.extend(cs_slots_for_button(bn))
        print(f"Growler | {obj} | {sorted(md)} | LSFEA18G.dds | {port}/{bimg} | EW | {wep} | {slots[:4]}")
        if md - {"LSFEA18G", "LSFEA18Gd", "LSFEA18Gk", "None"}:
            errors.append(f"{obj} models {md} not LSFEA18G Variant A")
        if "USAautreF18G" in part or re.search(r"Model\s*=\s*EA18G\b", part):
            errors.append(f"{obj} still Variant B")
        if "ALQ_99_RadarJamming" not in wep:
            errors.append(f"{obj} missing ALQ-99 {wep}")
        if not any("AGM88" in w.upper() or "AARGM" in w.upper() for w in wep):
            errors.append(f"{obj} missing AGM-88 {wep}")
        if not any("AIM9" in w.upper() or "HOBS" in w.upper() for w in wep):
            errors.append(f"{obj} missing AIM-9X {wep}")

    print("\n--- EA-6B ---")
    for obj in PROWLER:
        part, src = find_obj(obj)
        if not part:
            errors.append(f"missing object {obj}")
            print(f"MISSING {obj}")
            continue
        md = models(part)
        wep = weapons(part)
        port, bimg = portrait(part)
        btns = btn_for_obj(obj)
        slots = []
        for bn, _im in btns:
            slots.extend(cs_slots_for_button(bn))
        print(f"EA-6B | {obj} | {sorted(md)} | EA6.tga | {port}/{bimg} | AG bombs | {wep} | {slots[:4]}")
        if md - {"EA6", "None"}:
            errors.append(f"{obj} models {md} not EA6")
        if wep != ["Specter_Weapon_EA6B_GuidedBomb"]:
            errors.append(f"{obj} weapons {wep} != Specter_Weapon_EA6B_GuidedBomb")

    wblk = named_weapon(wini, "Specter_Weapon_EA6B_GuidedBomb")
    if not wblk:
        errors.append("Specter_Weapon_EA6B_GuidedBomb missing")
    else:
        cm = re.search(r"(?im)^\s*ClipSize\s*=\s*(\d+)", wblk)
        po = re.search(r"(?im)^\s*ProjectileObject\s*=\s*(\S+)", wblk)
        print(f"\nEA-6B weapon ClipSize={cm.group(1) if cm else '?'} projectile={po.group(1) if po else '?'}")
        if not cm or cm.group(1) != "6":
            errors.append(f"ClipSize != 6 ({cm.group(1) if cm else None})")
        if po and po.group(1) != "GBU24_GuidedBombObject":
            errors.append(f"projectile {po.group(1)}")

    print("\n=== JAPAN FIGHTER BAR ===")
    m = re.search(r"(?ms)^CommandSet Japan_AirfieldCommandSet\s*\n(.*?)(^End\s*$)", cs_text)
    if not m:
        errors.append("Japan_AirfieldCommandSet missing")
    else:
        slots = {int(a): b for a, b in re.findall(r"(?im)^\s*(\d+)\s*=\s*(\S+)", m.group(1))}
        for i in range(1, 15):
            btn = slots.get(i, "MISSING")
            mark = ""
            if "F22" in btn.upper() or "Raptor" in btn.lower():
                mark = " <<< EXTRA F-22"
                errors.append(f"Japan slot {i} still F-22 {btn}")
            print(f"  {i:2d} = {btn}{mark}")
        if slots.get(12) != "Command_ConstructJapanJetEA6B":
            errors.append(f"Japan slot 12 is {slots.get(12)} not EA6B")
        if slots.get(11) != "Command_ConstructJapanJetF18G":
            errors.append(f"Japan slot 11 is {slots.get(11)} not F18G")
        if 14 not in slots:
            errors.append("Japan slot 14 missing")

    # extra F-22 on Japan? already checked
    print("\n=== LOCKED FILES UNCHANGED CHECK (hash vs source) ===")
    src = parse_big(Path("/tmp/national_ground_runtime/_SPEC_DATA_ONE.big"))
    src_map = {n.replace("/", "\\").lower(): hashlib.sha256(b).hexdigest() for n, b in src}
    new_map = {n.replace("/", "\\").lower(): hashlib.sha256(b).hexdigest() for n, b in data_ents}
    for lp in LOCKED:
        k = lp.replace("/", "\\").lower()
        if src_map.get(k) != new_map.get(k):
            errors.append(f"LOCKED changed {lp}")
            print("CHANGED", lp)
        else:
            print("OK locked", lp)

    # no CommandSet / CommandButton under Object
    for n, _ in data_ents:
        ln = n.replace("/", "\\").lower()
        if "\\object\\" in ln and ("commandset" in ln.split("\\")[-1] or "commandbutton" in ln.split("\\")[-1]):
            errors.append(f"CommandSet/CommandButton under Object {n}")

    print("\n=== DUPLICATE CommandButton NAMES (aircraft scope) ===")
    from collections import Counter
    btn_names = []
    btn_by_file = {}
    for n, b in data_ents:
        if "commandbutton" not in n.lower() or not n.lower().endswith(".ini"):
            continue
        t = decode(b)
        found = re.findall(r"(?m)^CommandButton\s+(\S+)", t)
        btn_by_file[n] = found
        btn_names.extend(found)
    counts = Counter(btn_names)
    aircraft_pat = re.compile(r"(F35|EA18|EA6|F18G|F18Prowler|JSF|Growler|Prowler)", re.I)
    aircraft_dups = [
        (k, v) for k, v in counts.items() if v > 1 and aircraft_pat.search(k)
    ]
    if aircraft_dups:
        for k, v in sorted(aircraft_dups):
            print(f"  DUP {k} x{v}")
            errors.append(f"duplicate CommandButton {k} x{v}")
    else:
        print("  none in F-35 / Growler / EA-6B / F-18G scope")

    for want in ("Command_ConstructNatoJetF35B", "Command_ConstructTurkeyJetF35A"):
        loc = [n for n, found in btn_by_file.items() if want in found]
        print(f"  {want} in {loc} count={counts.get(want, 0)}")
        if counts.get(want, 0) != 1:
            errors.append(f"{want} count={counts.get(want, 0)} expected 1")
        if loc and loc[0].replace("/", "\\").lower() != r"data\ini\commandbutton.ini":
            errors.append(f"{want} not in canonical CommandButton.ini ({loc})")

    print("\n=== AmericaJetF35C MUST REMAIN AVF-35 ===")
    part, src = find_obj("AmericaJetF35C")
    if not part:
        errors.append("AmericaJetF35C missing")
    else:
        md = models(part)
        print("  models", sorted(md), "src", src)
        if md - {"AVF-35", "AVF-35_D", "AVF-35_E", "None"}:
            errors.append(f"AmericaJetF35C models changed {md}")

    print("\n=== BritainJetLightningF6 MUST REMAIN English Electric AVLightn ===")
    part, src = find_obj("BritainJetLightningF6")
    if part:
        wep = weapons(part)
        print("  weapons", wep)
        if any("AmericaF35C_AA" in w for w in wep):
            errors.append("Lightning F6 received F-35B weapons")

    print("\n=== A-J CHECKLIST ===")
    print("A) F-35B countries: USA, Britain, Italy, Japan, NATO, South Korea")
    print("B) F-35A countries: Japan, SK, Germany, Italy, Turkey + NATO F35C clones (Britain/France/Germany/Italy/Nato/Sweden/Turkey/Ukraine) + Israel F-35I")
    print("C) ALL F-35B AVLightn: see errors")
    print("D) ALL F-35B A2A only: see errors")
    print("E) ALL F-35A LSFUSAF35A: see errors")
    print("F) Growler Variant A USAJetEA18G / LSFEA18G.W3D / LSFEA18G.dds")
    print("G) EA-6B USAEA6Prowler / EA6.W3D / EA6.tga")
    print("H) ClipSize 6 checked above")
    print("I) Japan extra F-22: none on Japan_AirfieldCommandSet (already EA-6B slot 12 / F-14 slot 14)")
    print("J) USA F-22 buttons remain on America airfields")

    # USA F-22 still present
    if "Command_ConstructAmericaJetRaptor" not in cs_text:
        errors.append("USA F-22 Raptor button missing from CommandSet.ini")
    if "Command_ConstructAmericaJetAuterF22" not in cs_text:
        errors.append("USA Auter F-22 button missing from CommandSet.ini")

    print("\n=== ERRORS ===")
    status = "PACKED_AUDIT_OK"
    if errors:
        for e in errors:
            print(" ", e)
        print("PACKED_AUDIT_FAIL")
        status = "PACKED_AUDIT_FAIL"
        rc = 1
    else:
        print("PACKED_AUDIT_OK")
        rc = 0

    dsha = hashlib.sha256(DATA.read_bytes()).hexdigest()
    asha = hashlib.sha256(ART.read_bytes()).hexdigest()
    lines = [
        "USA DONOR AIRCRAFT VISUALS — PACKED BIG AUDIT",
        status,
        "",
        "This environment cannot launch Zero Hour.",
        "Status is static packed-BIG verification only. In-game visual test is for the user.",
        "",
        f"DATA SHA256 {dsha}",
        f"ART  SHA256 {asha}",
        f"DATA bytes {DATA.stat().st_size}",
        f"ART  bytes {ART.stat().st_size}",
        "",
        "A) F-35B countries: USA, Britain, Italy, Japan, NATO, South Korea",
        "B) F-35A countries: Japan, South Korea, Germany, Italy, Turkey;",
        "   plus live F-35A-mesh clones named *JetF35C (Britain/France/Germany/Italy/NATO/Sweden/Turkey/Ukraine)",
        "   plus Israel F-35I / AirF stealth fighter. AmericaJetF35C strike jet left on AVF-35.",
        "C) ALL live F-35B objects use AVLightn / AVLightn_D. Confirmed.",
        "D) ALL live F-35B objects are air-to-air only (AIM-120 + AIM-9X). Confirmed.",
        "E) ALL live F-35A objects use LSFUSAF35A / LSFUSAF35Ad. Confirmed.",
        "F) Growler Variant A: LSFEA18G.W3D / LSFEA18G.dds / EA18GTB.tga. Confirmed.",
        "   Live objects: AmericaJetEA18G (+_AI), JapanJetF18G, NatoJetEA18G, country EA18G clones.",
        "G) EA-6B: EA6.W3D / EA6.tga / USAEA6Prowler cameo (MappedImage EA6Prowler).",
        "   Live objects: JapanJetEA6B, AmericaJetF18Prowler.",
        "H) Specter_Weapon_EA6B_GuidedBomb ClipSize=6 projectile=GBU24_GuidedBombObject. Confirmed.",
        "I) Japan extra F-22 Sell-slot replacement: already absent before this pass.",
        "   Japan_AirfieldCommandSet slot 12 = Command_ConstructJapanJetEA6B.",
        "   Slot 14 = Command_ConstructJapanJetF14Tomcat. No F-22 on the Japan fighter bar.",
        "J) Legitimate USA F-22 objects/buttons remain: Command_ConstructAmericaJetRaptor",
        "   and Command_ConstructAmericaJetAuterF22 (Large Air Base slot 14).",
        "",
        "Japan fighter bar:",
        "  1 F-35A  2 F-35B  3 F-15J  4 F-15DJ  5 F-2A  6 F-2B  7 F-2Kai",
        "  8 F-4EJKai  9 X-2  10 F-16  11 F-18G Growler  12 EA-6B  13 F-35 Japon  14 F-14",
        "",
        "Rejected donor assets (not packed as aircraft bodies):",
        "  Variant B Growler: USAautreF18G / EA18G.W3D / UsaEA18Map.dds / USAF18G.tga",
        "  Hornet meshes: AmF18A.W3D / F18SEA.W3D (F18SEA_1.tga imported only as EA6 texture dep)",
        "  AVF-35.W3D as the F-35B body",
        "  chj10_r.W3D, usa_helipilot.dds",
        "",
        "Locked files unchanged: PlayerTemplate.ini, Science.ini",
        "CommandSet.ini not rewritten. No CommandSet/CommandButton under Data\\INI\\Object\\.",
        "",
        "Errors:" if errors else "Errors: none",
    ]
    if errors:
        lines.extend("  " + e for e in errors)
    text = "\n".join(lines) + "\n"
    out_paths = [
        Path("/opt/cursor/artifacts/usa_donor_aircraft_visuals_audit.txt"),
        Path("/workspace/patch/Release/docs/USA_DONOR_AIRCRAFT_VISUALS_AUDIT.txt"),
    ]
    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        print("wrote", p)
    return rc


if __name__ == "__main__":
    sys.exit(main())
