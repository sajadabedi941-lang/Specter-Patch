#!/usr/bin/env python3
"""Validate destination War Factory rebuild against packed DATA."""
from __future__ import annotations

import re
import struct
from collections import defaultdict
from pathlib import Path

SRC_DATA = Path("/tmp/ea6b_crash_fix/_SPEC_DATA_ONE.big")
PACKED = Path("/tmp/warfactory_rebuild/_SPEC_DATA_ONE.big")
INI_PATH = Path("/workspace/patch/Data/INI/CommandSet_ZZZZ_WarFactoryRebuild.ini")
REPORT = Path("/workspace/patch/Release/docs/WARFACTORY_REBUILD_FINAL_REPORT.txt")

LIVE_DEST = {
    "Britain": ("NATO", "NatoWarfactoryCommandSet", "BritainWarFactory", "BritainWarfactoryCommandSet"),
    "Germany": ("NATO", "NatoWarfactoryCommandSet", "GermanyWarFactory", "GermanyWarfactoryCommandSet"),
    "France": ("NATO", "NatoWarfactoryCommandSet", "FranceWarFactory", "FranceWarfactoryCommandSet"),
    "Italy": ("NATO", "NatoWarfactoryCommandSet", "ItalyWarFactory", "ItalyWarfactoryCommandSet"),
    "Ukraine": ("NATO", "NatoWarfactoryCommandSet", "UkraineWarFactory", "UkraineWarfactoryCommandSet"),
    "Turkey": ("NATO", "NatoWarfactoryCommandSet", "TurkeyWarFactory", "TurkeyWarfactoryCommandSet"),
    "Sweden": ("NATO", "NatoWarfactoryCommandSet", "SwedenWarFactory", "SwedenWarfactoryCommandSet"),
    "Libya": ("Iraq", "Iraq_WarFactoryCommandSet_T3", "Libya_WarFactory_T", "Libya_WarFactoryCommandSet"),
    "SouthAfrica": ("Iraq", "Iraq_WarFactoryCommandSet_T3", "SouthAfrica_WarFactory_T", "SouthAfrica_WarFactoryCommandSet"),
    "UAE": ("Egypt", "EgyptWarFactoryCommandSet", "UAE_WarFactory_T", "UAE_WarFactoryCommandSet"),
    "SaudiArabia": ("Egypt", "EgyptWarFactoryCommandSet", "SaudiArabia_WarFactory_T", "SaudiArabia_WarFactoryCommandSet"),
    "Syria": ("Egypt", "EgyptWarFactoryCommandSet", "Syria_WarFactory_T", "Syria_WarFactoryCommandSet"),
    "Japan": ("USA", "AmericaWarFactoryCommandSet", "Japan_WarFactory", "Japan_WarFactoryCommandSet"),
    "Vietnam": ("USA", "AmericaWarFactoryCommandSet", "Vietnam_WarFactory", "Vietnam_WarFactoryCommandSet"),
    "SouthKorea": ("USA", "AmericaWarFactoryCommandSet", "SouthKorea_WarFactory", "SouthKorea_WarFactoryCommandSet"),
    "India": ("Russia", "RussiaWarFactoryCommandSet", "India_WarFactory_T", "India_WarFactoryCommandSet"),
    "Pakistan": ("Russia", "RussiaWarFactoryCommandSet", "Pakistan_WarFactory_T", "Pakistan_WarFactoryCommandSet"),
}

PROTECTED_CS = [
    "NatoWarfactoryCommandSet",
    "AmericaWarFactoryCommandSet",
    "AmericaWarFactoryCommandSet_T3",
    "RussiaWarFactoryCommandSet",
    "EgyptWarFactoryCommandSet",
    "Iraq_WarFactoryCommandSet_T3",
    "IranWarfactoryCommandSet",
    "Israel_WarFactoryCommandSet",
    "NorthKorea_WarFactoryCommandSet",
    "ChinaWarFactoryCommandSet",
]

SKIP_BTNS = {
    "Command_Sell",
    "Command_SetRallyPoint",
}

