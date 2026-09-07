#!/usr/bin/env python3
"""Prove Japan / South Korea / Vietnam no longer load Iraq air assets."""

from __future__ import annotations

import io
import re
import struct
import sys
from pathlib import Path

DATA = Path("/tmp/jp_sk_vn_faction_chain/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/jp_sk_vn_faction_chain_audit.txt")


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
        out.append((btn, obj))
    return out


def main() -> int:
    if not DATA.is_file():
        print("missing packed DATA", DATA, file=sys.stderr)
        return 1
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        code = _run()
    finally:
        sys.stdout = old_stdout
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
    sci = idx[r"data\ini\science.ini"][2].decode("latin1")
    errors = []

    factions = {
        "Japan": {
            "pt": "FactionJapan",
            "side": "Japan",
            "science": "SCIENCE_Japan",
            "cc": "Japan_CommandCenter",
            "dozer": "Japan_VT72B",
            "dozer_cs": "Japan_VT72BCommandSet",
            "air": "Japan_LargeAirBase",
            "air_cs": "Japan_AirfieldCommandSet",
            "heavy": "Japan_HeavyAirBase",
            "heavy_cs": "Japan_HeavyAirBaseCommandSet",
            "forbidden_btn": r"Iraq",
        },
        "SouthKorea": {
            "pt": "FactionSouthKorea",
            "side": "SouthKorea",
            "science": "SCIENCE_SouthKorea",
            "cc": "SouthKorea_CommandCenter",
            "dozer": "SouthKorea_VT72B",
            "dozer_cs": "SouthKorea_VT72BCommandSet",
            "air": "SouthKorea_LargeAirBase",
            "air_cs": "SouthKorea_AirfieldCommandSet",
            "heavy": "SouthKorea_HeavyAirBase",
            "heavy_cs": "SouthKorea_HeavyAirBaseCommandSet",
            "forbidden_btn": r"Iraq",
        },
        "Vietnam": {
            "pt": "FactionVietnam",
            "side": "Vietnam",
            "science": "SCIENCE_Vietnam",
            "cc": "Vietnam_CommandCenter",
            "dozer": "Vietnam_VT72B",
            "dozer_cs": "Vietnam_VT72BCommandSet",
            "air": "Vietnam_LargeAirBase",
            "air_cs": "Vietnam_AirfieldCommandSet",
            "heavy": "Vietnam_HeavyAirBase",
            "heavy_cs": "Vietnam_HeavyAirBaseCommandSet",
            "forbidden_btn": r"Iraq",
        },
    }

    print("PACKED", DATA, "files", len(entries))
    print()

    for label, spec in factions.items():
        print("=" * 72)
        print(label)
        print("=" * 72)
        pblock = named(pt, "PlayerTemplate", spec["pt"])
        if not pblock:
            errors.append(f"{label} PlayerTemplate missing")
            continue
        print(pblock)
        if re.search(r"(?m)^\s*BaseSide\s*=\s*Iraq\s*$", pblock):
            errors.append(f"{label} BaseSide still Iraq")
        if "SCIENCE_Iraq" in pblock:
            errors.append(f"{label} still SCIENCE_Iraq")
        if f"BaseSide          = {spec['side']}" not in pblock and f"BaseSide = {spec['side']}" not in pblock:
            if not re.search(rf"(?m)^\s*BaseSide\s*=\s*{spec['side']}\s*$", pblock):
                errors.append(f"{label} BaseSide not {spec['side']}")
        if spec["science"] not in pblock:
            errors.append(f"{label} missing {spec['science']}")
        if spec["cc"] not in pblock:
            errors.append(f"{label} StartingBuilding not {spec['cc']}")
        if spec["dozer"] not in pblock:
            errors.append(f"{label} StartingUnit0 not {spec['dozer']}")

        if not named(sci, "Science", spec["science"]):
            errors.append(f"{spec['science']} not defined")

        cc_hits = last_object(entries, spec["cc"])
        if not cc_hits:
            errors.append(f"{spec['cc']} missing")
            continue
        i, n, block = cc_hits[-1]
        cmd = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", block)
        print(f"LIVE CommandCenter {spec['cc']}")
        print(f"  last file [{i}] {n}")
        print(f"  CommandSet {cmd.group(1) if cmd else None}")
        print(f"  copies {len(cc_hits)}")
        if cmd and "Iraq" in cmd.group(1):
            errors.append(f"{spec['cc']} CommandSet still Iraq")

        dz_hits = last_object(entries, spec["dozer"])
        i, n, block = dz_hits[-1]
        cmd = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", block)
        live_cs = cmd.group(1) if cmd else None
        print(f"LIVE dozer {spec['dozer']}")
        print(f"  last file [{i}] {n}")
        print(f"  CommandSet {live_cs}")
        print(f"  copies {len(dz_hits)}")
        if live_cs != spec["dozer_cs"]:
            errors.append(f"{spec['dozer']} live CS {live_cs} != {spec['dozer_cs']}")
        if live_cs == "Iraq_VT72BCommandSet":
            errors.append(f"{spec['dozer']} still Iraq_VT72BCommandSet")
        if "VT72B.ini" in n.replace("/", "\\") and n.replace("/", "\\").split("\\")[-1] == "VT72B.ini":
            errors.append(f"{spec['dozer']} last file is still VT72B.ini override")

        dozer_bar = named(cs, "CommandSet", spec["dozer_cs"])
        print("DOZER BAR")
        print(dozer_bar)
        links = buttons_to_objects(cb, dozer_bar)
        spawned_air = None
        spawned_heavy = None
        for btn, obj in links:
            print(f"  {btn} -> {obj}")
            if obj == spec["air"]:
                spawned_air = obj
            if obj == spec["heavy"]:
                spawned_heavy = obj
            if obj and obj.startswith("Iraq_"):
                errors.append(f"{label} dozer still builds {obj}")
        if spawned_air != spec["air"]:
            errors.append(f"{label} dozer does not spawn {spec['air']}")
        if spawned_heavy != spec["heavy"]:
            errors.append(f"{label} dozer does not spawn {spec['heavy']}")

        air_hits = last_object(entries, spec["air"])
        i, n, block = air_hits[-1]
        cmd = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", block)
        print(f"LIVE airbase {spec['air']}")
        print(f"  last file [{i}] {n}")
        print(f"  CommandSet {cmd.group(1) if cmd else None}")
        if cmd and cmd.group(1) != spec["air_cs"]:
            errors.append(f"{spec['air']} CS {cmd.group(1)} != {spec['air_cs']}")

        heavy_hits = last_object(entries, spec["heavy"])
        i, n, block = heavy_hits[-1]
        cmd = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", block)
        print(f"LIVE heavy {spec['heavy']}")
        print(f"  last file [{i}] {n}")
        print(f"  CommandSet {cmd.group(1) if cmd else None}")
        if cmd and cmd.group(1) != spec["heavy_cs"]:
            errors.append(f"{spec['heavy']} CS {cmd.group(1)} != {spec['heavy_cs']}")

        print("ACTIVE AIRCRAFT LIST")
        air_bar = named(cs, "CommandSet", spec["air_cs"])
        heavy_bar = named(cs, "CommandSet", spec["heavy_cs"])
        print(air_bar)
        print(heavy_bar)
        for bar_name, body in (("air", air_bar), ("heavy", heavy_bar)):
            for btn, obj in buttons_to_objects(cb, body):
                print(f"  {bar_name} {btn} -> {obj}")
                if obj and obj.startswith("Iraq_"):
                    errors.append(f"{label} {bar_name} list still {obj}")
                if btn.startswith("Command_ConstructIraq") or (obj and "Iraq" in obj):
                    errors.append(f"{label} {bar_name} Iraq button {btn} -> {obj}")
        print()

    print("=" * 72)
    if errors:
        print("AUDIT_FAIL")
        for e in errors:
            print("ERROR", e)
        return 1
    print("AUDIT_OK three countries no longer load Iraq air assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
