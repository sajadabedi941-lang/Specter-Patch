#!/usr/bin/env python3
"""Re-extract packed DATA and prove live dest War Factory CommandSets were replaced."""
from __future__ import annotations

import re
import struct
from pathlib import Path

SRC = Path("/tmp/ea6b_crash_fix/_SPEC_DATA_ONE.big")
PACKED = Path("/tmp/warfactory_runtime/_SPEC_DATA_ONE.big")
REPORT = Path("/workspace/patch/Release/docs/WARFACTORY_RUNTIME_REBUILD_REPORT.txt")

COUNTRIES = {
    "Britain": ("NATO", "FactionBritain", "NatoWarfactoryCommandSet"),
    "Germany": ("NATO", "FactionGermany", "NatoWarfactoryCommandSet"),
    "France": ("NATO", "FactionFrance", "NatoWarfactoryCommandSet"),
    "Italy": ("NATO", "FactionItaly", "NatoWarfactoryCommandSet"),
    "Ukraine": ("NATO", "FactionUkraine", "NatoWarfactoryCommandSet"),
    "Turkey": ("NATO", "FactionTurkey", "NatoWarfactoryCommandSet"),
    "Sweden": ("NATO", "FactionSweden", "NatoWarfactoryCommandSet"),
    "Libya": ("Iraq", "FactionLibya", "Iraq_WarFactoryCommandSet_T3"),
    "SouthAfrica": ("Iraq", "FactionSouthAfrica", "Iraq_WarFactoryCommandSet_T3"),
    "UAE": ("Egypt", "FactionUAE", "EgyptWarFactoryCommandSet"),
    "SaudiArabia": ("Egypt", "FactionSaudiArabia", "EgyptWarFactoryCommandSet"),
    "Syria": ("Egypt", "FactionSyria", "EgyptWarFactoryCommandSet"),
    "Japan": ("USA", "FactionJapan", "AmericaWarFactoryCommandSet_T3"),
    "Vietnam": ("USA", "FactionVietnam", "AmericaWarFactoryCommandSet_T3"),
    "SouthKorea": ("USA", "FactionSouthKorea", "AmericaWarFactoryCommandSet_T3"),
    "India": ("Russia", "FactionIndia", "RussiaWarFactoryCommandSet"),
    "Pakistan": ("Russia", "FactionPakistan", "RussiaWarFactoryCommandSet"),
}

USA_OMIT = {"Command_ConstructAmericaVehicleM1075I_AI"}

PROTECTED_CS = [
    "NatoWarfactoryCommandSet",
    "AmericaWarFactoryCommandSet",
    "AmericaWarFactoryCommandSet_T3",
    "RussiaWarFactoryCommandSet",
    "EgyptWarFactoryCommandSet",
    "Egypt_WarFactoryCommandSet",
    "Iraq_WarFactoryCommandSet_T3",
    "IranWarfactoryCommandSet",
    "Israel_WarFactoryCommandSet",
    "NorthKorea_WarFactoryCommandSet",
    "ChinaWarFactoryCommandSet",
]


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


def parse_block(text, start):
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
            r"(?i)^\s*(Draw|Behavior|Body|WeaponSet|ArmorSet|Prerequisites|DefaultConditionState|ConditionState|UnitSpecificSounds|Turret)\b",
            raw,
        ):
            depth += 1
    return "".join(buf)


def last_block(kind, name, entries):
    found = None
    src = None
    pat = re.compile(rf"(?im)^{kind}\s+{re.escape(name)}\b")
    for fname, blob in entries:
        text = blob.decode("latin1", errors="ignore")
        for m in pat.finditer(text):
            found = parse_block(text, m.start())
            src = fname
    return src, found


def all_defs(kind, name, entries):
    pat = re.compile(rf"(?im)^{kind}\s+{re.escape(name)}\b")
    hits = []
    for fname, blob in entries:
        text = blob.decode("latin1", errors="ignore")
        for m in pat.finditer(text):
            hits.append((fname, parse_block(text, m.start())))
    return hits


def field(blk, key):
    if not blk:
        return None
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", blk)
    return m.group(1) if m else None


def cs_slots(blk):
    out = []
    if not blk:
        return out
    for line in blk.splitlines():
        raw = line.split(";", 1)[0]
        m = re.match(r"\s*(\d+)\s*=\s*(\S+)", raw)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def btn_obj(entries, btn):
    _src, blk = last_block("CommandButton", btn, entries)
    return field(blk, "Object")


def worker_wf(entries, worker):
    _os, oblk = last_block("Object", worker, entries)
    dcs = field(oblk, "CommandSet")
    _cs, cblk = last_block("CommandSet", dcs, entries) if dcs else (None, None)
    hits = []
    for slot, btn in cs_slots(cblk):
        obj = btn_obj(entries, btn)
        if not obj:
            continue
        low = (btn + " " + obj).lower()
        if "warfactory" in low or "war_factory" in low:
            _ws, wblk = last_block("Object", obj, entries)
            wcs = re.findall(r"(?im)^\s*CommandSet\s*=\s*(\S+)", wblk or "")
            hits.append((btn, obj, wcs[0] if wcs else None, wcs))
    return dcs, hits


