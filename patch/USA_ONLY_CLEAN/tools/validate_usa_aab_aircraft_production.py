#!/usr/bin/env python3
"""Validate USA AdvancedAirBase aircraft production wiring."""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import sys
from pathlib import Path

STOCK_CS_HASH = "6d2749ef50ed262fb2aa273d19a83b4585682cfca9f7e788ae110d4f4cd7af31"

REQUIRED_AIRCRAFT = [
    "Patch_America_B2",
    "Patch_America_B1",
    "Patch_America_B52",
    "Patch_America_E3",
    "Patch_America_C17",
    "Patch_America_KC135",
    "Patch_America_AC130Spectre",
    "Patch_America_F22",
    "Patch_America_F35",
    "Patch_America_AssaultHelo",
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

    h = hashlib.sha256(e["Data\\INI\\CommandSet.ini"]).hexdigest()
    if h != STOCK_CS_HASH:
        errors.append(f"CommandSet.ini hash mismatch: {h}")

    aab = None
    for k, v in e.items():
        if re.search(rb"^Object\s+America_AdvancedAirBase\b", v, re.M):
            m = re.search(rb"^Object\s+America_AdvancedAirBase\b(.*?)(?=^Object\s|\Z)", v, re.M | re.S)
            aab = m.group(1).decode("latin-1", "replace") if m else ""
            print(f"AAB object file: {k}")
            break
    if aab is None:
        errors.append("America_AdvancedAirBase missing")
        aab = ""

    cs_m = re.search(r"CommandSet\s*=\s*(\S+)", aab)
    aab_cs = cs_m.group(1) if cs_m else None
    print(f"AAB CommandSet = {aab_cs}")
    if aab_cs != "AmericaAirfieldCommandSet":
        errors.append(f"AAB must use AmericaAirfieldCommandSet, got {aab_cs}")

    if "ProductionUpdate" not in aab:
        errors.append("AAB missing ProductionUpdate")
    if "ParkingPlaceBehavior" not in aab:
        errors.append("AAB missing ParkingPlaceBehavior")
    if "FS_AIRFIELD" not in aab:
        errors.append("AAB KindOf missing FS_AIRFIELD")

    # Resolve AmericaAirfieldCommandSet from last definition across INIs
    last_block = None
    last_file = None
    for k in sorted(e.keys(), key=lambda s: s.lower()):
        if not k.lower().endswith(".ini"):
            continue
        v = e[k]
        for m in re.finditer(
            rb"^CommandSet\s+AmericaAirfieldCommandSet\s*\n(.*?)(?=^CommandSet\s|\Z)",
            v,
            re.M | re.S,
        ):
            last_block = m.group(1).decode("latin-1", "replace")
            last_file = k
    print(f"AmericaAirfieldCommandSet last defined in: {last_file}")
    if not last_block:
        errors.append("AmericaAirfieldCommandSet missing")
        refs = []
    else:
        refs = re.findall(r"=\s*(Command_\S+)", last_block)
        print(f"slots: {len(refs)}")

    buttons = {}
    objects = set()
    for k, v in e.items():
        if not k.lower().endswith(".ini"):
            continue
        for m in re.finditer(rb"^Object\s+(\S+)", v, re.M):
            objects.add(m.group(1).decode())
        for m in re.finditer(rb"^CommandButton\s+(\S+)\s*\n(.*?)(?=^CommandButton\s|\Z)", v, re.M | re.S):
            name = m.group(1).decode()
            body = m.group(2).decode("latin-1", "replace")
            om = re.search(r"Object\s*=\s*(\S+)", body)
            buttons[name] = om.group(1) if om else None

    for r in refs:
        if r not in buttons:
            errors.append(f"missing CommandButton {r}")
            continue
        o = buttons[r]
        if o and o not in objects:
            errors.append(f"button {r} Object={o} missing")
        else:
            print(f"  OK {r} -> {o}")

    for ac in REQUIRED_AIRCRAFT:
        if ac not in objects:
            errors.append(f"missing aircraft {ac}")

    # AssaultHelo must not require helipad-only production
    for k, v in e.items():
        m = re.search(rb"^Object\s+Patch_America_AssaultHelo\b(.*?)(?=^Object\s|\Z)", v, re.M | re.S)
        if m:
            kind = re.search(rb"KindOf\s*=\s*([^\n]+)", m.group(1))
            if kind and b"PRODUCED_AT_HELIPAD" in kind.group(1):
                errors.append("Patch_America_AssaultHelo KindOf still has PRODUCED_AT_HELIPAD")

    # Dozer still stock
    for k, v in e.items():
        if k.endswith("Dozer.ini") and b"Object AmericaVehicleDozer" in v:
            m = re.search(rb"CommandSet\s*=\s*(\S+)", v)
            if m and m.group(1).decode() != "AmericaDozerCommandSet":
                errors.append(f"Dozer CommandSet regress: {m.group(1).decode()}")

    if errors:
        print("FAIL")
        for err in errors:
            print(" -", err)
        return 1
    print("PASS: USA AAB aircraft production wiring OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
