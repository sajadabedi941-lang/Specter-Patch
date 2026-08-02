#!/usr/bin/env python3
"""Validate USA dozer build menu wiring in a packed DATA.big."""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import sys
from pathlib import Path

STOCK_CS_HASH = "6d2749ef50ed262fb2aa273d19a83b4585682cfca9f7e788ae110d4f4cd7af31"

REQUIRED_BUILDINGS = [
    "AmericaCommandCenter",
    "AmericaPowerPlant",
    "AmericaBarracks",
    "AmericaWarFactory",
    "AmericaSupplyCenter",
    "AmericaAirfield",
    "America_AdvancedAirBase",
    "AmericaPatriotBattery",
    "AmericaFireBase",
    "AmericaRadarStation",
]


def read_big(path: Path):
    data = path.read_bytes()
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = {}
    for _ in range(n):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        sz = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries[name] = data[off : off + sz]
    return entries


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-big", type=Path, required=True)
    args = ap.parse_args()
    e = read_big(args.data_big)
    errors = []

    cs_key = "Data\\INI\\CommandSet.ini"
    if cs_key not in e:
        errors.append("CommandSet.ini missing")
    else:
        h = hashlib.sha256(e[cs_key]).hexdigest()
        if h != STOCK_CS_HASH:
            errors.append(f"CommandSet.ini hash mismatch: {h}")

    dozer_cs = None
    for k, v in e.items():
        if k.endswith("Dozer.ini") and re.search(rb"^Object\s+AmericaVehicleDozer\b", v, re.M):
            m = re.search(rb"CommandSet\s*=\s*(\S+)", v)
            dozer_cs = m.group(1).decode() if m else None
            print(f"Dozer CommandSet = {dozer_cs} ({k})")
    if dozer_cs != "AmericaDozerCommandSet":
        errors.append(f"Dozer must use AmericaDozerCommandSet, got {dozer_cs}")
    if dozer_cs and dozer_cs.endswith("_PatchAAB"):
        errors.append("PatchAAB dozer CommandSet is known-empty at runtime")

    buttons = set()
    objects = set()
    for k, v in e.items():
        if not k.lower().endswith(".ini"):
            continue
        buttons.update(m.group(1).decode() for m in re.finditer(rb"^CommandButton\s+(\S+)", v, re.M))
        objects.update(m.group(1).decode() for m in re.finditer(rb"^Object\s+(\S+)", v, re.M))

    stock = e[cs_key].decode("latin-1", "replace")
    m = re.search(r"^CommandSet AmericaDozerCommandSet\s*\n(.*?)(?=^CommandSet |\Z)", stock, re.M | re.S)
    if not m:
        errors.append("AmericaDozerCommandSet missing from CommandSet.ini")
        refs = []
    else:
        refs = re.findall(r"=\s*(Command_\S+)", m.group(1))
        print(f"AmericaDozerCommandSet slots: {len(refs)}")
        for r in refs:
            print(f"  {r}")

    btn_obj = {}
    for k, v in e.items():
        if not k.lower().endswith(".ini"):
            continue
        for bm in re.finditer(rb"^CommandButton\s+(\S+)\s*\n(.*?)(?=^CommandButton\s|\Z)", v, re.M | re.S):
            name = bm.group(1).decode()
            body = bm.group(2).decode("latin-1", "replace")
            om = re.search(r"Object\s*=\s*(\S+)", body)
            if om:
                btn_obj[name] = om.group(1)

    for r in refs:
        if r not in buttons:
            errors.append(f"missing CommandButton {r}")
            continue
        o = btn_obj.get(r)
        if o and o not in objects:
            errors.append(f"button {r} Object={o} missing")

    for b in REQUIRED_BUILDINGS:
        if b not in objects:
            errors.append(f"missing building Object {b}")

    # AAB aircraft commandset
    aab_cs_file = e.get("Data\\INI\\CommandSet_USA_AdvancedAirBase.ini", b"").decode("latin-1", "replace")
    if "America_AdvancedAirBaseCommandSet" not in aab_cs_file:
        errors.append("America_AdvancedAirBaseCommandSet missing from CommandSet_USA_AdvancedAirBase.ini")
    if "AmericaDozerCommandSet_PatchAAB" in aab_cs_file:
        errors.append("stale PatchAAB dozer set still present")

    # keep aircraft
    for ac in [
        "Patch_America_B52",
        "Patch_America_B1",
        "Patch_America_E3",
        "Patch_America_C17",
        "Patch_America_KC135",
        "Patch_America_AC130Spectre",
        "America_AdvancedAirBase",
    ]:
        if ac not in objects:
            errors.append(f"missing required aircraft/AAB object {ac}")

    # AAB building must not be locked by Object Prerequisites / Science.
    aab_body = None
    for k, v in e.items():
        m = re.search(rb"^Object\s+America_AdvancedAirBase\b(.*?)(?=^Object\s|\Z)", v, re.M | re.S)
        if m:
            aab_body = m.group(1).decode("latin-1", "replace")
    if aab_body is None:
        errors.append("America_AdvancedAirBase Object missing")
    else:
        pr = re.search(r"Prerequisites\s*\n(.*?)\n\s*End", aab_body, re.S)
        if pr:
            inner = pr.group(1)
            if re.search(r"Object\s*=", inner) or re.search(r"Science\s*=", inner):
                errors.append("AAB Object must have empty Prerequisites (no Object/Science locks)")
        if re.search(r"^\s*RequiredScience\s*=", aab_body, re.M):
            errors.append("AAB Object has RequiredScience lock")

    # no English txt
    eng_txt = [k for k in e if "\\english\\" in k.lower() and k.lower().endswith(".txt")]
    if eng_txt:
        errors.append(f"English txt overlays present: {eng_txt}")

    if errors:
        print("FAIL")
        for err in errors:
            print(" -", err)
        return 1
    print("PASS: USA dozer build menu wiring OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
