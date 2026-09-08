#!/usr/bin/env python3
"""Packed-BIG audit for National Ground CommandBar integration.

Validates CommandButton -> Object -> Weapon -> Armor -> Locomotor -> ART -> CSF
for every 17x14 national War Factory slot. ART and object combat data stay
identical to the identity pack.
"""

from __future__ import annotations

import hashlib
import io
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_national_ground_forces import last_named, last_named_any, last_object_any, parse_big, walk_csf
from national_ground_names import NAMES
from national_ground_roster import (
    ALIAS_COMMANDSETS,
    COUNTRIES,
    LOCKED_BIG_PATHS,
    PROTECTED_COMMANDSETS,
    ROLES,
    all_units,
)

SRC_DATA = Path("/tmp/national_ground_identity/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_identity/_SPEC_ART_ONE.big")
DATA = Path("/tmp/national_ground_commandbar/_SPEC_DATA_ONE.big")
ART = Path("/tmp/national_ground_commandbar/_SPEC_ART_ONE.big")
REPORT = Path("/opt/cursor/artifacts/national_ground_commandbar_audit.txt")
IDENTITY_ART_SHA = "e72e6334ab7b9691e3327a0d0a76d4fe771b4cb607e656fa97106e4d69b90c12"
NATO_HINT = re.compile(r"(Nato|NATO|Leopard2A7Plus|CortaleMK3|Command_Sell)", re.I)


def fail(msg: str) -> int:
    print("FAIL", msg)
    return 1


def field(blk: str, name: str):
    m = re.search(rf"(?m)^\s*{name}\s+=\s+(\S+)", blk)
    return m.group(1) if m else None


def basename(name: str) -> str:
    return name.replace("\\", "/").split("/")[-1].lower()


