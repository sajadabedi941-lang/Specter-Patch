#!/usr/bin/env python3
"""Packed-BIG audit for the national WMD completion."""

from __future__ import annotations

import hashlib
import io
import re
import struct
import sys
from pathlib import Path

DATA = Path("/tmp/national_wmd/_SPEC_DATA_ONE.big")
SRC = Path("/tmp/usa_jp_visual_buttons/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/national_wmd_audit.txt")

NUCLEAR_FACTIONS = {
    "FactionAmerica": "AmericaSpecialPowerLGM30G",
    "FactionRussia": "RussiaSpecialPowerRS28",
    "FactionChina": "ChinaSpecialPowerDF5C",
    "FactionBritain": "BritainSpecialPowerTrident",
    "FactionFrance": "FranceSpecialPowerM51",
    "FactionIndia": "IndiaSpecialPowerAgniV",
    "FactionPakistan": "PakistanSpecialPowerShaheenIII",
    "FactionNorthKorea": "NorthKorea_NuclearMissile",
    "FactionIsrael": "IsraelSpecialPowerJerichoIII",
}

NON_NUCLEAR = {
    "FactionIran": ["Iran_SejjilMissile", "Iran_ChemicalStrike", "Iran_BiologicalWeapon"],
    "FactionJapan": ["Japan_Type12Missile", "Japan_ChemicalDefense"],
    "FactionGermany": ["Germany_TaurusMissile", "Germany_ChemicalStrike"],
    "FactionSouthKorea": ["SouthKorea_HyunmooMissile", "SouthKorea_BiologicalWeapon"],
    "FactionTurkey": ["Turkey_BoraMissile", "Turkey_ChemicalStrike"],
    "FactionItaly": ["Italy_StormShadowMissile", "Italy_BiologicalWeapon"],
    "FactionEgypt": ["Egypt_ScudDMissile", "Egypt_ChemicalStrike"],
    "FactionVietnam": ["Vietnam_K300Missile", "Vietnam_BiologicalWeapon"],
    "FactionSaudiArabia": ["SaudiArabia_AbabilMissile", "SaudiArabia_ChemicalStrike"],
    "FactionUAE": ["UAE_ThunderMissile", "UAE_BiologicalWeapon"],
    "FactionUkraine": ["Ukraine_Hrim2Missile", "Ukraine_ChemicalStrike"],
    "FactionSyria": ["Syria_ScudMissile", "Syria_ChemicalStrike"],
    "FactionLibya": ["Libya_ScudBMissile", "Libya_BiologicalWeapon"],
    "FactionSouthAfrica": ["SouthAfrica_RaptorMissile", "SouthAfrica_ChemicalStrike"],
    "FactionSweden": ["Sweden_RBS15Missile", "Sweden_BiologicalDefense"],
}

NUCLEAR_POWERS = set(NUCLEAR_FACTIONS.values())
ALL_WMD = set(NUCLEAR_POWERS)
for powers in NON_NUCLEAR.values():
    ALL_WMD.update(powers)

LOCKED_PATHS = {
    r"data\ini\science.ini",
    r"data\ini\object\specter\japan self-defense forces\tracked\japan_vt72b.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_commandcenter.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_airfield.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_largeairbase.ini",
    r"data\ini\object\specter\japan self-defense forces\buildings\japan_heavyairbase.ini",
}

OCL = {
    "nuke": "SUPERWEAPON_AmericaLGM30G",
    "missile": "SUPERWEAPON_SejjilAttack",
    "chem": "SUPERWEAPON_Arab_Jarrah",
    "bio": "SUPERWEAPON_AnthraxBomb",
}


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


