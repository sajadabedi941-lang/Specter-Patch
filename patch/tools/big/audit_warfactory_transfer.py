#!/usr/bin/env python3
"""Audit destination War Factory transfer INI against packed DATA."""
from __future__ import annotations

import re
import struct
from collections import defaultdict
from pathlib import Path

SRC_DATA = Path("/tmp/ea6b_crash_fix/_SPEC_DATA_ONE.big")
TRANSFER = Path("/workspace/patch/Data/INI/CommandSet_ZZZZ_WarFactoryTransfer.ini")

REF_COUNTRIES = {
    "USA", "America", "Russia", "China", "Iran", "Israel", "Nato", "NATO",
    "Egypt", "Iraq", "NorthKorea",
}
DEST_LIVE = {
    "Britain": ("NATO", "BritainWarfactoryCommandSet"),
    "Germany": ("NATO", "GermanyWarfactoryCommandSet"),
    "France": ("NATO", "FranceWarfactoryCommandSet"),
    "Italy": ("NATO", "ItalyWarfactoryCommandSet"),
    "Ukraine": ("NATO", "UkraineWarfactoryCommandSet"),
    "Turkey": ("NATO", "TurkeyWarfactoryCommandSet"),
    "Sweden": ("NATO", "SwedenWarfactoryCommandSet"),
    "Libya": ("Iraq", "Libya_WarFactoryCommandSet"),
    "SouthAfrica": ("Iraq", "SouthAfrica_WarFactoryCommandSet"),
    "UAE": ("Egypt", "UAE_WarFactoryCommandSet"),
    "SaudiArabia": ("Egypt", "SaudiArabia_WarFactoryCommandSet"),
    "Syria": ("Egypt", "Syria_WarFactoryCommandSet"),
    "Japan": ("USA", "Japan_WarFactoryCommandSet"),
    "Vietnam": ("USA", "Vietnam_WarFactoryCommandSet"),
    "SouthKorea": ("USA", "SouthKorea_WarFactoryCommandSet"),
    "India": ("Russia", "India_WarFactoryCommandSet"),
    "Pakistan": ("Russia", "Pakistan_WarFactoryCommandSet"),
}

REF_LOCKED_CS = {
    "NatoWarfactoryCommandSet",
    "AmericaWarFactoryCommandSet",
    "AmericaWarFactoryCommandSet_T",
    "AmericaWarFactoryCommandSet_T1",
    "AmericaWarFactoryCommandSet_T2",
    "AmericaWarFactoryCommandSet_T3",
    "RussiaWarFactoryCommandSet",
    "EgyptWarFactoryCommandSet",
    "Egypt_WarFactoryCommandSet",
    "Iraq_WarFactoryCommandSet",
    "Iraq_WarFactoryCommandSet_T3",
    "IranWarfactoryCommandSet",
    "Israel_WarFactoryCommandSet",
    "NorthKorea_WarFactoryCommandSet",
    "ChinaWarFactoryCommandSet",
}


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


def blocks(text: str, kind: str):
    found = {}
    for m in re.finditer(rf"(?im)^{kind}\s+(\S+)", text):
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
        found[name] = "".join(buf)
    return found


def main() -> int:
    errors = []
    text = TRANSFER.read_text(encoding="latin1")
    sets = blocks(text, "CommandSet")
    print(f"Transfer CommandSets: {len(sets)}")

    locked_hit = [n for n in sets if n in REF_LOCKED_CS]
    if locked_hit:
        errors.append(f"transfer edits reference CommandSets: {locked_hit}")

    entries = parse_big(SRC_DATA)
    objects = set()
    obj_files = defaultdict(list)
    for n, b in entries:
        t = b.decode("latin1", errors="ignore")
        for m in re.finditer(r"(?im)^Object(?:Reskin)?\s+(\S+)", t):
            objects.add(m.group(1))
            obj_files[m.group(1)].append(n)

    btns = {}
    for n, b in entries:
        t = b.decode("latin1", errors="ignore")
        btns.update(blocks(t, "CommandButton"))

    print("\n=== PER-COUNTRY AUDIT ===")
    report_rows = []
    for country, (ref, live_cs) in DEST_LIVE.items():
        blk = sets.get(live_cs)
        if not blk:
            errors.append(f"{country}: missing live CommandSet {live_cs}")
            continue
        units = []
        has_sell = False
        seen_btn = set()
        seen_obj = set()
        for line in blk.splitlines():
            m = re.match(r"\s*(\d+)\s*=\s*(\S+)", line)
            if not m:
                continue
            slot, btn = m.group(1), m.group(2)
            if btn == "Command_Sell":
                has_sell = True
                continue
            if btn in seen_btn:
                errors.append(f"{country} duplicate button {btn}")
            seen_btn.add(btn)
            if btn not in btns:
                errors.append(f"{country} missing CommandButton {btn}")
                units.append((slot, btn, None, False))
                continue
            om = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", btns[btn])
            obj = om.group(1) if om else None
            if not obj:
                errors.append(f"{country} {btn} has no Object")
                continue
            if obj in seen_obj:
                errors.append(f"{country} duplicate object {obj}")
            seen_obj.add(obj)
            if obj not in objects:
                errors.append(f"{country} missing object {obj}")
            # destination identity: object name should include country token
            token = country.replace("SouthAfrica", "SouthAfrica").replace("SaudiArabia", "SaudiArabia")
            if country == "SouthKorea":
                ident_ok = obj.startswith("SouthKorea")
            elif country == "UAE":
                ident_ok = obj.startswith("UAE")
            else:
                ident_ok = obj.startswith(country)
            if not ident_ok:
                errors.append(f"{country} object {obj} is not destination-named")
            units.append((slot, btn, obj, obj in objects))
        if not has_sell:
            errors.append(f"{country} missing Command_Sell")
        ok = sum(1 for u in units if u[3])
        print(f"{country:12} ref={ref:6} live={live_cs} units={ok} sell={has_sell}")
        report_rows.append((country, ref, live_cs, units, has_sell))

    # no new Object definitions in transfer file
    if re.search(r"(?im)^Object(?:Reskin)?\s+", text):
        errors.append("transfer file defines objects")

    print(f"\nErrors: {len(errors)}")
    for e in errors:
        print(" FAIL", e)
    if errors:
        return 1
    print("WARFACTORY_TRANSFER_AUDIT_OK")
    out = Path("/tmp/wf_inspect/TRANSFER_AUDIT.txt")
    lines = ["WARFACTORY_TRANSFER_AUDIT_OK", ""]
    for country, ref, live_cs, units, has_sell in report_rows:
        lines.append(f"{country}  reference={ref}  CommandSet={live_cs}  sell={has_sell}")
        for slot, btn, obj, ex in units:
            lines.append(f"  {slot:>2} {btn} -> {obj}")
        lines.append("")
    out.write_text("\n".join(lines))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
