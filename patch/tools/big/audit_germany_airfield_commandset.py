#!/usr/bin/env python3
"""Packed-BIG audit for the GermanyAirfieldCommandSet parse crash."""

from __future__ import annotations

import hashlib
import io
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_national_ground_forces import last_named, last_named_any, parse_big
from national_ground_roster import LOCKED_BIG_PATHS

DATA = Path("/tmp/national_ground_commandbar/_SPEC_DATA_ONE.big")
ART = Path("/tmp/national_ground_commandbar/_SPEC_ART_ONE.big")
SRC_ART = Path("/tmp/national_ground_identity/_SPEC_ART_ONE.big")
SRC_DATA = Path("/tmp/national_ground_identity/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/germany_airfield_commandset_audit.txt")
IDENTITY_ART_SHA = "e72e6334ab7b9691e3327a0d0a76d4fe771b4cb607e656fa97106e4d69b90c12"

AIRFIELD_CS = "GermanyAirfieldCommandSet"
GERMANY_AIR_CS = (
    "GermanyAirfieldCommandSet",
    "Germany_LargeAirBaseCommandSet",
    "Germany_HeavyAirBaseCommandSet",
    "Germany_HelicopterBaseCommandSet",
)


def fail(msg: str) -> int:
    print("FAIL", msg)
    return 1


def field(blk: str, name: str):
    m = re.search(rf"(?m)^\s*{name}\s+=\s+(\S+)", blk)
    return m.group(1) if m else None