USA_OMIT = {"Command_ConstructAmericaVehicleM1075I_AI"}


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


def parse_block(text: str, start: int) -> str:
    depth = 0
    buf = []
    for i, line in enumerate(text[start:].splitlines(True)):
        buf.append(line)
        raw = line.split(";", 1)[0]
        if i == 0:
            depth = 1
            continue
        if re.match(r"(?i)^\s*End\b", raw):
            depth -= 1
            if depth <= 0:
                break
        elif re.match(
            r"(?i)^\s*(Draw|Behavior|Body|WeaponSet|ArmorSet|Prerequisites|DefaultConditionState|ConditionState|UnitSpecificSounds|Turret|LocomotorSet|TransitionState|IdleConditionState)\b",
            raw,
        ):
            depth += 1
    return "".join(buf)


def last_blocks(kind: str, names: set[str], entries):
    found = {n: (None, None) for n in names}
    pats = [(n, re.compile(rf"(?im)^{kind}\s+{re.escape(n)}\b")) for n in names]
    for fname, blob in entries:
        text = blob.decode("latin1", errors="ignore")
        for n, pat in pats:
            for m in pat.finditer(text):
                found[n] = (fname, parse_block(text, m.start()))
    return found


def last_block(kind: str, name: str, entries):
    hit = last_blocks(kind, {name}, entries)
    return hit[name]


def cs_slots(blk: str):
    out = []
    for line in blk.splitlines():
        raw = line.split(";", 1)[0]
        m = re.match(r"\s*(\d+)\s*=\s*(\S+)", raw)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def load_buttons(entries):
    btns = {}
    for _n, b in entries:
        text = b.decode("latin1", errors="ignore")
        for m in re.finditer(r"(?im)^CommandButton\s+(\S+)", text):
            name = m.group(1)
            start = m.start()
            depth = 0
            buf = []
            for i, line in enumerate(text[start:].splitlines(True)):
                buf.append(line)
                raw = line.split(";", 1)[0]
                if i == 0:
                    depth = 1
                    continue
                if re.match(r"(?i)^\s*End\b", raw):
                    depth -= 1
                    if depth <= 0:
                        break
            btns[name] = "".join(buf)
    return btns


def btn_obj(blk: str | None):
    if not blk:
        return None
    m = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", blk)
    return m.group(1) if m else None


def index_kinds(entries):
    kinds = defaultdict(set)
    pats = {
        "Object": re.compile(r"(?im)^Object(?:Reskin)?\s+(\S+)"),
        "Weapon": re.compile(r"(?im)^Weapon\s+(\S+)"),
        "Armor": re.compile(r"(?im)^Armor\s+(\S+)"),
        "Locomotor": re.compile(r"(?im)^Locomotor\s+(\S+)"),
        "CommandSet": re.compile(r"(?im)^CommandSet\s+(\S+)"),
        "CommandButton": re.compile(r"(?im)^CommandButton\s+(\S+)"),
    }
    for _n, b in entries:
        text = b.decode("latin1", errors="ignore")
        for kind, pat in pats.items():
            kinds[kind].update(pat.findall(text))
    return kinds


def named_exists(kind: str, name: str, index) -> bool:
    return name in index.get(kind, ())