def named(text, kind, name):
    m = re.search(rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^[Ee][Nn][Dd]\s*$", text)
    return m.group(0) if m else None


def walk_csf(blob):
    pos = 24
    nlab = struct.unpack_from("<I", blob, 8)[0]
    out = {}
    for _ in range(nlab):
        if blob[pos : pos + 4] != b" LBL":
            break
        nstr, namelen = struct.unpack_from("<II", blob, pos + 4)
        pos += 12
        name = blob[pos : pos + namelen].decode("latin1", "replace")
        pos += namelen
        vals = []
        for _s in range(nstr):
            mag = blob[pos : pos + 4]
            slen = struct.unpack_from("<I", blob, pos + 4)[0]
            pos += 8
            raw = blob[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(x ^ 0xFF for x in raw).decode("utf-16-le", "replace")
            if mag == b"WRTS":
                elen = struct.unpack_from("<I", blob, pos)[0]
                pos += 4 + elen
            vals.append(val)
        out[name] = vals[0] if vals else ""
    return out


def field(blk: str, key: str) -> str | None:
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*(\S+)", blk)
    return m.group(1) if m else None


def all_named(text: str, kind: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(rf"(?ms)^{kind}\s+(\S+)\s*\r?\n.*?^[Ee][Nn][Dd]\s*$", text):
        out[m.group(1)] = m.group(0)
    return out


def last_object(entries, obj):
    hits = []
    for _i, n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        if re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", t):
            m = re.search(rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)", t)
            hits.append((n, m.group(0) if m else t))
    return hits[-1] if hits else None


def player_shortcut(pt: str, faction: str) -> str | None:
    m = re.search(
        rf"(?ms)^PlayerTemplate\s+{re.escape(faction)}\s*\r?\n.*?^\s*SpecialPowerShortcutCommandSet\s*=\s*(\S+)",
        pt,
    )
    return m.group(1) if m else None


def commandset_buttons(cs_map: dict[str, str], name: str) -> list[str]:
    blk = cs_map.get(name)
    if not blk:
        return []
    return re.findall(r"(?m)^\s*\d+\s*=\s*(\S+)", blk)


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


def _run() -> int:
    errors = []
    data = parse_big(DATA)
    src = parse_big(SRC)
    dst_idx = {n.replace("/", "\\").lower(): b for _i, n, b in data}
    src_idx = {n.replace("/", "\\").lower(): b for _i, n, b in src}

    sha = hashlib.sha256(DATA.read_bytes()).hexdigest()
    print("DATA_SHA256", sha)
    print("DATA_BYTES", DATA.stat().st_size)
    print("DATA_FILES", len(data))

    if [n for _i, n, _b in data] != [n for _i, n, _b in src]:
        errors.append("BIG entry order changed")

    for locked in LOCKED_PATHS:
        if locked in src_idx and src_idx[locked] != dst_idx.get(locked):
            errors.append(f"locked path mutated: {locked}")

    sp_text = dst_idx[r"data\ini\specialpower.ini"].decode("latin1")
    cb_parts = [
        b.decode("latin1")
        for key, b in dst_idx.items()
        if key.startswith(r"data\ini\commandbutton") and key.endswith(".ini")
    ]
    cb_text = "\n".join(cb_parts)
    cs_parts = [dst_idx[r"data\ini\commandset.ini"].decode("latin1")]
    for extra in (
        r"data\ini\commandset_egypt.ini",
        r"data\ini\commandset_israel.ini",
        r"data\ini\commandset_pakistan.ini",
    ):
        if extra in dst_idx:
            cs_parts.append(dst_idx[extra].decode("latin1"))
    cs_text = "\n".join(cs_parts)
    pt_text = dst_idx[r"data\ini\playertemplate.ini"].decode("latin1")
    pt_patch = dst_idx.get(r"data\ini\playertemplate_specterpatch.ini", b"").decode("latin1")
    ocl_text = dst_idx[r"data\ini\objectcreationlist.ini"].decode("latin1")
    csf = walk_csf(dst_idx[r"data\english\generals.csf"])

    powers = all_named(sp_text, "SpecialPower")
    buttons = all_named(cb_text, "CommandButton")
    commandsets = all_named(cs_text, "CommandSet")
    ocls = set(re.findall(r"(?m)^ObjectCreationList\s+(\S+)", ocl_text))

    objects = set()
    for _i, n, b in data:
        if n.lower().endswith(".ini"):
            objects.update(re.findall(r"(?m)^Object\s+(\S+)", b.decode("latin1", "replace")))

    print("\n=== SpecialPower WMD ===")
    for name in sorted(ALL_WMD):
        blk = powers.get(name)
        if not blk:
            errors.append(f"missing SpecialPower {name}")
            print("MISS", name)
            continue
        reload = field(blk, "ReloadTime")
        enum = field(blk, "Enum")
        req = field(blk, "RequiredScience")
        ok = reload == "1200000" and req is None
        if name in NUCLEAR_POWERS and enum != "SPECIAL_NEUTRON_MISSILE":
            ok = False
            errors.append(f"{name} enum {enum} != SPECIAL_NEUTRON_MISSILE")
        if reload != "1200000":
            errors.append(f"{name} ReloadTime {reload}")
        if req:
            errors.append(f"{name} still has RequiredScience {req}")
        print(("OK" if ok else "FAIL"), name, "reload", reload, "enum", enum)

    print("\n=== CommandButton -> SpecialPower / Object ===")
    wmd_buttons = []
    for bname, blk in buttons.items():
        power = field(blk, "SpecialPower")
        obj = field(blk, "Object")
        if power in ALL_WMD or (power and power in NUCLEAR_POWERS):
            wmd_buttons.append(bname)
            if power not in powers:
                errors.append(f"button {bname} SpecialPower {power} missing")
            for key in ("TextLabel", "DescriptLabel"):
                lab = field(blk, key)
                if lab and lab not in csf:
                    errors.append(f"button {bname} CSF missing {lab}")
            sci = field(blk, "Science")
            if sci:
                errors.append(f"WMD button {bname} has Science {sci}")
        if obj and obj not in objects:
            # only flag buttons we added or WMD-related select/system
            if "WMD" in bname or "National" in bname or bname.startswith("Command_Launch") and "FromShortcut" in bname:
                errors.append(f"button {bname} Object {obj} missing")

    # Every new WMD shortcut button must exist and point at a live SpecialPower
    required_buttons = [
        "Command_LaunchBritainTridentFromShortcut",
        "Command_LaunchFranceM51FromShortcut",
        "Command_LaunchIndiaAgniVFromShortcut",
        "Command_LaunchPakistanShaheenFromShortcut",
        "Command_LaunchIranChemicalFromShortcut",
        "Command_LaunchIranBiologicalFromShortcut",
        "Command_LaunchJapanType12FromShortcut",
        "Command_LaunchJapanChemicalDefenseFromShortcut",
        "Command_LaunchGermanyTaurusFromShortcut",
        "Command_LaunchGermanyChemicalFromShortcut",
        "Command_LaunchSouthKoreaHyunmooFromShortcut",
        "Command_LaunchSouthKoreaBiologicalFromShortcut",
        "Command_LaunchTurkeyBoraFromShortcut",
        "Command_LaunchTurkeyChemicalFromShortcut",
        "Command_LaunchItalyStormShadowFromShortcut",
        "Command_LaunchItalyBiologicalFromShortcut",
        "Command_LaunchEgyptScudDFromShortcut",
        "Command_LaunchEgyptChemicalFromShortcut",
        "Command_LaunchVietnamK300FromShortcut",
        "Command_LaunchVietnamBiologicalFromShortcut",
        "Command_LaunchSaudiAbabilFromShortcut",
        "Command_LaunchSaudiChemicalFromShortcut",
        "Command_LaunchUAEThunderFromShortcut",
        "Command_LaunchUAEBiologicalFromShortcut",
        "Command_LaunchUkraineHrim2FromShortcut",
        "Command_LaunchUkraineChemicalFromShortcut",
        "Command_LaunchSyriaScudFromShortcut",
        "Command_LaunchSyriaChemicalFromShortcut",
        "Command_LaunchLibyaScudBFromShortcut",
        "Command_LaunchLibyaBiologicalFromShortcut",
        "Command_LaunchSouthAfricaRaptorFromShortcut",
        "Command_LaunchSouthAfricaChemicalFromShortcut",
        "Command_LaunchSwedenRBS15FromShortcut",
        "Command_LaunchSwedenBiologicalDefenseFromShortcut",
        "Command_LaunchLgm30FromShortcut",
        "Command_LaunchRS28FromShortcut",
        "Command_LaunchLaunchDF5CFromShortcut",
        "Command_LaunchJerichoIIIFromShortcut",
        "Command_LaunchNorthKoreaNuclearFromShortcut",
        "Command_SejjilFireFromShortcut",
        "Command_LaunchJapanNuclearFromShortcut",
        "Command_LaunchSouthKoreaNuclearFromShortcut",
        "Command_LaunchVietnamNuclearFromShortcut",
    ]
    for bname in required_buttons:
        blk = buttons.get(bname)
        if not blk:
            errors.append(f"missing CommandButton {bname}")
            continue
        power = field(blk, "SpecialPower")
        if power not in powers:
            errors.append(f"{bname} SpecialPower {power} missing")
        print("BTN", bname, "->", power)

    print("\n=== CommandSet buttons exist ===")
    required_sets = {
        "SpecialPowerShortcutUSA": ["Command_LaunchLgm30FromShortcut"],
        "SpecialPowerShortcutRussia": ["Command_LaunchRS28FromShortcut"],
        "SpecialPowerShortcutChina": ["Command_LaunchLaunchDF5CFromShortcut"],
        "SpecialPowerShortcutNorthKorea": ["Command_LaunchNorthKoreaNuclearFromShortcut"],
        "SpecialPowerShortcutIRAN": [
            "Command_SejjilFireFromShortcut",
            "Command_LaunchIranChemicalFromShortcut",
            "Command_LaunchIranBiologicalFromShortcut",
        ],
        "SpecialPowerShortcutBritainCommandSet": ["Command_LaunchBritainTridentFromShortcut"],
        "SpecialPowerShortcutFranceCommandSet": ["Command_LaunchFranceM51FromShortcut"],
        "SpecialPowerShortcutGermanyCommandSet": [
            "Command_LaunchGermanyTaurusFromShortcut",
            "Command_LaunchGermanyChemicalFromShortcut",
        ],
        "SpecialPowerShortcutItalyCommandSet": [
            "Command_LaunchItalyStormShadowFromShortcut",
            "Command_LaunchItalyBiologicalFromShortcut",
        ],
        "SpecialPowerShortcutSwedenCommandSet": [
            "Command_LaunchSwedenRBS15FromShortcut",
            "Command_LaunchSwedenBiologicalDefenseFromShortcut",
        ],
        "SpecialPowerShortcutUkraineCommandSet": [
            "Command_LaunchUkraineHrim2FromShortcut",
            "Command_LaunchUkraineChemicalFromShortcut",
        ],
        "SpecialPowerShortcutTurkeyCommandSet": [
            "Command_LaunchTurkeyBoraFromShortcut",
            "Command_LaunchTurkeyChemicalFromShortcut",
        ],
        "SpecialPowerShortcutSaudiArabia": [
            "Command_LaunchSaudiAbabilFromShortcut",
            "Command_LaunchSaudiChemicalFromShortcut",
        ],
        "SpecialPowerShortcutUAE": [
            "Command_LaunchUAEThunderFromShortcut",
            "Command_LaunchUAEBiologicalFromShortcut",
        ],
        "SpecialPowerShortcutIndia": ["Command_LaunchIndiaAgniVFromShortcut"],
        "SpecialPowerShortcutSyria": [
            "Command_LaunchSyriaScudFromShortcut",
            "Command_LaunchSyriaChemicalFromShortcut",
        ],
        "SpecialPowerShortcutLibya": [
            "Command_LaunchLibyaScudBFromShortcut",
            "Command_LaunchLibyaBiologicalFromShortcut",
        ],
        "SpecialPowerShortcutSouthAfrica": [
            "Command_LaunchSouthAfricaRaptorFromShortcut",
            "Command_LaunchSouthAfricaChemicalFromShortcut",
        ],
        "SpecialPowerShortcutPakistan": ["Command_LaunchPakistanShaheenFromShortcut"],
        "SpecialPowerShortcutJapan": [
            "Command_LaunchJapanType12FromShortcut",
            "Command_LaunchJapanChemicalDefenseFromShortcut",
        ],
        "SpecialPowerShortcutSouthKorea": [
            "Command_LaunchSouthKoreaHyunmooFromShortcut",
            "Command_LaunchSouthKoreaBiologicalFromShortcut",
        ],
        "SpecialPowerShortcutVietnam": [
            "Command_LaunchVietnamK300FromShortcut",
            "Command_LaunchVietnamBiologicalFromShortcut",
        ],
        "SpecialPowerShortcutEgyptSystem": [
            "Command_LaunchEgyptScudDFromShortcut",
            "Command_LaunchEgyptChemicalFromShortcut",
        ],
        "SpecialPowerShortcutIsraelSystem": ["Command_LaunchJerichoIIIFromShortcut"],
    }
    for cs_name, need in required_sets.items():
        have = commandset_buttons(commandsets, cs_name)
        if cs_name not in commandsets:
            errors.append(f"missing CommandSet {cs_name}")
            print("MISS CS", cs_name)
            continue
        missing = [b for b in need if b not in have]
        if missing:
            errors.append(f"{cs_name} missing buttons {missing}")
        leaked_nuke = []
        if cs_name not in (
            "SpecialPowerShortcutUSA",
            "SpecialPowerShortcutRussia",
            "SpecialPowerShortcutChina",
            "SpecialPowerShortcutNorthKorea",
            "SpecialPowerShortcutIsraelSystem",
            "SpecialPowerShortcutBritainCommandSet",
            "SpecialPowerShortcutFranceCommandSet",
            "SpecialPowerShortcutIndia",
            "SpecialPowerShortcutPakistan",
        ):
            for b in have:
                blk = buttons.get(b, "")
                p = field(blk, "SpecialPower") if blk else None
                if p in NUCLEAR_POWERS:
                    leaked_nuke.append(b)
        if leaked_nuke:
            errors.append(f"{cs_name} still has nuclear buttons {leaked_nuke}")
        print(("OK" if not missing and not leaked_nuke else "FAIL"), cs_name, have)

        for b in have:
            if b not in buttons:
                errors.append(f"{cs_name} button {b} not defined")

    print("\n=== PlayerTemplate shortcuts ===")
    expected_pt = {
        "FactionAmerica": "SpecialPowerShortcutUSA",
        "FactionRussia": "SpecialPowerShortcutRussia",
        "FactionChina": "SpecialPowerShortcutChina",
        "FactionNorthKorea": "SpecialPowerShortcutNorthKorea",
        "FactionIran": "SpecialPowerShortcutIRAN",
        "FactionBritain": "SpecialPowerShortcutBritainCommandSet",
        "FactionFrance": "SpecialPowerShortcutFranceCommandSet",
        "FactionIndia": "SpecialPowerShortcutIndia",
        "FactionPakistan": "SpecialPowerShortcutPakistan",
        "FactionJapan": "SpecialPowerShortcutJapan",
        "FactionGermany": "SpecialPowerShortcutGermanyCommandSet",
        "FactionSouthKorea": "SpecialPowerShortcutSouthKorea",
        "FactionTurkey": "SpecialPowerShortcutTurkeyCommandSet",
        "FactionItaly": "SpecialPowerShortcutItalyCommandSet",
        "FactionVietnam": "SpecialPowerShortcutVietnam",
        "FactionSaudiArabia": "SpecialPowerShortcutSaudiArabia",
        "FactionUAE": "SpecialPowerShortcutUAE",
        "FactionUkraine": "SpecialPowerShortcutUkraineCommandSet",
        "FactionSyria": "SpecialPowerShortcutSyria",
        "FactionLibya": "SpecialPowerShortcutLibya",
        "FactionSouthAfrica": "SpecialPowerShortcutSouthAfrica",
        "FactionSweden": "SpecialPowerShortcutSwedenCommandSet",
    }
    for faction, cs_name in expected_pt.items():
        got = player_shortcut(pt_text, faction)
        if got != cs_name:
            errors.append(f"{faction} shortcut {got} != {cs_name}")
        print(("OK" if got == cs_name else "FAIL"), faction, got)

    if player_shortcut(pt_patch, "FactionEgypt") != "SpecialPowerShortcutEgyptSystem":
        errors.append("Egypt SpecterPatch shortcut lost")
    if player_shortcut(pt_patch, "FactionIsrael") != "SpecialPowerShortcutIsraelSystem":
        errors.append("Israel SpecterPatch shortcut lost")
    print("Egypt overlay", player_shortcut(pt_patch, "FactionEgypt"))
    print("Israel overlay", player_shortcut(pt_patch, "FactionIsrael"))

    src_pt = src_idx[r"data\ini\playertemplate.ini"].decode("latin1")
    dst_pt = pt_text
    src_lines = src_pt.splitlines()
    dst_lines = dst_pt.splitlines()
    extra_changes = []
    for a, b in zip(src_lines, dst_lines):
        if a != b and "SpecialPowerShortcutCommandSet" not in a and "SpecialPowerShortcutCommandSet" not in b:
            extra_changes.append((a.strip(), b.strip()))
    if extra_changes:
        errors.append(f"PlayerTemplate changed non-shortcut lines: {extra_changes[:5]}")
    print("PlayerTemplate non-shortcut diffs", len(extra_changes))

    print("\n=== System objects grant WMD ===")
    system_expect = {
        "AmericaSystemSpecialPowerShortcut": ["AmericaSpecialPowerLGM30G"],
        "RussiaSystemSpecialPowerShortcut": ["RussiaSpecialPowerRS28"],
        "ChinaSystemSpecialPowerShortcut": ["ChinaSpecialPowerDF5C"],
        "IsraelSystemSpecialPowerShortcut": ["IsraelSpecialPowerJerichoIII"],
        "NorthKoreaSystemSpecialPowerShortcut": ["NorthKorea_NuclearMissile"],
        "IranSystemSpecialPowerShortcut": ["Iran_SejjilMissile", "Iran_ChemicalStrike", "Iran_BiologicalWeapon"],
        "BritainSystemSpecialPowerShortcut": ["BritainSpecialPowerTrident"],
        "FranceSystemSpecialPowerShortcut": ["FranceSpecialPowerM51"],
        "India_SystemSpecialPowerShortcut": ["IndiaSpecialPowerAgniV"],
        "Pakistan_SystemSpecialPowerShortcut": ["PakistanSpecialPowerShaheenIII"],
        "JapanSystemSpecialPowerShortcut": ["Japan_Type12Missile", "Japan_ChemicalDefense"],
        "GermanySystemSpecialPowerShortcut": ["Germany_TaurusMissile", "Germany_ChemicalStrike"],
        "SouthKoreaSystemSpecialPowerShortcut": ["SouthKorea_HyunmooMissile", "SouthKorea_BiologicalWeapon"],
        "TurkeySystemSpecialPowerShortcut": ["Turkey_BoraMissile", "Turkey_ChemicalStrike"],
        "ItalySystemSpecialPowerShortcut": ["Italy_StormShadowMissile", "Italy_BiologicalWeapon"],
        "Egypt_SystemSpecialPowerShortcut": ["Egypt_ScudDMissile", "Egypt_ChemicalStrike"],
        "VietnamSystemSpecialPowerShortcut": ["Vietnam_K300Missile", "Vietnam_BiologicalWeapon"],
        "SaudiArabia_SystemSpecialPowerShortcut": ["SaudiArabia_AbabilMissile", "SaudiArabia_ChemicalStrike"],
        "UAE_SystemSpecialPowerShortcut": ["UAE_ThunderMissile", "UAE_BiologicalWeapon"],
        "UkraineSystemSpecialPowerShortcut": ["Ukraine_Hrim2Missile", "Ukraine_ChemicalStrike"],
        "Syria_SystemSpecialPowerShortcut": ["Syria_ScudMissile", "Syria_ChemicalStrike"],
        "Libya_SystemSpecialPowerShortcut": ["Libya_ScudBMissile", "Libya_BiologicalWeapon"],
        "SouthAfrica_SystemSpecialPowerShortcut": ["SouthAfrica_RaptorMissile", "SouthAfrica_ChemicalStrike"],
        "SwedenSystemSpecialPowerShortcut": ["Sweden_RBS15Missile", "Sweden_BiologicalDefense"],
    }
    for obj, need in system_expect.items():
        hit = last_object(data, obj)
        if not hit:
            errors.append(f"missing Object {obj}")
            print("MISS OBJ", obj)
            continue
        _file, blk = hit
        granted = re.findall(r"(?m)^\s*SpecialPowerTemplate\s*=\s*(\S+)", blk)
        cs_name = field(blk, "CommandSet")
        if cs_name and cs_name not in commandsets:
            errors.append(f"{obj} CommandSet {cs_name} missing")
        for power in need:
            if power not in granted:
                errors.append(f"{obj} missing OCL grant {power}")
            kind = (
                "nuke"
                if power in NUCLEAR_POWERS
                else "bio"
                if "Biological" in power
                else "chem"
                if "Chemical" in power
                else "missile"
            )
            if power in granted:
                # verify matching OCL near that template
                if OCL[kind] not in blk:
                    errors.append(f"{obj} missing OCL {OCL[kind]} for {power}")
        print(("OK" if all(p in granted for p in need) else "FAIL"), obj, "grants", granted, "cs", cs_name)

    print("\n=== OCL existence ===")
    for ocl in OCL.values():
        if ocl not in ocls:
            errors.append(f"missing ObjectCreationList {ocl}")
        print(("OK" if ocl in ocls else "MISS"), ocl)

    print("\n=== CSF required ===")
    required_csf = [
        "CONTROLBAR:BritainTrident",
        "CONTROLBAR:FranceM51",
        "CONTROLBAR:IndiaAgniV",
        "CONTROLBAR:PakistanShaheenIII",
        "CONTROLBAR:KhorramshahrBallisticMissile",
        "CONTROLBAR:JapanType12Missile",
        "CONTROLBAR:GermanyTaurusMissile",
        "CONTROLBAR:SouthKoreaHyunmooMissile",
        "CONTROLBAR:TurkeyBoraMissile",
        "CONTROLBAR:ItalyStormShadowMissile",
        "CONTROLBAR:EgyptScudDMissile",
        "CONTROLBAR:VietnamK300Missile",
        "CONTROLBAR:SaudiAbabilMissile",
        "CONTROLBAR:UAEThunderMissile",
        "CONTROLBAR:UkraineHrim2Missile",
        "CONTROLBAR:SyriaScudMissile",
        "CONTROLBAR:LibyaScudBMissile",
        "CONTROLBAR:SouthAfricaRaptorMissile",
        "CONTROLBAR:SwedenRBS15Missile",
        "CONTROLBAR:SwedenBiologicalDefense",
        "CONTROLBAR:IranChemicalStrike",
        "CONTROLBAR:IranBiologicalWeapon",
    ]
    for lab in required_csf:
        if lab not in csf:
            errors.append(f"CSF missing {lab}")
        else:
            print("CSF", lab, "=", csf[lab])

    # non-nuclear shortcuts must not include LGM-30
    nato = commandset_buttons(commandsets, "SpecialPowerShortcutNATO")
    if "Command_LaunchLgm30FromShortcut" in commandset_buttons(commandsets, "SpecialPowerShortcutGermanyCommandSet"):
        errors.append("Germany still has LGM-30")
    print("NATO bar still", nato)

    print("\n=== RESULT ===")
    if errors:
        print("AUDIT_FAIL", len(errors))
        for e in errors:
            print(" -", e)
        return 1
    print("AUDIT_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
