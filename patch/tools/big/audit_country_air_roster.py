#!/usr/bin/env python3
"""Verify every JP/SK/VN roster aircraft has the four-way connection.

Object INI + CommandButton + CommandSet slot + BuildObject.
Faction CommandCenter / Dozer / VT72B chains must still be the live country chain.
No Iraq aircraft / Iraq CommandButtons on country air bars.
"""

from __future__ import annotations

import io
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from country_air_roster import COUNTRIES, LOCKED_COMMANDSETS, is_iraq_name

DATA = Path("/tmp/country_air_roster/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/country_air_roster_audit.txt")


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


def buttons_to_objects(cb: str, body: str):
    out = []
    for slot, btn in re.findall(r"(?m)^\s*(\d+)\s*=\s*(Command_\S+)", body):
        blk = named(cb, "CommandButton", btn)
        obj = None
        cmd = None
        img = None
        if blk:
            m = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", blk)
            obj = m.group(1) if m else None
            m = re.search(r"(?m)^\s*Command\s*=\s*(\S+)", blk)
            cmd = m.group(1) if m else None
            m = re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", blk)
            img = m.group(1) if m else None
        out.append((int(slot), btn, obj, cmd, img, bool(blk)))
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
    pending = []

    print("PACKED", DATA, "files", len(entries))
    print()
    print("FACTION CHAINS LOCKED (must stay country-owned)")
    expected_pt = {
        "FactionJapan": ("Japan_CommandCenter", "Japan_VT72B", "Japan"),
        "FactionSouthKorea": ("SouthKorea_CommandCenter", "SouthKorea_VT72B", "SouthKorea"),
        "FactionVietnam": ("Vietnam_CommandCenter", "Vietnam_VT72B", "Vietnam"),
    }
    for faction, (cc, dozer, side) in expected_pt.items():
        block = named(pt, "PlayerTemplate", faction)
        if not block:
            errors.append(f"{faction} missing")
            continue
        if f"StartingBuilding  = {cc}" not in block and cc not in block:
            errors.append(f"{faction} StartingBuilding not {cc}")
        if dozer not in block:
            errors.append(f"{faction} StartingUnit0 not {dozer}")
        if re.search(r"(?m)^\s*BaseSide\s*=\s*Iraq\s*$", block) or "SCIENCE_Iraq" in block:
            errors.append(f"{faction} still Iraq faction refs")
        print(f"  {faction} CC={cc} dozer={dozer} BaseSide={side}")

    for obj, expect_cs in (
        ("Japan_VT72B", "Japan_VT72BCommandSet"),
        ("SouthKorea_VT72B", "SouthKorea_VT72BCommandSet"),
        ("Vietnam_VT72B", "Vietnam_VT72BCommandSet"),
        ("Japan_CommandCenter", "Japan_CommandCenterCommandSet"),
        ("SouthKorea_CommandCenter", "SouthKorea_CommandCenterCommandSet"),
        ("Vietnam_CommandCenter", "Vietnam_CommandCenterCommandSet"),
    ):
        hits = last_object(entries, obj)
        cmd = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", hits[-1][2]) if hits else None
        live = cmd.group(1) if cmd else None
        print(f"  LIVE {obj} -> {live} file={hits[-1][1] if hits else None}")
        if live != expect_cs:
            errors.append(f"{obj} CS {live} != {expect_cs}")
        if live and "Iraq" in live:
            errors.append(f"{obj} still Iraq CommandSet")

    for name in LOCKED_COMMANDSETS:
        if not named(cs, "CommandSet", name):
            errors.append(f"locked CommandSet missing {name}")

    print()
    print("AIRCRAFT FOUR-WAY CONNECTION")
    for country in COUNTRIES:
        print("=" * 72)
        print(country.name)
        print("=" * 72)
        for bar_name, expect_obj, rows in (
            (country.air_cs, country.air_obj, country.fighters),
            (country.heavy_cs, country.heavy_obj, country.heavy),
        ):
            air_hits = last_object(entries, expect_obj)
            cmd = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", air_hits[-1][2]) if air_hits else None
            live_cs = cmd.group(1) if cmd else None
            print(f"BUILDING {expect_obj} CommandSet={live_cs}")
            if live_cs != bar_name:
                errors.append(f"{expect_obj} CS {live_cs} != {bar_name}")
            body = named(cs, "CommandSet", bar_name)
            if not body:
                errors.append(f"{bar_name} missing")
                continue
            print(body)
            links = buttons_to_objects(cb, body)
            by_slot = {slot: (btn, obj, cmd, img, ok) for slot, btn, obj, cmd, img, ok in links}
            for row in rows:
                print(f"SLOT {row.slot} {row.button}")
                if row.slot not in by_slot:
                    errors.append(f"{country.name} missing slot {row.slot} {row.button}")
                    print("  FAIL no CommandSet slot")
                    continue
                btn, obj, cmd, img, ok = by_slot[row.slot]
                if btn != row.button:
                    errors.append(f"{bar_name} slot {row.slot} is {btn} != {row.button}")
                if not ok:
                    errors.append(f"missing CommandButton {row.button}")
                    print("  FAIL no CommandButton")
                    continue
                hits = last_object(entries, row.obj)
                model = None
                src = None
                if hits:
                    src = hits[-1][1]
                    mm = re.search(r"(?m)^\s*Model\s*=\s*(\S+)", hits[-1][2])
                    model = mm.group(1) if mm else None
                ok_obj = bool(hits)
                ok_build = obj == row.obj and cmd == "UNIT_BUILD"
                print(f"  CommandButton {ok} Object={obj} Command={cmd} Image={img}")
                print(f"  Object INI {ok_obj} {src} Model={model}")
                print(f"  BuildObject {ok_build} donor_art={row.donor_art}")
                if not ok_obj:
                    errors.append(f"{row.obj} Object INI missing")
                if not ok_build:
                    errors.append(f"{row.button} BuildObject {obj}/{cmd} != {row.obj}/UNIT_BUILD")
                if is_iraq_name(obj) or is_iraq_name(btn) or (img and img.lower().startswith("irq_")):
                    errors.append(f"{country.name} Iraq reference {btn} -> {obj} img={img}")
                if "Iraq" in (src or ""):
                    errors.append(f"{row.obj} defined in Iraq-named file {src}")
                if row.donor_art.startswith("PENDING"):
                    pending.append(f"{country.name} {row.obj} model={model} {row.donor_art}")
            for slot, btn, obj, cmd, img, ok in links:
                if btn in ("Command_SetRallyPoint", "Command_Sell"):
                    continue
                if obj and is_iraq_name(obj):
                    errors.append(f"{bar_name} extra Iraq object {obj}")
                if is_iraq_name(btn):
                    errors.append(f"{bar_name} extra Iraq button {btn}")

    print()
    print("DONOR ART PENDING (not a failure; next pass only)")
    for line in pending:
        print(" ", line)

    print()
    print("=" * 72)
    if errors:
        print("AUDIT_FAIL")
        for e in errors:
            print("ERROR", e)
        return 1
    print("AUDIT_OK every roster aircraft has Object INI + CommandButton + CommandSet slot + BuildObject")
    print("AUDIT_OK faction CommandCenter/Dozer/VT72B chains unchanged")
    print("AUDIT_OK no Iraq aircraft on JP/SK/VN airbars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
