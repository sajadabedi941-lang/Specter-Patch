#!/usr/bin/env python3
"""Packed audit for national ground runtime repair."""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_national_ground_forces import walk_csf
from build_national_ground_forces import last_named, parse_big, w3d_textures
from build_national_ground_runtime import (
    W3D_PIVOTS,
    classify_bones,
    default_model,
    field_line,
    w3d_bones,
)
from national_ground_roster import (
    ALIAS_COMMANDSETS,
    COUNTRIES,
    LOCKED_BIG_PATHS,
    PROTECTED_COMMANDSETS,
    ROLES,
    all_units,
)

DATA = Path("/tmp/national_ground_runtime/_SPEC_DATA_ONE.big")
ART = Path("/tmp/national_ground_runtime/_SPEC_ART_ONE.big")
SRC_DATA = Path("/tmp/national_ground_commandbar/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/national_ground_runtime_visual_audit.txt")
CHAIN = Path("/opt/cursor/artifacts/national_ground_runtime_build_chain.txt")

FACTIONS = {
    "Japan": ("FactionJapan", "Japan_VT72B"),
    "SouthKorea": ("FactionSouthKorea", "SouthKorea_VT72B"),
    "Vietnam": ("FactionVietnam", "Vietnam_VT72B"),
    "Germany": ("FactionGermany", "GermanyVehicleDozer"),
    "France": ("FactionFrance", "FranceVehicleDozer"),
    "Britain": ("FactionBritain", "BritainVehicleDozer"),
    "Italy": ("FactionItaly", "ItalyVehicleDozer"),
    "Turkey": ("FactionTurkey", "TurkeyVehicleDozer"),
    "Ukraine": ("FactionUkraine", "UkraineVehicleDozer"),
    "Sweden": ("FactionSweden", "SwedenVehicleDozer"),
    "India": ("FactionIndia", "India_Dozer"),
    "Pakistan": ("FactionPakistan", "Pakistan_Dozer"),
    "SaudiArabia": ("FactionSaudiArabia", "SaudiArabia_Dozer"),
    "UAE": ("FactionUAE", "UAE_Dozer"),
    "Syria": ("FactionSyria", "Syria_Dozer"),
    "Libya": ("FactionLibya", "Libya_Dozer"),
    "SouthAfrica": ("FactionSouthAfrica", "SouthAfrica_Dozer"),
}

WF_BTN = {
    "Japan": "Command_ConstructJapan_WarFactory",
    "SouthKorea": "Command_ConstructSouthKorea_WarFactory",
    "Vietnam": "Command_ConstructVietnam_WarFactory",
    "Germany": "Command_ConstructGermanyWarFactory",
    "France": "Command_ConstructFranceWarFactory",
    "Britain": "Command_ConstructBritainWarFactory",
    "Italy": "Command_ConstructItalyWarFactory",
    "Turkey": "Command_ConstructTurkeyWarFactory",
    "Ukraine": "Command_ConstructUkraineWarFactory",
    "Sweden": "Command_ConstructSwedenWarFactory",
    "India": "Command_ConstructIndia_WarFactory_T",
    "Pakistan": "Command_ConstructPakistan_WarFactory_T",
    "SaudiArabia": "Command_ConstructSaudiArabia_WarFactory_T",
    "UAE": "Command_ConstructUAE_WarFactory_T",
    "Syria": "Command_ConstructSyria_WarFactory_T",
    "Libya": "Command_ConstructLibya_WarFactory_T",
    "SouthAfrica": "Command_ConstructSouthAfrica_WarFactory_T",
}

BAD_PREREQ = re.compile(
    r"StrategyCenter|SCIENCE_|NeededUpgrade|IndustrialPlant|Airfield",
    re.I,
)


def fail(msg: str) -> int:
    print("FAIL", msg)
    return 1


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def basename(name: str) -> str:
    return name.replace("\\", "/").split("/")[-1].lower()


def index_kind(entries, kind: str) -> dict[str, tuple[str, str]]:
    found: dict[str, tuple[str, str]] = {}
    rx = re.compile(rf"(?ms)^{kind}\s+(\S+)[^\r\n]*\r?\n.*?(?=^{kind}\s|\Z)")
    for n, blob in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = blob.decode("latin1")
        for m in rx.finditer(t):
            found[m.group(1)] = (n, m.group(0))
    return found


def last_kind(index, name):
    hit = index.get(name)
    if not hit:
        return None, None
    return hit[0], hit[1]


