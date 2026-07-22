#!/usr/bin/env python3
"""Compatibility audit: Turkey faction selection references resolve in patch.

Exit 0 = OK. Exit 1 = missing references that block MP/skirmish play.
Does not modify Specter archives.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # patch/
INI = ROOT / "Data" / "INI"
ART = ROOT / "Art" / "Textures"
ENG = ROOT / "Data" / "English"

errors: list[str] = []
warnings: list[str] = []


def collect(keyword: str) -> set[str]:
    found: set[str] = set()
    rx = re.compile(rf"^{keyword}\s+(\S+)\s*$", re.M)
    for p in INI.rglob("*.ini"):
        found.update(rx.findall(p.read_text(errors="replace")))
    return found


def main() -> int:
    objects = collect("Object")
    command_sets = collect("CommandSet")
    sciences = collect("Science")
    player_templates = collect("PlayerTemplate")
    mapped = set()
    for p in (INI / "MappedImages").rglob("*.INI"):
        mapped.update(re.findall(r"^MappedImage\s+(\S+)\s*$", p.read_text(errors="replace"), re.M))
    for p in (INI / "MappedImages").rglob("*.ini"):
        mapped.update(re.findall(r"^MappedImage\s+(\S+)\s*$", p.read_text(errors="replace"), re.M))

    pt = (INI / "PlayerTemplate_SpecterPatch.ini").read_text(errors="replace")
    m = re.search(r"PlayerTemplate FactionTurkey\n(.*?)(?:^PlayerTemplate |\Z)", pt, re.M | re.S)
    if not m:
        errors.append("MISSING PlayerTemplate FactionTurkey")
        print_report()
        return 1
    block = m.group(1)

    def field(name: str) -> str | None:
        fm = re.search(rf"^\s*{name}\s*=\s*(\S+)", block, re.M)
        return fm.group(1) if fm else None

    if field("PlayableSide") != "Yes":
        errors.append("FactionTurkey PlayableSide must be Yes for MP/skirmish")
    if field("Side") != "Turkey":
        errors.append("FactionTurkey Side must be Turkey")

    for key, pool, label in [
        ("StartingBuilding", objects, "Object"),
        ("StartingUnit0", objects, "Object"),
        ("StartingUnit1", objects, "Object"),
        ("PurchaseScienceCommandSetRank1", command_sets, "CommandSet"),
        ("PurchaseScienceCommandSetRank3", command_sets, "CommandSet"),
        ("PurchaseScienceCommandSetRank8", command_sets, "CommandSet"),
        ("SpecialPowerShortcutCommandSet", command_sets, "CommandSet"),
        ("IntrinsicSciences", sciences, "Science"),
    ]:
        val = field(key)
        if not val:
            errors.append(f"MISSING field {key}")
            continue
        # IntrinsicSciences may be multi
        for part in val.split():
            if part not in pool:
                errors.append(f"MISSING {label} {part} (from {key})")

    for img_field in ("FlagWaterMark", "EnabledImage", "SideIconImage", "GeneralImage", "LoadScreenImage"):
        val = field(img_field)
        if not val:
            warnings.append(f"optional field missing: {img_field}")
            continue
        if val in (
            "Turkey_Flag",
            "WatermarkTurkey",
            "GameinfoTurkey",
            "Turkey_Logo",
            "SSObserverTurkey",
        ):
            if val not in mapped:
                errors.append(f"MISSING MappedImage {val} ({img_field})")

    textures = {
        "WatermarkTurkey.tga",
        "GameinfoTurkey.tga",
        "Turkey_Logo.tga",
        "SSObserverTurkey.tga",
        "Turkey_Flag.tga",
    }
    for tex in textures:
        if not (ART / tex).exists():
            errors.append(f"MISSING texture Art/Textures/{tex}")

    # ControlBarScheme Side=Turkey
    cbs = (INI / "ControlBarScheme_SpecterPatch.ini").read_text(errors="replace")
    if not re.search(r"ControlBarScheme\s+Turkey8x6", cbs):
        errors.append("MISSING ControlBarScheme Turkey8x6")
    if "Side Turkey" not in cbs:
        errors.append("ControlBarScheme Turkey8x6 missing Side Turkey")

    # Picker strings in Turkey_FactionStrings.txt
    strings = (ENG / "Turkey_FactionStrings.txt").read_text(errors="replace")
    for key in (
        "INI:FactionTurkey",
        "Side:Turkey",
        "FACTION:Turkey",
        "SCIENCE:Turkey",
        "TOOLTIP:BioStrategyLong_Turkey",
        "GUI:BioFeatures_Turkey",
    ):
        if key not in strings:
            errors.append(f"MISSING string key {key} in Turkey_FactionStrings.txt")

    if "FactionTurkey" not in player_templates:
        errors.append("FactionTurkey not collected as PlayerTemplate")

    # FactionTurkey system object
    if "FactionTurkey" not in objects:
        warnings.append("Object FactionTurkey not found (optional system marker)")

    print_report()
    return 1 if errors else 0


def print_report() -> None:
    print("Turkey faction selection audit")
    for e in errors:
        print(f"  ERROR: {e}")
    for w in warnings:
        print(f"  WARN: {w}")
    if not errors:
        print("  PASS — Turkey MP/skirmish selection references resolve")


if __name__ == "__main__":
    # allow print_report to see lists
    sys.exit(main())