def slots_of(blk: str):
    return [(int(a), b) for a, b in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", blk)]


def _run() -> int:
    errors = 0
    if not DATA.is_file():
        return fail("missing packed DATA")
    data = parse_big(DATA)
    art = parse_big(ART) if ART.is_file() else []
    src_data = parse_big(SRC_DATA) if SRC_DATA.is_file() else []

    print("SPECTER GERMANY AIRFIELD COMMANDSET — CRASH-FIX AUDIT")
    print("=" * 72)
    print("INI syntax and CommandButton references only.")
    print("Weapons, objects, ART, CSF, costs, and balance are unchanged.")
    print()
    print("DATA_SHA256", hashlib.sha256(DATA.read_bytes()).hexdigest())
    if ART.is_file():
        print("ART_SHA256", hashlib.sha256(ART.read_bytes()).hexdigest())
    print("DATA_FILES", len(data))

    if ART.is_file() and SRC_ART.is_file():
        if hashlib.sha256(ART.read_bytes()).hexdigest() != hashlib.sha256(SRC_ART.read_bytes()).hexdigest():
            errors += fail("ART SHA changed")
        else:
            print("OK ART unchanged")
        if hashlib.sha256(ART.read_bytes()).hexdigest() != IDENTITY_ART_SHA:
            errors += fail("ART SHA is not identity ART")

    buttons = {}
    objects = {}
    csini = None
    csini_name = None
    for _i, n, b in data:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        if n.replace("/", "\\").lower() == r"data\ini\commandset.ini":
            csini, csini_name = t, n
        for m in re.finditer(r"(?m)^CommandButton\s+(\S+)\s*$", t):
            buttons[m.group(1)] = n
        for m in re.finditer(r"(?m)^Object\s+(\S+)\s*$", t):
            objects[m.group(1)] = n
        nl = n.replace("/", "\\").lower()
        if nl.endswith(".ini") and "\\object\\" in nl:
            if re.search(r"(?m)^CommandSet\s+", t) or (
                "nationalgroundcommandbar.ini" in nl and re.search(r"(?m)^CommandButton\s+", t)
            ):
                errors += fail(f"CommandSet/CommandButton under Object\\ {n}")

    if not csini:
        return fail("missing CommandSet.ini")

    print()
    print("=== CommandSet.ini structure ===")
    names = re.findall(r"(?m)^CommandSet\s+(\S+)", csini)
    dups = [k for k, v in Counter(names).items() if v > 1]
    if dups:
        errors += fail(f"duplicate CommandSet names {dups}")
    else:
        print("OK no duplicate CommandSet names", len(names))

    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^CommandSet\s+(\S+)", csini)]
    air_off = next((off for off, name in starts if name == AIRFIELD_CS), None)
    if air_off is None:
        return fail(f"missing {AIRFIELD_CS} in CommandSet.ini")
    print(f"OK found {AIRFIELD_CS} in {csini_name} at {air_off}")

    missing_end = []
    for i, (off, name) in enumerate(starts):
        if off > air_off:
            break
        end = starts[i + 1][0] if i + 1 < len(starts) else len(csini)
        blk = csini[off:end]
        if not re.search(r"(?m)^(End|END)\s*$", blk):
            missing_end.append(name)
    if missing_end:
        errors += fail(f"missing End/END before/at Airfield: {missing_end}")
    else:
        print("OK every CommandSet before/including GermanyAirfield has End or END")

    hit = last_named_any(data, "CommandSet", AIRFIELD_CS)
    if hit[0].replace("/", "\\").lower() != r"data\ini\commandset.ini":
        errors += fail(f"{AIRFIELD_CS} last-wins {hit[0]}")
    if not re.search(r"(?m)^End\s*$", hit[1]):
        errors += fail(f"{AIRFIELD_CS} missing End")
    else:
        print("OK GermanyAirfieldCommandSet has End")

    print()
    print("=== Object references to GermanyAirfieldCommandSet ===")
    obj_refs = []
    for _i, n, b in data:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        for m in re.finditer(r"(?m)^Object\s+(\S+)", t):
            pass
        if re.search(r"(?m)^\s*CommandSet\s+=\s+GermanyAirfieldCommandSet\s*$", t):
            objs = re.findall(r"(?m)^Object\s+(\S+)", t)
            obj_refs.append((n, objs[-1] if objs else "?"))
    if not obj_refs:
        errors += fail("no Object CommandSet= GermanyAirfieldCommandSet")
    for n, obj in obj_refs:
        print(f"OK {obj} in {n} -> {AIRFIELD_CS}")

    print()
    print("=== Germany air CommandSet button refs ===")
    for csname in GERMANY_AIR_CS:
        cs = last_named_any(data, "CommandSet", csname)
        if not cs:
            errors += fail(f"missing {csname}")
            continue
        print(csname, "last", cs[0])
        for slot, btn in slots_of(cs[1]):
            if btn not in buttons:
                errors += fail(f"{csname} slot {slot} missing button {btn}")
                continue
            bhit = last_named_any(data, "CommandButton", btn)
            obj = field(bhit[1], "Object") if bhit else None
            if field(bhit[1], "Command") == "UNIT_BUILD":
                if not obj or obj not in objects:
                    errors += fail(f"{btn} Object {obj} missing")
                else:
                    print(f"  {slot:2d} {btn} -> {obj} OK")
            else:
                print(f"  {slot:2d} {btn} command={field(bhit[1], 'Command')}")

    if src_data:
        for obj in (
            "GermanyJetTyphoonT4",
            "GermanyJetTyphoonECR",
            "GermanyJetTornadoADV",
            "GermanyJetF35A",
            "GermanyJetMiG29G",
            "GermanyJetTornadoIDS",
            "GermanyJetF4F",
            "GermanyJetAlphaJet",
            "GermanyJetMako",
        ):
            src = last_named_any(src_data, "Object", obj)
            dst = last_named_any(data, "Object", obj)
            if src and dst and src[1] != dst[1]:
                errors += fail(f"object data changed {obj}")
        print("OK Germany airfield jet objects unchanged")

    for locked in LOCKED_BIG_PATHS:
        key = locked.replace("/", "\\").lower()
        smap = {n.replace("/", "\\").lower(): b for _i, n, b in src_data} if src_data else {}
        dmap = {n.replace("/", "\\").lower(): b for _i, n, b in data}
        if key in smap and dmap.get(key) != smap[key]:
            errors += fail(f"locked changed {locked}")

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
