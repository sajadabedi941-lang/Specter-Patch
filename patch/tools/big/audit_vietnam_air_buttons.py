#!/usr/bin/env python3
"""Prove every required Vietnam aircraft button exists and is reachable."""

from __future__ import annotations

import io
import re
import struct
import sys
from pathlib import Path

DATA = Path("/tmp/vietnam_air_buttons/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/vietnam_air_buttons_audit.txt")

REQUIRED_FIGHTERS = [
    ("Command_ConstructVietnamJetMig29S", "VietnamJetMig29S"),
    ("Command_ConstructVietnamJetMig21", "VietnamJetMig21"),
    ("Command_ConstructVietnamJetSu22", "VietnamJetSu22"),
    ("Command_ConstructVietnamJetSu27", "VietnamJetSu27"),
    ("Command_ConstructVietnamJetSu30", "VietnamJetSu30"),
    ("Command_ConstructVietnamJetYak130", "VietnamJetYak130"),
    ("Command_ConstructVietnamJetF5E", "VietnamJetF5E"),
]

REQUIRED_HEAVY = [
    ("Command_ConstructVietnamJetMi8", "VietnamJetMi8"),
    ("Command_ConstructVietnamJetMi17", "VietnamJetMi17"),
    ("Command_ConstructVietnamJetIL76", "VietnamJetIL76"),
]


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