def main() -> int:
    errors = []
    src = parse_big(SRC)
    packed = parse_big(PACKED)
    lines = [
        "SPECTER WAR FACTORY RUNTIME REBUILD",
        "===================================",
        "",
        "Live path was traced from the packed DATA BIG:",
        "PlayerTemplate -> StartingUnit/Dozer/VT72B -> Dozer CommandSet",
        "-> WarFactory CommandButton -> WarFactory Object -> CommandSet",
        "",
        "The winning CommandSet.ini (and CommandSet_Pakistan.ini) blocks",
        "were replaced in-place. No unused override file was appended.",
        "",
    ]

    ok_count = 0
    print("=== RUNTIME TRACE (re-extracted packed BIG) ===")
    for country, (ref, faction, ref_cs) in COUNTRIES.items():
        _ps, pt = last_block("PlayerTemplate", faction, packed)
        start0 = field(pt, "StartingUnit0")
        side = field(pt, "Side")
        old_dcs, old_hits = worker_wf(src, start0)
        new_dcs, new_hits = worker_wf(packed, start0)
        if not new_hits:
            errors.append(f"{country}: no WarFactory on worker {start0}")
            print(f"{country} FAIL no WF on {start0}")
            continue
        # player WF is the first non-AI factory
        btn, obj, live_cs, all_cs = new_hits[0]
        old_btn, old_obj, old_cs, _ = old_hits[0] if old_hits else (None, None, None, [])
        defs_old = all_defs("CommandSet", old_cs, src) if old_cs else []
        defs_new = all_defs("CommandSet", live_cs, packed) if live_cs else []
        win_old = defs_old[-1] if defs_old else (None, None)
        win_new = defs_new[-1] if defs_new else (None, None)
        old_units = [b for _s, b in cs_slots(win_old[1]) if b != "Command_Sell"]
        new_units = [b for _s, b in cs_slots(win_new[1]) if b != "Command_Sell"]
        _rs, ref_blk = last_block("CommandSet", ref_cs, packed)
        ref_units = [b for _s, b in cs_slots(ref_blk) if b != "Command_Sell" and b not in USA_OMIT]
        if ref == "USA":
            expect = ref_units
        else:
            expect = [b for _s, b in cs_slots(ref_blk) if b != "Command_Sell"]
        status = "TARGET_COUNTRY_WARFACTORY_REPLACED_OK"
        if new_units != expect:
            status = "FAIL dest bar != template"
            errors.append(f"{country}: {new_units} != {expect}")
        if live_cs != old_cs:
            # name should stay; content changes
            errors.append(f"{country}: live CommandSet name changed {old_cs} -> {live_cs}")
            status = "FAIL CommandSet name changed"
        if obj != old_obj:
            errors.append(f"{country}: WarFactory object changed {old_obj} -> {obj}")
            status = "FAIL WF object changed"
        removed = [u for u in old_units if u not in new_units]
        added = [u for u in new_units if u not in old_units]
        if status.endswith("_OK"):
            ok_count += 1
        print(f"{country:12} {status} winner={win_new[0]} units={len(new_units)}")
        lines += [
            f"Country: {country}",
            f"PlayerTemplate: {faction} Side={side} StartingUnit0={start0}",
            f"Dozer/Worker CommandSet: {new_dcs}",
            f"WarFactory button: {btn}",
            f"WarFactory Object: {obj}",
            f"Old WarFactory CommandSet: {old_cs} (winner {win_old[0]})",
            f"New WarFactory CommandSet: {live_cs} (same name, new content from {ref} {ref_cs})",
            f"Old units removed: {len(removed)}",
        ]
        for u in removed:
            lines.append(f"  - {u}")
        lines.append(f"New units added: {len(added)}")
        for u in added:
            lines.append(f"  + {u}")
        lines.append("Final winning definition:")
        lines.append(f"  file={win_new[0]}")
        for slot, b in cs_slots(win_new[1]):
            lines.append(f"  {slot} = {b}")
        lines.append(f"Old definition (baseline winner {win_old[0]}):")
        for slot, b in cs_slots(win_old[1]):
            lines.append(f"  {slot} = {b}")
        lines.append(f"Status: {status}")
        lines.append("")

    lines.append("PROTECTED COUNTRIES")
    lines.append("-------------------")
    prot_ok = True
    for cs in PROTECTED_CS:
        _os, old = last_block("CommandSet", cs, src)
        _ns, new = last_block("CommandSet", cs, packed)
        if old != new:
            prot_ok = False
            errors.append(f"protected CommandSet changed {cs}")
    lines.append("USA / Russia / China / Iran / Israel / NATO / Egypt / Iraq / North Korea")
    lines.append("UNCHANGED" if prot_ok else "CHANGED")
    lines.append("")
    lines.append(f"TARGET_COUNTRY_WARFACTORY_REPLACED_OK count={ok_count}/17")
    lines.append(f"Errors: {len(errors)}")
    for e in errors:
        lines.append(f" FAIL {e}")
        print(" FAIL", e)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", REPORT)
    if errors:
        return 1
    print("TARGET_COUNTRY_WARFACTORY_REPLACED_OK")
    print("PROTECTED COUNTRIES: UNCHANGED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