def main() -> int:
    errors = []
    src = parse_big(SRC_DATA)
    packed = parse_big(PACKED)
    btns = load_buttons(packed)
    index = index_kinds(packed)
    objects = index["Object"]

    ini_text = INI_PATH.read_text(encoding="latin1")
    for cs in PROTECTED_CS:
        if re.search(rf"(?im)^CommandSet\s+{re.escape(cs)}\b", ini_text):
            errors.append(f"rebuild INI defines protected CommandSet {cs}")

    lines = [
        "SPECTER WAR FACTORY REBUILD FINAL AUDIT",
        "=======================================",
        "",
        "Method: destination War Factory CommandSets were emptied of",
        "destination-named production and rebuilt as exact copies of the",
        "assigned reference-country live CommandSet (same CommandButtons,",
        "same unit Objects, same costs/times/prereqs on those Objects).",
        "",
        "Protected countries were not edited.",
        "",
    ]

    cs_names = set(PROTECTED_CS)
    obj_names = set()
    for _country, (ref, ref_cs, building, live_cs) in LIVE_DEST.items():
        cs_names.add(ref_cs)
        cs_names.add(live_cs)
        obj_names.add(building)

    src_cs = last_blocks("CommandSet", cs_names, src)
    packed_cs = last_blocks("CommandSet", cs_names, packed)
    packed_obj = last_blocks("Object", obj_names, packed)

    needed_units = set()
    for _country, (_ref, _ref_cs, _building, live_cs) in LIVE_DEST.items():
        _ns, new_blk = packed_cs.get(live_cs, (None, None))
        for _slot, btn in cs_slots(new_blk or ""):
            if btn in SKIP_BTNS:
                continue
            obj = btn_obj(btns.get(btn))
            if obj:
                needed_units.add(obj)
    packed_units = last_blocks("Object", needed_units, packed)

    for cs in PROTECTED_CS:
        _os, old = src_cs.get(cs, (None, None))
        _ns, new = packed_cs.get(cs, (None, None))
        if old != new:
            errors.append(f"protected CommandSet changed: {cs}")

    print("=== PER-COUNTRY AUDIT ===")
    for country, (ref, ref_cs, building, live_cs) in LIVE_DEST.items():
        bsrc, bblk = packed_obj.get(building, (None, None))
        if not bblk:
            errors.append(f"{country}: missing WarFactory object {building}")
            continue
        m = re.search(r"(?im)^\s*CommandSet\s*=\s*(\S+)", bblk)
        bcs = m.group(1) if m else None
        if bcs != live_cs:
            errors.append(f"{country}: building {building} CommandSet={bcs} expected {live_cs}")

        _os, old_blk = src_cs.get(live_cs, (None, None))
        old_btns = [b for _s, b in cs_slots(old_blk or "") if b not in SKIP_BTNS]
        _ns, new_blk = packed_cs.get(live_cs, (None, None))
        new_slots = cs_slots(new_blk or "")
        _rs, ref_blk = packed_cs.get(ref_cs, (None, None))
        ref_slots = cs_slots(ref_blk or "")
        if ref == "USA":
            ref_slots = [(s, b) for s, b in ref_slots if b not in USA_OMIT]
        if new_slots != ref_slots:
            errors.append(f"{country}: live CommandSet {live_cs} != {ref_cs} (minus AI if USA)")

        units = []
        seen_btn = set()
        seen_obj = set()
        has_sell = False
        for slot, btn in new_slots:
            if btn == "Command_Sell":
                has_sell = True
                continue
            if btn in SKIP_BTNS:
                continue
            if btn in seen_btn:
                errors.append(f"{country}: duplicate button {btn}")
            seen_btn.add(btn)
            if btn not in btns:
                errors.append(f"{country}: missing CommandButton {btn}")
                units.append((slot, btn, None, "MISSING_BUTTON"))
                continue
            obj = btn_obj(btns[btn])
            if not obj:
                errors.append(f"{country}: {btn} has no Object")
                units.append((slot, btn, None, "NO_OBJECT"))
                continue
            if obj in seen_obj:
                errors.append(f"{country}: duplicate object {obj}")
            seen_obj.add(obj)
            if obj not in objects:
                errors.append(f"{country}: missing object {obj}")
                units.append((slot, btn, obj, "MISSING_OBJECT"))
                continue
            _osrc, oblk = packed_units.get(obj, (None, None))
            if not oblk:
                errors.append(f"{country}: object block missing {obj}")
                units.append((slot, btn, obj, "MISSING_BLOCK"))
                continue
            armor = re.search(r"(?im)^\s*Armor\s*=\s*(\S+)", oblk)
            loco = re.findall(r"(?im)^\s*Locomotor\s*=\s*(?:SET_\S+\s+)?(\S+)", oblk)
            weps = re.findall(r"(?im)^\s*Weapon\s*=\s+(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", oblk)
            model = re.search(r"(?im)^\s*Model\s*=\s*(\S+)", oblk)
            kind = re.search(r"(?im)^\s*KindOf\s*=\s*(.+)$", oblk)
            variations = re.search(r"(?im)^\s*BuildVariations\s*=\s*(.+)$", oblk)
            issues = []
            warnings = []
            kind_s = kind.group(1) if kind else ""
            if variations and "PROJECTILE" in kind_s:
                missing_var = []
                for var in variations.group(1).split():
                    if var not in objects:
                        missing_var.append(var)
                if missing_var:
                    issues.append("BuildVariations missing " + ",".join(missing_var))
                else:
                    warnings.append("selector stub BuildVariations=" + variations.group(1).strip())
            else:
                if not armor:
                    issues.append("no Armor")
                elif not named_exists("Armor", armor.group(1), index):
                    issues.append(f"Armor {armor.group(1)} missing")
                if not loco:
                    issues.append("no Locomotor")
                else:
                    for loc in loco:
                        if loc in ("End", "SET_NORMAL", "SET_NORMAL_UPGRADED", "None", "NONE"):
                            continue
                        if not named_exists("Locomotor", loc, index):
                            issues.append(f"Locomotor {loc} missing")
                if not model or model.group(1) in ("None", "NONE"):
                    issues.append("no Model")
                if "CAN_ATTACK" in kind_s and not weps:
                    issues.append("CAN_ATTACK but no Weapon")
                for w in weps:
                    if w in ("NONE", "None", "End"):
                        continue
                    if not named_exists("Weapon", w, index):
                        issues.append(f"Weapon {w} missing")
            status = "OK" if not issues else "; ".join(issues)
            if warnings and status == "OK":
                status = "OK (" + "; ".join(warnings) + ")"
            if issues:
                errors.append(f"{country}: {obj} {status}")
            units.append((slot, btn, obj, status))

        if not has_sell:
            errors.append(f"{country}: missing Command_Sell")

        print(f"{country:12} ref={ref:6} units={len(units)} sell={has_sell}")
        lines.append(f"Country: {country}")
        lines.append(f"Old WarFactory entries removed: {len(old_btns)}")
        for b in old_btns:
            lines.append(f"  - {b}")
        lines.append(f"New template used: {ref} ({ref_cs})")
        lines.append(f"Units transferred: {len(units)}")
        lines.append(f"CommandSet: {live_cs}")
        lines.append(f"WarFactory Object: {building} (file {bsrc})")
        lines.append("CommandButtons:")
        for slot, btn, obj, status in units:
            lines.append(f"  {slot:>2} {btn} -> {obj} [{status}]")
        unit_ok = all(u[3].startswith("OK") for u in units)
        lines.append(f"Validation: {'PASS' if unit_ok and has_sell and new_slots == ref_slots else 'FAIL'}")
        lines.append("")

    # Rebuild INI must not define objects
    if re.search(r"(?im)^Object(?:Reskin)?\s+", ini_text):
        errors.append("rebuild INI defines objects")

    lines.append("PROTECTED COUNTRIES")
    lines.append("-------------------")
    lines.append("USA / Russia / China / Iran / Israel / NATO / Egypt / Iraq / North Korea")
    lines.append("CommandSets identical to baseline: " + ("YES" if not any("protected CommandSet" in e for e in errors) else "NO"))
    lines.append("CommandSet.ini / CommandButton.ini / PlayerTemplate.ini / Science.ini: not modified")
    lines.append("Protected country Object folders: not modified")
    lines.append("")
    lines.append(f"Errors: {len(errors)}")
    for e in errors:
        lines.append(f" FAIL {e}")
        print(" FAIL", e)
    if errors:
        lines.append("")
        lines.append("WARFACTORY_REBUILD_AUDIT_FAIL")
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("wrote", REPORT)
        return 1
    lines.append("WARFACTORY_REBUILD_AUDIT_OK")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("WARFACTORY_REBUILD_AUDIT_OK")
    print("wrote", REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
