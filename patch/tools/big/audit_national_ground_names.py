#!/usr/bin/env python3
"""Verify CommandButton -> Object -> CSF names for all 17 nations."""

from __future__ import annotations

import hashlib
import io
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_national_ground_forces import last_named, last_named_any, last_object_any, parse_big, walk_csf
from national_ground_names import NAMES
from national_ground_roster import COUNTRIES, LOCKED_BIG_PATHS, all_units

SRC_DATA = Path("/tmp/national_ground_visual/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_visual/_SPEC_ART_ONE.big")
DATA = Path("/tmp/national_ground_names/_SPEC_DATA_ONE.big")
ART = Path("/tmp/national_ground_names/_SPEC_ART_ONE.big")
REPORT = Path("/opt/cursor/artifacts/national_ground_names_audit.txt")

VISUAL_ART_SHA = "0778d63b6d08ac92d025a4fcbd70003fbdeed968de18941eeb2b3059d9a8b353"
ROLES = (
    "MBT",
    "Heavy Tank",
    "Recon",
    "IFV",
    "APC",
    "SHORAD",
    "Mobile SAM",
    "Radar",
    "MLRS",
    "Ballistic/Cruise TEL",
    "SPA",
    "AT Vehicle",
    "Engineer",
    "Special",
)


def fail(msg: str) -> int:
    print("FAIL", msg)
    return 1


def field(blk: str, name: str):
    m = re.search(rf"(?m)^\s*{name}\s+=\s+(\S+)", blk)
    return m.group(1) if m else None


def all_fields(blk: str, name: str):
    return re.findall(rf"(?m)^\s*{name}\s+=\s+(\S+)", blk)


def _run() -> int:
    errors = 0
    if not DATA.is_file() or not ART.is_file():
        return fail("missing packed name-pass BIG")
    data = parse_big(DATA)
    art = parse_big(ART)
    src_data = parse_big(SRC_DATA)
    src_art = parse_big(SRC_ART)
    dmap = {n.replace("/", "\\").lower(): b for _i, n, b in data}
    smap = {n.replace("/", "\\").lower(): b for _i, n, b in src_data}

    data_sha = hashlib.sha256(DATA.read_bytes()).hexdigest()
    art_sha = hashlib.sha256(ART.read_bytes()).hexdigest()
    src_art_sha = hashlib.sha256(SRC_ART.read_bytes()).hexdigest()
    print("SPECTER NATIONAL GROUND NAMES — FINAL NAMING AUDIT")
    print("=" * 72)
    print("DATA only. Models, weapons, armor, locomotor, cost, time,")
    print("CommandSets, and ART are unchanged from the visual pack.")
    print()
    print("DATA_SHA256", data_sha)
    print("ART_SHA256", art_sha)
    print("SRC_ART_SHA256", src_art_sha)
    if art_sha != src_art_sha:
        errors += fail("ART SHA changed")
    else:
        print("OK ART byte-identical to visual pack")
    if art_sha != VISUAL_ART_SHA:
        errors += fail(f"ART SHA is not visual-upgrade {VISUAL_ART_SHA}")
    else:
        print("OK ART SHA is visual-upgrade ART")
    if [n for _i, n, _b in data] != [n for _i, n, _b in src_data]:
        errors += fail("DATA entry names/order changed")
    else:
        print("OK DATA entry names/order")
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

    csf_blob = None
    for _i, n, b in data:
        if n.lower().endswith("generals.csf"):
            csf_blob = b
    if not csf_blob:
        return fail("missing generals.csf")
    csf = walk_csf(csf_blob)

    print()
    print("=== CommandButton -> Object -> CSF ===")
    unit_count = 0
    for country in COUNTRIES:
        hit = last_named_any(data, "CommandSet", country.cs)
        if not hit:
            errors += fail(f"missing CS {country.cs}")
            continue
        _csfile, csblk = hit
        slots = {int(a): b for a, b in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", csblk)}
        if len(slots) != 14 or set(slots) != set(range(1, 15)):
            errors += fail(f"{country.key} slots {sorted(slots)}")
            continue
        names = []
        print()
        print(f"{country.key}  WF={country.wf}  CS={country.cs}")
        for idx, unit in enumerate(country.units, 1):
            unit_count += 1
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
            _fn, oblk = ohit
            src_hit = last_object_any(src_data, unit.obj)
            if not src_hit:
                errors += fail(f"missing source object {unit.obj}")
                continue
            _sfn, soblk = src_hit
            for key in ("Model", "BuildCost", "BuildTime"):
                if all_fields(oblk, key) != all_fields(soblk, key):
                    errors += fail(f"{unit.obj} {key} changed")
            if re.findall(r"(?m)^\s*Weapon\s+=\s+.+$", oblk) != re.findall(r"(?m)^\s*Weapon\s+=\s+.+$", soblk):
                errors += fail(f"{unit.obj} Weapon changed")
            if re.findall(r"(?m)^\s*Locomotor\s+=\s+.+$", oblk) != re.findall(r"(?m)^\s*Locomotor\s+=\s+.+$", soblk):
                errors += fail(f"{unit.obj} Locomotor changed")
            if re.findall(r"(?m)^\s*Armor\s+=\s+(\S+)", oblk) != re.findall(r"(?m)^\s*Armor\s+=\s+(\S+)", soblk):
                errors += fail(f"{unit.obj} Armor changed")

            dn = field(oblk, "DisplayName")
            if dn != f"OBJECT:{unit.obj}":
                errors += fail(f"{unit.obj} DisplayName {dn}")
            want_display, want_tip = NAMES[unit.obj]
            got_obj = csf.get(f"OBJECT:{unit.obj}")
            got_btn = csf.get(f"CONTROLBAR:Construct{unit.obj}")
            got_tip = csf.get(f"CONTROLBAR:ToolTip{unit.obj}")
            if got_obj != want_display:
                errors += fail(f"CSF OBJECT:{unit.obj} {got_obj!r} != {want_display!r}")
            if got_btn != want_display:
                errors += fail(f"CSF Construct{unit.obj} {got_btn!r} != {want_display!r}")
            if got_tip != want_tip:
                errors += fail(f"CSF ToolTip{unit.obj} {got_tip!r} != {want_tip!r}")
            names.append(want_display)
            role = ROLES[idx - 1]
            print(
                f"  {idx:2d} {role:<22} {unit.obj:<32} "
                f"{want_display:<22} btn={btn} csf=OK"
            )
        low = [n.lower() for n in names]
        if len(set(low)) != 14:
            errors += fail(f"{country.key} names not unique: {names}")
        else:
            print(f"  OK 14 unique names")

    print()
    print("UNIT_COUNT", unit_count)
    if unit_count != 17 * 14:
        errors += fail(f"expected 238 units, got {unit_count}")
    if errors:
        print("AUDIT_FAIL", errors)
        return 1
    print("AUDIT_OK  17 countries x 14 unique names = 238")
    print("CommandButton -> Object -> CSF verified for all 17 nations.")
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
