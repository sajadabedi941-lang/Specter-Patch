#!/usr/bin/env python3
"""Re-extract packed DATA and prove dest War Factory units are unlocked."""
from __future__ import annotations

import re
import struct
from pathlib import Path

BASE = Path("/tmp/warfactory_runtime/_SPEC_DATA_ONE.big")
PACKED = Path("/tmp/warfactory_unlock/_SPEC_DATA_ONE.big")
REPORT = Path("/workspace/patch/Release/docs/WARFACTORY_UNLOCK_REPORT.txt")

LIVE = {
    "Britain": ("FactionBritain", "BritainWarFactory", "BritainWarfactoryCommandSet"),
    "Germany": ("FactionGermany", "GermanyWarFactory", "GermanyWarfactoryCommandSet"),
    "France": ("FactionFrance", "FranceWarFactory", "FranceWarfactoryCommandSet"),
    "Italy": ("FactionItaly", "ItalyWarFactory", "ItalyWarfactoryCommandSet"),
    "Ukraine": ("FactionUkraine", "UkraineWarFactory", "UkraineWarfactoryCommandSet"),
    "Turkey": ("FactionTurkey", "TurkeyWarFactory", "TurkeyWarfactoryCommandSet"),
    "Sweden": ("FactionSweden", "SwedenWarFactory", "SwedenWarfactoryCommandSet"),
    "Libya": ("FactionLibya", "Libya_WarFactory_T", "Libya_WarFactoryCommandSet"),
    "SouthAfrica": ("FactionSouthAfrica", "SouthAfrica_WarFactory_T", "SouthAfrica_WarFactoryCommandSet"),
    "UAE": ("FactionUAE", "UAE_WarFactory_T", "UAE_WarFactoryCommandSet"),
    "SaudiArabia": ("FactionSaudiArabia", "SaudiArabia_WarFactory_T", "SaudiArabia_WarFactoryCommandSet"),
    "Syria": ("FactionSyria", "Syria_WarFactory_T", "Syria_WarFactoryCommandSet"),
    "Japan": ("FactionJapan", "Japan_WarFactory", "Japan_WarFactoryCommandSet"),
    "Vietnam": ("FactionVietnam", "Vietnam_WarFactory", "Vietnam_WarFactoryCommandSet"),
    "SouthKorea": ("FactionSouthKorea", "SouthKorea_WarFactory", "SouthKorea_WarFactoryCommandSet"),
    "India": ("FactionIndia", "India_WarFactory_T", "India_WarFactoryCommandSet"),
    "Pakistan": ("FactionPakistan", "Pakistan_WarFactory_T", "Pakistan_WarFactoryCommandSet"),
}

PROTECTED_CS = [
    "NatoWarfactoryCommandSet",
    "AmericaWarFactoryCommandSet",
    "AmericaWarFactoryCommandSet_T3",
    "RussiaWarFactoryCommandSet",
    "EgyptWarFactoryCommandSet",
    "Iraq_WarFactoryCommandSet_T3",
    "IranWarfactoryCommandSet",
    "Israel_WarFactoryCommandSet",
    "NorthKorea_WarFactoryCommandSet",
    "ChinaWarFactoryCommandSet",
]

SKIP = {"Command_Sell", "Command_SetRallyPoint"}


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


def index_kind(kind, entries, reskin=False):
    blocks, srcs = {}, {}
    pat = re.compile(rf"(?im)^{kind}\s+(\S+)")
    if reskin:
        pat = re.compile(r"(?im)^Object(?:Reskin)?\s+(\S+)")
    for fname, blob in entries:
        text = blob.decode("latin1", errors="ignore")
        for m in pat.finditer(text):
            name = m.group(1)
            blocks[name] = parse_block(text, m.start())
            srcs[name] = fname
    return blocks, srcs


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


def lock_prereq(oblk):
    if not oblk:
        return "MISSING_OBJECT"
    m = re.search(r"(?ims)^\s*Prerequisites\b.*?^\s*End\b", oblk)
    if not m:
        return None
    body = m.group(0)
    if re.search(r"(?im)^\s*(Object|Science)\s*=", body):
        return " ".join(body.split())
    return None


def main() -> int:
    errors = []
    print("index packed")
    packed_e = parse_big(PACKED)
    base_e = parse_big(BASE)
    pcs, pcs_src = index_kind("CommandSet", packed_e)
    pbtn, _ = index_kind("CommandButton", packed_e)
    pobj, pobj_src = index_kind("Object", packed_e, reskin=True)
    bcs, _ = index_kind("CommandSet", base_e)

    lines = [
        "SPECTER WAR FACTORY START-UNLOCK AUDIT",
        "======================================",
        "",
        "Re-extracted packed DATA. Dest War Factory units must be",
        "visible and buildable at game start (no Science / Object /",
        "tier / CommandSetUpgrade locks).",
        "",
    ]

    print("=== DEST UNLOCK TRACE ===")
    ok = 0
    for country, (faction, building, live_cs) in LIVE.items():
        bblk = pobj.get(building)
        upgrades = len(re.findall(r"(?i)Behavior\s*=\s*CommandSetUpgrade", bblk or ""))
        cblk = pcs.get(live_cs)
        winner = pcs_src.get(live_cs)
        units = []
        locked_here = []
        for slot, btn in cs_slots(cblk):
            if btn in SKIP:
                continue
            obj = field(pbtn.get(btn), "Object")
            pre = lock_prereq(pobj.get(obj)) if obj else "NO_OBJECT"
            status = "UNLOCKED"
            if pre:
                status = f"LOCKED {pre}"
                locked_here.append(f"{btn}->{obj}")
                errors.append(f"{country}: {btn} -> {obj} still locked")
            if obj not in pobj:
                status = "MISSING_OBJECT"
                errors.append(f"{country}: missing object {obj}")
            units.append((slot, btn, obj, status, pobj_src.get(obj)))
        if upgrades:
            errors.append(f"{country}: CommandSetUpgrade still present ({upgrades})")
        if not locked_here and not upgrades:
            ok += 1
            st = "UNLOCKED_AT_GAME_START"
        else:
            st = "FAIL"
        print(f"{country:12} {st} cs={live_cs} winner={winner} units={len(units)} upgrades={upgrades}")
        lines += [
            f"Country: {country}",
            f"PlayerTemplate: {faction}",
            f"WarFactory Object: {building}",
            f"CommandSet: {live_cs} winner={winner}",
            f"CommandSetUpgrade modules: {upgrades}",
            "Unlocked WarFactory units:",
        ]
        for slot, btn, obj, status, src in units:
            lines.append(f"  {slot:>2} {btn} -> {obj} [{status}] src={src}")
        lines.append(f"Status: {st}")
        lines.append("")

    lines.append("PROTECTED COUNTRIES")
    prot_ok = True
    for cs in PROTECTED_CS:
        if bcs.get(cs) != pcs.get(cs):
            prot_ok = False
            errors.append(f"protected CommandSet changed {cs}")
    lines.append("USA / Russia / China / Iran / Israel / NATO / Egypt / Iraq / North Korea")
    lines.append("UNCHANGED" if prot_ok else "CHANGED")
    lines.append("")
    lines.append(f"DEST_WARFACTORY_UNLOCKED_OK count={ok}/17")
    lines.append(f"Errors: {len(errors)}")
    for e in errors:
        lines.append(f" FAIL {e}")
        print(" FAIL", e)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", REPORT)
    if errors:
        return 1
    print("DEST_WARFACTORY_UNLOCKED_OK")
    print("PROTECTED COUNTRIES: UNCHANGED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