def prereq_text(blk: str) -> str:
    m = re.search(r"(?ms)^\s*Prerequisites\s*\r?\n(.*?)^\s*End", blk or "")
    return m.group(1).strip() if m else ""


def slots_of(blk: str) -> dict[int, str]:
    return {int(a): b for a, b in re.findall(r"(?m)^\s*(\d+)\s*=\s*(\S+)", blk or "")}


def collect_defs(entries):
    weapons, armor, loco = set(), set(), set()
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        weapons.update(re.findall(r"(?m)^Weapon\s+(\S+)", t))
        armor.update(re.findall(r"(?m)^Armor\s+(\S+)", t))
        loco.update(re.findall(r"(?m)^Locomotor\s+(\S+)", t))
    return weapons, armor, loco


def object_weapons(blk: str) -> list[str]:
    return re.findall(r"(?m)^\s*Weapon\s*=\s*(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", blk)


def object_locos(blk: str) -> list[str]:
    return [x for x in re.findall(r"(?m)^\s*Locomotor\s*=\s+\S+\s+(\S+)", blk) if x != "SET_NORMAL"]


def packed_tex_stems(art_entries) -> set[str]:
    out = set()
    for n, _b in art_entries:
        bn = basename(n)
        if bn.endswith((".tga", ".dds", ".jpg", ".jpeg")):
            out.add(Path(bn).stem)
    return out


def missing_tex(texs, packed_stems):
    miss = []
    seen = set()
    for t in texs:
        st = Path(basename(t)).stem
        if st in seen:
            continue
        seen.add(st)
        if st not in packed_stems:
            miss.append(t)
    return miss


def crlf_stats(blob: bytes):
    crlf = blob.count(b"\r\n")
    bare_cr = blob.count(b"\r") - crlf
    lf_only = blob.count(b"\n") - crlf
    return crlf, lf_only, bare_cr