def named(text: str, kind: str, name: str):
    m = re.search(rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$", text)
    return m.group(0) if m else None


def last_object(entries, obj: str):
    hits = []
    for i, n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        if re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", t):
            m = re.search(rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)", t)
            hits.append((i, n, m.group(0) if m else t))
    return hits


def buttons_to_objects(cb: str, commandset_body: str):
    out = []
    for btn in re.findall(r"(?m)^\s*\d+\s*=\s*(Command_\S+)", commandset_body):
        blk = named(cb, "CommandButton", btn)
        obj = None
        if blk:
            m = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", blk)
            obj = m.group(1) if m else None
        out.append((btn, obj, bool(blk)))
    return out


def main() -> int:
    if not DATA.is_file():
        print("missing packed DATA", DATA, file=sys.stderr)
        return 1
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
    entries = parse_big(DATA)
    idx = {n.replace("/", "\\").lower(): (i, n, b) for i, n, b in entries}
    pt = idx[r"data\ini\playertemplate.ini"][2].decode("latin1")
    cs = idx[r"data\ini\commandset.ini"][2].decode("latin1")
    cb = idx[r"data\ini\commandbutton.ini"][2].decode("latin1")
    errors = []

    print("PACKED", DATA, "files", len(entries))
    print()

    pblock = named(pt, "PlayerTemplate", "FactionVietnam")
    print("PLAYERTEMPLATE")
    print(pblock)
    if not pblock:
        errors.append("FactionVietnam missing")
    else:
        if "BaseSide          = Vietnam" not in pblock and not re.search(
            r"(?m)^\s*BaseSide\s*=\s*Vietnam\s*$", pblock
        ):
            errors.append("FactionVietnam BaseSide not Vietnam")
        if "SCIENCE_Iraq" in pblock:
            errors.append("FactionVietnam still SCIENCE_Iraq")
        if "Vietnam_CommandCenter" not in pblock:
            errors.append("StartingBuilding not Vietnam_CommandCenter")
        if "Vietnam_VT72B" not in pblock:
            errors.append("StartingUnit0 not Vietnam_VT72B")

    dz_hits = last_object(entries, "Vietnam_VT72B")
    i, n, block = dz_hits[-1]
    cmd = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", block)
    print("LIVE DOZER Vietnam_VT72B")
    print(f"  last file [{i}] {n}")
    print(f"  CommandSet {cmd.group(1) if cmd else None}")
    if not cmd or cmd.group(1) != "Vietnam_VT72BCommandSet":
        errors.append(f"dozer CS {cmd.group(1) if cmd else None} != Vietnam_VT72BCommandSet")

    dozer_bar = named(cs, "CommandSet", "Vietnam_VT72BCommandSet")
    print(dozer_bar)
    spawned = {obj for _b, obj, _ok in buttons_to_objects(cb, dozer_bar)}
    if "Vietnam_LargeAirBase" not in spawned:
        errors.append("dozer does not spawn Vietnam_LargeAirBase")
    if "Vietnam_HeavyAirBase" not in spawned:
        errors.append("dozer does not spawn Vietnam_HeavyAirBase")
    if any(obj and obj.startswith("Iraq_") for obj in spawned):
        errors.append("dozer still builds Iraq object")

    for obj_name, expect_cs in (
        ("Vietnam_CommandCenter", "Vietnam_CommandCenterCommandSet"),
        ("Vietnam_LargeAirBase", "Vietnam_AirfieldCommandSet"),
        ("Vietnam_HeavyAirBase", "Vietnam_HeavyAirBaseCommandSet"),
    ):
        hits = last_object(entries, obj_name)
        i, n, block = hits[-1]
        cmd = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", block)
        live = cmd.group(1) if cmd else None
        print(f"LIVE {obj_name}")
        print(f"  last file [{i}] {n}")
        print(f"  CommandSet {live}")
        if live != expect_cs:
            errors.append(f"{obj_name} CS {live} != {expect_cs}")

    print()
    print("REQUIRED FIGHTER BUTTONS")
    air_bar = named(cs, "CommandSet", "Vietnam_AirfieldCommandSet")
    print(air_bar)
    air_links = buttons_to_objects(cb, air_bar)
    air_by_btn = {btn: obj for btn, obj, ok in air_links if ok}
    for btn, obj in REQUIRED_FIGHTERS:
        blk = named(cb, "CommandButton", btn)
        if not blk:
            errors.append(f"missing CommandButton {btn}")
            print(f"  MISSING {btn}")
            continue
        got = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", blk)
        got_obj = got.group(1) if got else None
        reachable = air_by_btn.get(btn) == obj
        print(f"  {btn} -> {got_obj} reachable={reachable}")
        print(blk)
        if got_obj != obj:
            errors.append(f"{btn} Object {got_obj} != {obj}")
        if not reachable:
            errors.append(f"{btn} not on Vietnam_AirfieldCommandSet")
        if got_obj and got_obj.startswith("Iraq_"):
            errors.append(f"{btn} still Iraq {got_obj}")
        if not last_object(entries, obj):
            errors.append(f"object {obj} missing")

    print("REQUIRED HEAVY BUTTONS")
    heavy_bar = named(cs, "CommandSet", "Vietnam_HeavyAirBaseCommandSet")
    print(heavy_bar)
    heavy_links = buttons_to_objects(cb, heavy_bar)
    heavy_by_btn = {btn: obj for btn, obj, ok in heavy_links if ok}
    for btn, obj in REQUIRED_HEAVY:
        blk = named(cb, "CommandButton", btn)
        if not blk:
            errors.append(f"missing CommandButton {btn}")
            print(f"  MISSING {btn}")
            continue
        got = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", blk)
        got_obj = got.group(1) if got else None
        reachable = heavy_by_btn.get(btn) == obj
        print(f"  {btn} -> {got_obj} reachable={reachable}")
        print(blk)
        if got_obj != obj:
            errors.append(f"{btn} Object {got_obj} != {obj}")
        if not reachable:
            errors.append(f"{btn} not on Vietnam_HeavyAirBaseCommandSet")
        if got_obj and got_obj.startswith("Iraq_"):
            errors.append(f"{btn} still Iraq {got_obj}")
        if not last_object(entries, obj):
            errors.append(f"object {obj} missing")

    for bar_name, links in (("air", air_links), ("heavy", heavy_links)):
        for btn, obj, ok in links:
            if not ok and btn not in ("Command_SetRallyPoint", "Command_Sell"):
                errors.append(f"{bar_name} slot button missing: {btn}")
            if obj and obj.startswith("Iraq_"):
                errors.append(f"{bar_name} still {obj}")
            if btn.startswith("Command_ConstructIraq"):
                errors.append(f"{bar_name} Iraq button {btn}")

    required_air_objs = {obj for _b, obj in REQUIRED_FIGHTERS}
    required_heavy_objs = {obj for _b, obj in REQUIRED_HEAVY}
    got_air = {obj for _b, obj, ok in air_links if ok and obj}
    got_heavy = {obj for _b, obj, ok in heavy_links if ok and obj}
    if got_air != required_air_objs | set():
        extra = got_air - required_air_objs
        missing = required_air_objs - got_air
        if missing:
            errors.append(f"air missing objects {sorted(missing)}")
        # rally/sell have obj None; extras that are not required fighters fail
        extras = {o for o in extra if o}
        if extras:
            errors.append(f"air extra objects {sorted(extras)}")
    extras_h = {o for o in (got_heavy - required_heavy_objs) if o}
    if extras_h:
        errors.append(f"heavy extra objects {sorted(extras_h)}")
    missing_h = required_heavy_objs - got_heavy
    if missing_h:
        errors.append(f"heavy missing objects {sorted(missing_h)}")

    print("=" * 72)
    if errors:
        print("AUDIT_FAIL")
        for e in errors:
            print("ERROR", e)
        return 1
    print("AUDIT_OK every required Vietnam aircraft CommandButton exists and is reachable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