def slots_of(blk: str) -> dict[int, str]:
    return {int(a): b for a, b in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", blk)}


def object_combat_fingerprint(blk: str) -> tuple:
    display = field(blk, "DisplayName")
    body = re.sub(r"(?m)^\s*DisplayName\s+=\s+\S+\s*$", "", blk)
    return (display, body)


def collect_defs(entries):
    weapons = set()
    armor = set()
    loco = set()
    for _i, n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        weapons.update(re.findall(r"(?m)^Weapon\s+(\S+)", t))
        armor.update(re.findall(r"(?m)^Armor\s+(\S+)", t))
        loco.update(re.findall(r"(?m)^Locomotor\s+(\S+)", t))
    return weapons, armor, loco


def object_weapons(blk: str) -> list[str]:
    weap = re.findall(r"(?m)^\s*Weapon\s+=\s+(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", blk)
    if weap:
        return weap
    return [w for w in re.findall(r"(?m)^\s*Weapon\s+=\s+(\S+)", blk) if w not in {"PRIMARY", "SECONDARY", "TERTIARY"}]


def object_armors(blk: str) -> list[str]:
    return re.findall(r"(?m)^\s*Armor\s+=\s+(\S+)", blk)


def object_locos(blk: str) -> list[str]:
    return re.findall(r"(?m)^\s*Locomotor\s+=\s+SET_\S+\s+(\S+)", blk)


def country_by_key():
    return {c.key: c for c in COUNTRIES}


def target_commandsets():
    out = []
    for country in COUNTRIES:
        out.append((country.cs, country, "live"))
        for extra in (country.cs + "1", country.cs + "2", country.cs + "3"):
            out.append((extra, country, "extra"))
    by_key = country_by_key()
    for alias, key in ALIAS_COMMANDSETS.items():
        out.append((alias, by_key[key], "alias"))
    return out


def _run() -> int:
    errors = 0
    if not DATA.is_file() or not ART.is_file():
        return fail("missing packed CommandBar BIG")
    data = parse_big(DATA)
    art = parse_big(ART)
    src_data = parse_big(SRC_DATA)
    src_art = parse_big(SRC_ART)
    dmap = {n.replace("/", "\\").lower(): b for _i, n, b in data}
    smap = {n.replace("/", "\\").lower(): b for _i, n, b in src_data}
    art_bases = {basename(n): n for _i, n, b in art}

    data_sha = hashlib.sha256(DATA.read_bytes()).hexdigest()
    art_sha = hashlib.sha256(ART.read_bytes()).hexdigest()
    src_art_sha = hashlib.sha256(SRC_ART.read_bytes()).hexdigest()

    print("SPECTER NATIONAL GROUND COMMANDBAR — PACKED AUDIT")
    print("=" * 72)
    print("CommandSet / CommandButton / DisplayName / CSF only.")
    print("Object weapons, armor, locomotor, models, and ART are unchanged.")
    print()
    print("DATA_SHA256", data_sha)
    print("ART_SHA256", art_sha)
    print("SRC_ART_SHA256", src_art_sha)
    print("DATA_FILES", len(data), "ART_FILES", len(art))

    if art_sha != src_art_sha:
        errors += fail("ART SHA changed")
    else:
        print("OK ART byte-identical to identity pack")
    if art_sha != IDENTITY_ART_SHA:
        errors += fail(f"ART SHA is not identity {IDENTITY_ART_SHA}")
    else:
        print("OK ART SHA is identity ART")
    if [n for _i, n, _b in data][: len(src_data)] != [n for _i, n, _b in src_data]:
        errors += fail("DATA entry-order prefix changed")
    else:
        print("OK DATA entry-order prefix")
    if [n for _i, n, _b in art] != [n for _i, n, _b in src_art]:
        errors += fail("ART entry names/order changed")
    else:
        print("OK ART entry names/order")

    for locked in LOCKED_BIG_PATHS:
        key = locked.replace("/", "\\").lower()
        if key in smap and dmap.get(key) != smap[key]:
            errors += fail(f"locked changed {locked}")
        elif key in smap:
            print("OK locked", locked)

    for pcs in PROTECTED_COMMANDSETS:
        src_hit = last_named_any(src_data, "CommandSet", pcs)
        dst_hit = last_named_any(data, "CommandSet", pcs)
        if src_hit and dst_hit and src_hit[1] != dst_hit[1]:
            errors += fail(f"protected CommandSet changed {pcs}")
        elif src_hit and dst_hit:
            print("OK protected CS", pcs)

    csf_blob = None
    for _i, n, b in data:
        if n.lower().endswith("generals.csf"):
            csf_blob = b
    if not csf_blob:
        return fail("missing generals.csf")
    csf = walk_csf(csf_blob)
    weapons, armor, loco = collect_defs(data)

    print()
    print("=== CommandButton -> Object -> Weapon -> Armor -> Locomotor -> ART -> CSF ===")
    unit_count = 0
    nation_buttons = {}
    used_buttons = []
    for country in COUNTRIES:
        hit = last_named_any(data, "CommandSet", country.cs)
        if not hit:
            errors += fail(f"missing CS {country.cs}")
            continue
        _csfile, csblk = hit
        slots = slots_of(csblk)
        if len(slots) != 14 or set(slots) != set(range(1, 15)):
            errors += fail(f"{country.key} slots {sorted(slots)}")
            continue
        if any(NATO_HINT.search(btn or "") for btn in slots.values()):
            errors += fail(f"{country.key} NATO/Sell placeholder on live bar {slots}")
        nation_buttons[country.key] = [slots[i] for i in range(1, 15)]
        used_buttons.extend(nation_buttons[country.key])
        names = []
        print()
        print(f"{country.key}  WF={country.wf}  CS={country.cs}  last={_csfile}")
        for idx, unit in enumerate(country.units, 1):
            unit_count += 1
            role = ROLES[idx - 1]
            btn = f"Command_Construct{unit.obj}"
            if slots.get(idx) != btn:
                errors += fail(f"{country.key} slot {idx} {slots.get(idx)} != {btn}")
            bhit = last_named_any(data, "CommandButton", btn)
            if not bhit:
                errors += fail(f"missing button {btn}")
                continue
            _bf, bblk = bhit
            obj = field(bblk, "Object")
            text_key = field(bblk, "TextLabel")
            tip_key = field(bblk, "DescriptLabel")
            if obj != unit.obj:
                errors += fail(f"{btn} Object {obj}")
            if text_key != f"CONTROLBAR:Construct{unit.obj}":
                errors += fail(f"{btn} TextLabel {text_key}")
            if tip_key != f"CONTROLBAR:ToolTip{unit.obj}":
                errors += fail(f"{btn} DescriptLabel {tip_key}")

            ohit = last_object_any(data, unit.obj)
            if not ohit:
                errors += fail(f"missing object {unit.obj}")
                continue
            _of, oblk = ohit
            if field(oblk, "DisplayName") != f"OBJECT:{unit.obj}":
                errors += fail(f"{unit.obj} DisplayName {field(oblk, 'DisplayName')}")
            src_obj = last_object_any(src_data, unit.obj)
            if src_obj:
                _sf, sblk = src_obj
                _dd, dbody = object_combat_fingerprint(oblk)
                _sd, sbody = object_combat_fingerprint(sblk)
                if dbody != sbody:
                    errors += fail(f"{unit.obj} object combat/model data changed")

            model = field(oblk, "Model")
            if not model:
                errors += fail(f"{unit.obj} no Model")
                continue
            if model.lower() + ".w3d" not in art_bases:
                errors += fail(f"{unit.obj} Model {model} missing from ART")

            weap = object_weapons(oblk)
            if not weap:
                errors += fail(f"{unit.obj} no Weapon")
            for w in weap:
                if w not in weapons:
                    errors += fail(f"{unit.obj} Weapon {w} missing")
            arms = object_armors(oblk)
            if not arms:
                errors += fail(f"{unit.obj} no Armor")
            for a in arms:
                if a not in armor:
                    errors += fail(f"{unit.obj} Armor {a} missing")
            locos = object_locos(oblk)
            if not locos:
                errors += fail(f"{unit.obj} no Locomotor")
            for loc in locos:
                if loc not in loco:
                    errors += fail(f"{unit.obj} Locomotor {loc} missing")

            display = csf.get(f"OBJECT:{unit.obj}")
            btn_name = csf.get(f"CONTROLBAR:Construct{unit.obj}")
            tip = csf.get(f"CONTROLBAR:ToolTip{unit.obj}")
            expect_name, expect_tip = NAMES[unit.obj]
            if display != expect_name:
                errors += fail(f"CSF OBJECT:{unit.obj} {display!r}")
            if btn_name != expect_name:
                errors += fail(f"CSF CONTROLBAR:Construct{unit.obj} {btn_name!r}")
            if tip != expect_tip:
                errors += fail(f"CSF CONTROLBAR:ToolTip{unit.obj} {tip!r}")
            names.append(display)
            print(
                f"  {idx:2d} {role:22s} {btn} -> {unit.obj}  "
                f"name={display!r}  model={model}  weap={len(weap)} armor={len(arms)} loco={len(locos)}"
            )

        dup = [n for n, k in Counter(names).items() if k > 1]
        if dup:
            errors += fail(f"{country.key} duplicate names {dup}")
        else:
            print(f"  OK unique names {len(set(names))}/14")

    print()
    print("UNIT_COUNT", unit_count)
    if unit_count != 17 * 14:
        errors += fail(f"expected 238 units, got {unit_count}")

    shared = defaultdict(list)
    for nation, btns in nation_buttons.items():
        for btn in btns:
            shared[btn].append(nation)
    shared_hits = {b: ns for b, ns in shared.items() if len(ns) > 1}
    if shared_hits:
        errors += fail(f"shared buttons {shared_hits}")
    else:
        print("OK no shared buttons across nations")

    print()
    print("=== Extra / leftover CommandSets ===")
    for csname, country, kind in target_commandsets():
        hit = last_named_any(data, "CommandSet", csname)
        if not hit:
            if kind == "extra":
                continue
            errors += fail(f"missing {kind} CS {csname}")
            continue
        slots = slots_of(hit[1])
        expect = [f"Command_Construct{u.obj}" for u in country.units]
        got = [slots.get(i) for i in range(1, 15)]
        if got != expect:
            errors += fail(f"{kind} {csname} last-wins {hit[0]} != 14-slot roster")
        elif any(NATO_HINT.search(btn or "") for btn in slots.values()):
            errors += fail(f"{kind} {csname} still has NATO/Sell placeholder")
        else:
            print(f"OK {kind:5s} {csname} last={hit[0]}")

    print()
    print("=== Packed BIG audit ===")
    if errors:
        print("AUDIT_FAIL", errors)
        return 1
    print("AUDIT_OK")
    return 0


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


if __name__ == "__main__":
    sys.exit(main())