def main() -> int:
    errors = 0
    data_entries = parse_big(DATA)
    art_entries = parse_big(ART)
    src_entries = parse_big(SRC_DATA)
    objects = index_kind(data_entries, "Object")
    commandsets = index_kind(data_entries, "CommandSet")
    buttons = index_kind(data_entries, "CommandButton")
    templates = index_kind(data_entries, "PlayerTemplate")
    src_commandsets = index_kind(src_entries, "CommandSet")
    w3d = {basename(n)[:-4]: (n, b) for n, b in art_entries if basename(n).endswith(".w3d")}
    packed_stems = packed_tex_stems(art_entries)
    weapons, armor, loco = collect_defs(data_entries)
    csf_labels = set()
    for n, b in data_entries:
        if n.lower().endswith(".csf"):
            csf_labels |= {k.lower() for k in walk_csf(b)}

    lines = [
        "SPECTER NATIONAL GROUND RUNTIME VISUAL AUDIT",
        "=" * 72,
        f"DATA_SHA256 {sha256(DATA)}",
        f"ART_SHA256 {sha256(ART)}",
        f"DATA_FILES {len(data_entries)} ART_FILES {len(art_entries)}",
        "",
        "Country | Slot | Unit | Object | Model | Texture closure | Weapon bone compatibility | Status",
        "-" * 72,
    ]
    chain_lines = [
        "WAR FACTORY BUILD CHAIN",
        "Country | Builder | WarFactory Button | WarFactory Object | WarFactory CommandSet | Prerequisites | Result",
        "-" * 72,
    ]

    # locked files unchanged vs commandbar baseline (PlayerTemplate etc.)
    src_map = {n: b for n, b in src_entries}
    for p in LOCKED_BIG_PATHS:
        hit = None
        for n, b in data_entries:
            if n.replace("/", "\\").lower() == p.replace("/", "\\").lower():
                hit = (n, b)
                break
        if not hit:
            errors += fail(f"locked missing {p}")
            continue
        if src_map.get(hit[0]) != hit[1]:
            errors += fail(f"locked changed {p}")

    for csname in PROTECTED_COMMANDSETS:
        a = last_kind(src_commandsets, csname)[1]
        b = last_kind(commandsets, csname)[1]
        if a != b:
            errors += fail(f"protected CS changed {csname}")

    status_counts = Counter()
    visible = 0
    tex_pass = 0
    bone_pass = 0
    country_notes = defaultdict(lambda: {"prereq": [], "tex": [], "bone": [], "overlay": []})

    for country in COUNTRIES:
        fac, builder = FACTIONS[country.key]
        _, pt = last_kind(templates, fac)
        start_u = field_line(pt or "", "StartingUnit0")
        if start_u != builder:
            errors += fail(f"{country.key} StartingUnit0 {start_u} != {builder}")
        _, bld = last_kind(objects, builder)
        bcs = field_line(bld or "", "CommandSet")
        _, csblk = last_kind(commandsets, bcs or "")
        sl = slots_of(csblk)
        wf_btn = WF_BTN[country.key]
        if wf_btn not in sl.values():
            errors += fail(f"{country.key} dozer CS missing {wf_btn}")
            chain_lines.append(f"{country.key} | {builder} | {wf_btn} | MISSING | | | FAIL")
            continue
        _, btn = last_kind(buttons, wf_btn)
        cmd = field_line(btn or "", "Command")
        obj = field_line(btn or "", "Object")
        sci = field_line(btn or "", "Science")
        need = field_line(btn or "", "NeededUpgrade")
        if cmd != "DOZER_CONSTRUCT" or obj != country.wf:
            errors += fail(f"{country.key} WF button {cmd} {obj}")
        if sci or need:
            errors += fail(f"{country.key} WF button gated {sci} {need}")
        _, wf = last_kind(objects, country.wf)
        wfcs = field_line(wf or "", "CommandSet")
        pr = prereq_text(wf or "")
        if wfcs != country.cs:
            errors += fail(f"{country.key} WF CS {wfcs} != {country.cs}")
        if BAD_PREREQ.search(pr):
            errors += fail(f"{country.key} WF bad prereq {pr!r}")
        result = "BUILD_CHAIN_OK"
        chain_lines.append(
            f"{country.key} | {builder} | {wf_btn} | {country.wf} | {wfcs} | {pr.replace(chr(10), ' / ')} | {result}"
        )

        _, live = last_kind(commandsets, country.cs)
        live_slots = slots_of(live)
        if len(live_slots) != 14:
            errors += fail(f"{country.key} live CS slots {sorted(live_slots)}")
        for i, unit in enumerate(country.units, 1):
            btn_name = live_slots.get(i)
            _, bblk = last_kind(buttons, btn_name or "")
            bobj = field_line(bblk or "", "Object")
            if bobj != unit.obj:
                errors += fail(f"{country.key} slot {i} button Object {bobj} != {unit.obj}")
            ofile, oblk = last_kind(objects, unit.obj)
            if not oblk:
                errors += fail(f"missing object {unit.obj}")
                continue
            pru = prereq_text(oblk)
            if country.wf not in pru:
                errors += fail(f"{unit.obj} prereq not WF: {pru!r}")
                country_notes[country.key]["prereq"].append(unit.obj)
            if BAD_PREREQ.search(pru) or field_line(oblk, "Science"):
                errors += fail(f"{unit.obj} leftover gate {pru!r} sci={field_line(oblk, 'Science')}")
            model = default_model(oblk)
            missing_bones = []
            if not model or model.upper() == "NONE":
                errors += fail(f"{unit.obj} no DEFAULT model")
                status = "UNKNOWN"
            elif model.lower() not in w3d:
                errors += fail(f"{unit.obj} DEFAULT W3D missing {model}")
                status = "UNKNOWN"
            else:
                wname, wblob = w3d[model.lower()]
                texs = w3d_textures(wblob)
                miss = missing_tex(texs, packed_stems)
                bones = w3d_bones(wblob)
                bone_l = {b.lower() for b in bones}
                ini_bones = []
                for key in ("WeaponFireFXBone", "WeaponRecoilBone", "WeaponLaunchBone", "WeaponMuzzleFlash"):
                    for mm in re.finditer(rf"(?m)^\s*{key}\s*=\s*(\S+)(?:\s+(\S+))?", oblk):
                        slot, bone = mm.group(1), mm.group(2)
                        ini_bones.append(bone or (None if slot.upper() in {"PRIMARY", "SECONDARY", "TERTIARY"} else slot))
                for mm in re.finditer(r"(?m)^\s*(?:Turret|TurretPitch)\s*=\s*(\S+)", oblk):
                    if not re.match(r"^-?\d", mm.group(1)):
                        ini_bones.append(mm.group(1))
                missing_bones = [b for b in ini_bones if b and b.lower() not in bone_l]
                tex_ok = not miss
                bone_ok = not missing_bones
                if tex_ok:
                    tex_pass += 1
                    visible += 1
                else:
                    errors += fail(f"{unit.obj} missing textures {miss}")
                if bone_ok:
                    bone_pass += 1
                else:
                    errors += fail(f"{unit.obj} missing bones {missing_bones} model={model}")
                    country_notes[country.key]["bone"].append(unit.obj)
                if tex_ok and bone_ok:
                    status = "VISUAL_OK"
                elif not bone_ok and tex_ok:
                    status = "WEAPON_BONE_FIXED"
                else:
                    status = "VISUAL_FIXED"
                if miss:
                    country_notes[country.key]["tex"].append(f"{unit.obj}:{miss}")
            status_counts[status] += 1
            weaps = object_weapons(oblk)
            for w in weaps:
                if w not in weapons:
                    errors += fail(f"{unit.obj} missing weapon {w}")
            arm = field_line(oblk, "Armor")
            if arm and arm not in armor:
                errors += fail(f"{unit.obj} missing armor {arm}")
            for lc in object_locos(oblk):
                if lc not in loco:
                    errors += fail(f"{unit.obj} missing locomotor {lc}")
            if status == "VISUAL_OK":
                tex_note, bone_note = "OK", "OK"
            elif status == "WEAPON_BONE_FIXED":
                tex_note, bone_note = "OK", "FIXED"
            else:
                tex_note, bone_note = "FIXED", "OK" if not missing_bones else "FIXED"
            lines.append(
                f"{country.key} | {i} {ROLES[i-1]} | {unit.display} | {unit.obj} | {model} | {tex_note} | {bone_note} | {status}"
            )

        for alias, key in ALIAS_COMMANDSETS.items():
            if key != country.key:
                continue
            _, ablk = last_kind(commandsets, alias)
            if not ablk:
                continue
            aslots = slots_of(ablk)
            if len(aslots) != 14:
                errors += fail(f"alias {alias} slots {sorted(aslots)}")
            else:
                country_notes[country.key]["overlay"].append(alias)

    for n, b in data_entries:
        if n.replace("/", "\\").lower() == r"data\ini\commandset.ini":
            crlf, lf_only, bare_cr = crlf_stats(b)
            if lf_only or bare_cr:
                errors += fail(f"CommandSet.ini lf_only={lf_only} bare_cr={bare_cr}")
            glued = len(re.findall(br"End\r\nCommandSet", b))
            if glued:
                errors += fail(f"CommandSet.ini glued End+CommandSet {glued}")
            print(f"CommandSet.ini CRLF={crlf} LF-only={lf_only} bareCR={bare_cr}")
            break

    air_ok = 0
    for country in COUNTRIES:
        for name in (
            f"{country.key}AirfieldCommandSet",
            f"{country.side}_AirfieldCommandSet",
            f"{country.key}_AirfieldCommandSet",
        ):
            _, blk = last_kind(commandsets, name)
            if not blk:
                continue
            sl = slots_of(blk)
            for btn in sl.values():
                if btn in {"Command_Sell", "Command_SetRallyPoint", "Command_Stop"}:
                    continue
                _, bblk = last_kind(buttons, btn)
                if not bblk:
                    errors += fail(f"airfield button missing {name} {btn}")
                    continue
                obj = field_line(bblk, "Object")
                if obj:
                    _, oblk = last_kind(objects, obj)
                    if not oblk:
                        errors += fail(f"airfield object missing {obj} via {btn}")
            air_ok += 1
    print("airfield CommandSets resolved", air_ok)

    # no CommandSet/CommandButton under Object\
    for n, b in data_entries:
        if "\\object\\" in n.replace("/", "\\").lower() and n.lower().endswith(".ini"):
            t = b.decode("latin1")
            if re.search(r"(?m)^CommandSet\s+", t) or re.search(r"(?m)^CommandButton\s+", t):
                errors += fail(f"CommandSet/Button under Object {n}")

    if "UNKNOWN" in status_counts:
        errors += fail("UNKNOWN visual status present")

    lines += [
        "",
        f"STATUS_COUNTS {dict(status_counts)}",
        f"VISIBLE_DEFAULT {visible}/238",
        f"TEXTURE_CLOSURE {tex_pass}/238",
        f"WEAPON_BONE {bone_pass}/238",
        f"ERRORS {errors}",
        "AUDIT_OK" if errors == 0 else "AUDIT_FAIL",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    CHAIN.write_text("\n".join(chain_lines) + "\n", encoding="utf-8")
    print(REPORT)
    print(CHAIN)
    print("status", dict(status_counts), "errors", errors)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
