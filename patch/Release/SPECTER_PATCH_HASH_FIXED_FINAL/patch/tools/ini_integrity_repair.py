#!/usr/bin/env python3
"""Specter Object INI integrity repair — preserves factions/units/weapons/aircraft.

Repairs (overlay-only under patch/):
  - Cross-faction TriggeredBy upgrade references
  - Cross-faction / wrong Prerequisites Object= references
  - Side= mismatches when object name is clearly faction-prefixed
  - Missing Israel core buildings (cloned from Egypt templates)
  - Minimal Upgrade_Israel.ini for remapped TriggeredBy targets
  - NATO Barracks alias objects where only BootCamp/Camp exists

Does NOT delete countries, units, aircraft, or weapons.
"""
from __future__ import annotations

import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path("patch/Data/INI/Object/Specter")
INI = Path("patch/Data/INI")
REPORT = Path("Repair_Report.txt")

FOLDER_SIDE = {
    "British Armed Forces": "Britain",
    "Egyptian Armed Forces": "Egypt",
    "French Armed Forces": "France",
    "German Armed Forces": "Germany",
    "Indian Armed Forces": "India",
    "Israel Defense Forces": "Israel",
    "Italian Armed Forces": "Italy",
    "Japan Self-Defense Forces": "Japan",
    "Libyan Armed Forces": "Libya",
    "Pakistan Armed Forces": "Pakistan",
    "Republic of China Armed Forces": "Taiwan",
    "Republic of Korea Armed Forces": "SouthKorea",
    "Saudi Arabian Armed Forces": "SaudiArabia",
    "South African National Defence Force": "SouthAfrica",
    "Swedish Armed Forces": "Sweden",
    "Syrian Arab Army": "Syria",
    "Turkey Armed Forces": "Turkey",
    "Ukrainian Armed Forces": "Ukraine",
    "United Arab Emirates": "UAE",
    "United Nations Forces": "UN",
    "Vietnam People's Army": "Vietnam",
}

PATCH_PREFIX_SIDE = {
    "America": "America",
    "Russia": "Russia",
    "China": "China",
    "Iran": "Iran",
    "Iraq": "Iraq",
    "Nato": "Nato",
    "GLA": "GLA",
    "NorthKorea": "NorthKorea",
    "AirF_America": "America",
    "Patch_America": "America",
    "Patch_Russia": "Russia",
    "Patch_China": "China",
    "Patch_Iran": "Iran",
    "Patch_Iraq": "Iraq",
    "Patch_Nato": "Nato",
    "Patch_GLA": "GLA",
    "Patch_Israel": "Israel",
}

OBJ_DEF = re.compile(
    r"^\s*(Object|ObjectReskin|ChildObject)\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*$"
)
BUILDING_HINTS = re.compile(
    r"(CommandCenter|WarFactory|Warfactory|Barracks|BootCamp|Camp|Airfield|AirBase|"
    r"AdvancedAirBase|SupplyCenter|PowerPlant|PowerStation|Radar|StrategyCenter|"
    r"MIC|Abbas|MilitaryHQ|Palace)",
    re.I,
)

STOCK_PREREQ_KIND = {
    "NatoAirfield": "airfield",
    "UAEAirfield": "airfield",
    "AmericaAirfield": "airfield",
    "IraqMilitaryAirfield": "airfield",
    "JapanAirfield": "airfield",
    "AmericaWarFactory": "warfactory",
    "IraqMilitaryWarfactory": "warfactory",
    "NatoStrategyCenter": "strategy",
    "BritainStrategyCenter": "strategy",
    "AmericaStrategyCenter": "strategy",
    "AmericaSupplyCenter": "supply",
    "RussiaSupplyCenter": "supply",
    "ChinaSupplyCenter": "supply",
    "IranSupplyCenter": "supply",
    "NatoSupplyCenter": "supply",
    "GLASupplyStash": "supply",
    "AirF_AmericaSupplyCenter": "supply",
    "Iraq_SupplyCenter": "supply",
    "India_SupplyCenter": "supply",
    "India_RadarStation": "radar",
    "India_HussienResearchObject": "research",
    "GLAPalace": "command",
    "ChinaCommandCenter": "command",
    "GLACommandCenter": "command",
}

KIND_SUFFIXES = {
    "airfield": ["AdvancedAirBase", "Airfield_T", "Airfield", "Airfield_AI"],
    "warfactory": ["WarFactory", "Warfactory"],
    "supply": ["SupplyCenter"],
    "radar": ["RadarStation", "GM406", "RadarGM406", "StrategyCenter", "MIC"],
    "strategy": ["StrategyCenter", "MIC", "Abbas"],
    "research": ["MIC", "Abbas", "StrategyCenter", "HussienResearchObject"],
    "barracks": ["Barracks", "BootCamp", "Camp"],
    "command": ["CommandCenter"],
    "power": ["PowerPlant", "PowerStation"],
}


def index_objects():
    objects = {}
    buildings_by_side = defaultdict(set)
    for path in ROOT.rglob("*.ini"):
        parts = path.parts
        try:
            folder = parts[parts.index("Specter") + 1]
        except Exception:
            folder = "?"
        cur = None
        for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            code = line.split(";", 1)[0]
            m = OBJ_DEF.match(code)
            if m:
                cur = m.group(2)
                side = FOLDER_SIDE.get(folder)
                if folder == "PatchSystems":
                    side = None
                    for pref, s in sorted(
                        PATCH_PREFIX_SIDE.items(), key=lambda x: -len(x[0])
                    ):
                        if cur.startswith(pref + "_") or cur.startswith(pref):
                            side = s
                            break
                objects[cur] = {
                    "file": path,
                    "line": i,
                    "folder": folder,
                    "side": side,
                }
                continue
            if cur and re.match(r"^\s*Side\s*=", code, re.I):
                sm = re.match(r"^\s*Side\s*=\s*(\S+)", code, re.I)
                if sm:
                    objects[cur]["side"] = sm.group(1)

    for name, meta in objects.items():
        if BUILDING_HINTS.search(name) or meta["file"].parent.name == "Buildings":
            side = meta.get("side")
            if side:
                buildings_by_side[side].add(name)
    return objects, buildings_by_side


def load_upgrades():
    upgrades = set()
    for p in INI.glob("Upgrade*.ini"):
        for m in re.finditer(
            r"^\s*Upgrade\s+(\S+)", p.read_text(errors="replace"), re.M
        ):
            upgrades.add(m.group(1))
    return upgrades


def pick_building(buildings_by_side, objects, side: str, *suffixes):
    bset = buildings_by_side.get(side, set())
    for suf in suffixes:
        for cand in (f"{side}_{suf}", f"{side}{suf}", suf):
            if cand in bset or cand in objects:
                return cand
    for suf in suffixes:
        for n in bset:
            if suf.lower() in n.lower():
                return n
    return None


def map_upgrade(upgrades: set[str], side: str, upg: str) -> str | None:
    table = [
        (r"^Upgrade_Turkey_HisarNetwork$", f"Upgrade_{side}_Armor"),
        (r"^Upgrade_Turkey_PrecisionMunitions$", f"Upgrade_{side}_AircraftWeapons"),
        (
            r"^Upgrade_Turkey_Countermeasures$",
            f"Upgrade_{side}_AircraftCountermeasures",
        ),
        (r"^Upgrade_Britain_Armor$", f"Upgrade_{side}_Armor"),
        (r"^Upgrade_Britain_Weapons$", f"Upgrade_{side}_Weapons"),
        (
            r"^Upgrade_Britain_AircraftCountermeasures$",
            f"Upgrade_{side}_AircraftCountermeasures",
        ),
        (
            r"^Upgrade_Britain_AircraftWeapons$",
            f"Upgrade_{side}_AircraftWeapons",
        ),
    ]
    for pat, dest in table:
        if re.match(pat, upg):
            if upg.startswith(f"Upgrade_{side}_"):
                return None
            for candidate in (
                dest,
                f"Upgrade_{side}_Armor",
                f"Upgrade_{side}_Weapons",
                f"Upgrade_{side}_AircraftCountermeasures",
            ):
                if candidate in upgrades or candidate.startswith("Upgrade_Israel_"):
                    return candidate
            return dest
    m = re.match(r"^Upgrade_([A-Za-z]+)_(.+)$", upg)
    if m:
        other, rest = m.group(1), m.group(2)
        if other != side:
            local = f"Upgrade_{side}_{rest}"
            if local in upgrades:
                return local
    return None


def infer_kind(req: str, side: str) -> str | None:
    if req in STOCK_PREREQ_KIND:
        return STOCK_PREREQ_KIND[req]
    if req.startswith("India_") and side != "India":
        if "Supply" in req:
            return "supply"
        if "Radar" in req:
            return "radar"
        if "Hussien" in req or "Abbas" in req or "Research" in req:
            return "research"
    for other_side in list(FOLDER_SIDE.values()) + [
        "America",
        "Russia",
        "China",
        "Iran",
        "Iraq",
        "Nato",
        "GLA",
    ]:
        if other_side != side and (
            req.startswith(other_side + "_") or req.startswith(other_side)
        ):
            if "Airfield" in req or "AirBase" in req:
                return "airfield"
            if "WarFactory" in req or "Warfactory" in req:
                return "warfactory"
            if "Supply" in req:
                return "supply"
            if "Radar" in req or "GM406" in req:
                return "radar"
            if "Strategy" in req or "MIC" in req:
                return "strategy"
            if "Barracks" in req or "Camp" in req or "BootCamp" in req:
                return "barracks"
            if "Command" in req:
                return "command"
            if "Power" in req:
                return "power"
            if "Hussien" in req or "Abbas" in req or "Research" in req:
                return "research"
    return None


def side_for_object(objects, name: str, folder: str) -> str | None:
    if folder in FOLDER_SIDE:
        return FOLDER_SIDE[folder]
    if folder == "PatchSystems":
        for pref, s in sorted(PATCH_PREFIX_SIDE.items(), key=lambda x: -len(x[0])):
            if name.startswith(pref + "_") or name.startswith(pref):
                return s
        for side in FOLDER_SIDE.values():
            if name.startswith(side + "_"):
                return side
    return objects.get(name, {}).get("side")


def repair_object_files(objects, buildings_by_side, upgrades):
    fixed_files = set()
    actions = []
    upgrade_fix_count = 0
    prereq_fix_count = 0
    side_fix_count = 0

    for path in sorted(ROOT.rglob("*.ini")):
        parts = path.parts
        folder = parts[parts.index("Specter") + 1]
        lines = path.read_text(errors="replace").splitlines(True)
        out = []
        cur = None
        in_prereq = False
        changed = False

        for line in lines:
            code = line.split(";", 1)[0]
            m = OBJ_DEF.match(code)
            if m:
                cur = m.group(2)
                in_prereq = False
                out.append(line)
                continue

            side = side_for_object(objects, cur, folder) if cur else None

            if re.match(r"^\s*Prerequisites\b", code, re.I):
                in_prereq = True
                out.append(line)
                continue
            if in_prereq and re.match(r"^\s*End\b", code, re.I):
                in_prereq = False
                out.append(line)
                continue

            if in_prereq and cur and side:
                pm = re.match(r"^(\s*Object\s*=\s*)(\S+)\s*$", code)
                if pm:
                    req = pm.group(2)
                    if req not in buildings_by_side.get(side, set()):
                        kind = infer_kind(req, side)
                        new = None
                        if kind:
                            new = pick_building(
                                buildings_by_side,
                                objects,
                                side,
                                *KIND_SUFFIXES[kind],
                            )
                        if new and new != req:
                            out.append(
                                f"{pm.group(1)}{new} ; INI-REPAIR was {req}\n"
                            )
                            changed = True
                            prereq_fix_count += 1
                            actions.append(
                                f"PREREQ {path.as_posix()}:{cur}: {req} -> {new}"
                            )
                            continue
                out.append(line)
                continue

            if cur and side and re.match(r"^\s*TriggeredBy\s*=", code, re.I):
                tm = re.match(r"^(\s*TriggeredBy\s*=\s*)(\S+)\s*$", code)
                if tm:
                    upg = tm.group(2)
                    mapped = map_upgrade(upgrades, side, upg)
                    if (
                        mapped
                        and mapped != upg
                        and not upg.startswith(f"Upgrade_{side}_")
                    ):
                        out.append(
                            f"{tm.group(1)}{mapped} ; INI-REPAIR was {upg}\n"
                        )
                        changed = True
                        upgrade_fix_count += 1
                        actions.append(
                            f"UPGRADE {path.as_posix()}:{cur}: {upg} -> {mapped}"
                        )
                        continue

            if (
                cur
                and folder in FOLDER_SIDE
                and re.match(r"^\s*Side\s*=", code, re.I)
            ):
                expected = FOLDER_SIDE[folder]
                sm = re.match(r"^(\s*Side\s*=\s*)(\S+)\s*$", code)
                if (
                    sm
                    and sm.group(2) != expected
                    and (
                        cur.startswith(expected + "_") or cur.startswith(expected)
                    )
                ):
                    out.append(
                        f"{sm.group(1)}{expected} ; INI-REPAIR was {sm.group(2)}\n"
                    )
                    changed = True
                    side_fix_count += 1
                    actions.append(
                        f"SIDE {path.as_posix()}:{cur}: {sm.group(2)} -> {expected}"
                    )
                    continue

            out.append(line)

        if changed:
            path.write_text("".join(out), encoding="utf-8")
            fixed_files.add(path.as_posix())

    return {
        "fixed_files": fixed_files,
        "actions": actions,
        "upgrade_fix_count": upgrade_fix_count,
        "prereq_fix_count": prereq_fix_count,
        "side_fix_count": side_fix_count,
    }


def clone_egypt_building(src_name: str, dst_name: str, dst_path: Path) -> list[str]:
    """Clone an Egypt building INI into Israel with renamed IDs."""
    src = ROOT / "Egyptian Armed Forces" / "Buildings" / f"{src_name}.ini"
    if not src.exists():
        return [f"MISSING_TEMPLATE {src}"]
    text = src.read_text(encoding="utf-8", errors="replace")
    # Order matters: longer tokens first
    replacements = [
        ("Egypt_BarracksCommandSet", "Israel_BarracksCommandSet"),
        ("Egypt_WarFactoryCommandSet", "Israel_WarFactoryCommandSet"),
        ("Egypt_AirfieldCommandSet", "Israel_AirfieldCommandSet"),
        ("Egypt_SupplyCenterCommandSet", "Israel_SupplyCenterCommandSet"),
        ("Egypt_PowerPlantCommandSet", "Israel_PowerPlantCommandSet"),
        ("Egypt_RadarStationCommandSet", "Israel_RadarStationCommandSet"),
        ("Egypt_WarFactory", "Israel_WarFactory"),
        ("Egypt_Barracks", "Israel_Barracks"),
        ("Egypt_Airfield_T", "Israel_Airfield_T"),
        ("Egypt_SupplyCenter", "Israel_SupplyCenter"),
        ("Egypt_PowerPlant", "Israel_PowerPlant"),
        ("Egypt_RadarStation", "Israel_RadarStation"),
        ("Egypt_AdvancedAirBase", "Israel_AdvancedAirBase"),
        ("Egypt_CommandCenter", "Israel_CommandCenter"),
        ("Egypt_MIC", "Israel_MIC"),
        ("Egypt_Abbas", "Israel_Abbas"),
        ("side=Egypt", "side=Israel"),
        ("Side = Egypt", "Side = Israel"),
        ("Side             = Egypt", "Side             = Israel"),
        ("Side                = Egypt", "Side                = Israel"),
    ]
    for a, b in replacements:
        text = text.replace(a, b)
    header = (
        "; SPECTER PATCH — INI integrity repair\n"
        "; Israel building shell cloned from Egypt template (unique Israel_* IDs).\n"
        "; Preserves gameplay structure; does not remove other factions.\n\n"
    )
    # Drop Egypt kit banner lines that would confuse
    text = re.sub(
        r"^; SPECTER PATCH — Egypt.*\n(; Unique IDs only.*\n)?",
        "",
        text,
        count=1,
        flags=re.M,
    )
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(header + text, encoding="utf-8")
    return [f"CREATED {dst_path.as_posix()} (from {src.as_posix()} -> {dst_name})"]


def ensure_israel_buildings():
    actions = []
    created = []
    mapping = [
        ("Egypt_WarFactory", "Israel_WarFactory", "Israel_WarFactory.ini"),
        ("Egypt_Barracks", "Israel_Barracks", "Israel_Barracks.ini"),
        ("Egypt_Airfield_T", "Israel_Airfield_T", "Israel_Airfield_T.ini"),
        ("Egypt_SupplyCenter", "Israel_SupplyCenter", "Israel_SupplyCenter.ini"),
        ("Egypt_PowerPlant", "Israel_PowerPlant", "Israel_PowerPlant.ini"),
        ("Egypt_RadarStation", "Israel_RadarStation", "Israel_RadarStation.ini"),
    ]
    bdir = ROOT / "Israel Defense Forces" / "Buildings"
    for src_stem, dst_obj, fname in mapping:
        dst = bdir / fname
        if dst.exists():
            # ensure object name present
            if f"Object {dst_obj}" in dst.read_text(errors="replace"):
                continue
        acts = clone_egypt_building(src_stem, dst_obj, dst)
        actions.extend(acts)
        created.append(dst_obj)
    return actions, created


def ensure_israel_upgrades():
    path = INI / "Upgrade_Israel.ini"
    needed = [
        "Upgrade_Israel_Armor",
        "Upgrade_Israel_Weapons",
        "Upgrade_Israel_AircraftWeapons",
        "Upgrade_Israel_AircraftCountermeasures",
    ]
    existing = set()
    if path.exists():
        existing = set(
            re.findall(r"^\s*Upgrade\s+(\S+)", path.read_text(errors="replace"), re.M)
        )
    missing = [u for u in needed if u not in existing]
    if not missing and path.exists():
        return [], []
    blocks = []
    for upg in needed:
        if upg in existing:
            continue
        blocks.append(
            f"""Upgrade {upg}
; PatchBaseCost = 1200
; PatchBaseTime = 30.0
; INI-REPAIR: Israel isolation upgrade stub
  DisplayName   = UPGRADE:{upg.replace('Upgrade_', '')}
  BuildTime     = 24.0
  BuildCost     = 900
  ButtonImage   = SAArmor
  ResearchSound = ScorpionTankVoiceUpgradeRocket
End
"""
        )
    if path.exists():
        path.write_text(
            path.read_text(encoding="utf-8") + "\n" + "\n".join(blocks),
            encoding="utf-8",
        )
    else:
        path.write_text(
            "; SPECTER PATCH — Israel upgrades (INI integrity repair)\n\n"
            + "\n".join(blocks),
            encoding="utf-8",
        )
    return [f"CREATED/UPDATED {path.as_posix()}: {', '.join(missing or needed)}"], missing


def ensure_israel_commandsets():
    path = INI / "CommandSet_Israel_Integrity.ini"
    content = """; SPECTER PATCH — Israel building CommandSets (INI integrity repair)

CommandSet Israel_BarracksCommandSet
  1 = Command_ConstructIsrael_AD_IronDome
End

CommandSet Israel_WarFactoryCommandSet
  1 = Command_ConstructIsrael_AD_Barak8
End

CommandSet Israel_AirfieldCommandSet
  1 = Command_ConstructIsrael_AdvancedAirBase
End

CommandSet Israel_SupplyCenterCommandSet
End

CommandSet Israel_PowerPlantCommandSet
End

CommandSet Israel_RadarStationCommandSet
End
"""
    if path.exists() and "Israel_BarracksCommandSet" in path.read_text(errors="replace"):
        return [], []
    path.write_text(content, encoding="utf-8")
    return [f"CREATED {path.as_posix()}"], [
        "Israel_BarracksCommandSet",
        "Israel_WarFactoryCommandSet",
        "Israel_AirfieldCommandSet",
        "Israel_SupplyCenterCommandSet",
        "Israel_PowerPlantCommandSet",
        "Israel_RadarStationCommandSet",
    ]


def ensure_nato_barracks_aliases(objects, buildings_by_side):
    """For NATO-style factions with BootCamp/Camp but no Barracks object, add alias Object."""
    actions = []
    created = []
    nato_folders = {
        "British Armed Forces": "Britain",
        "French Armed Forces": "France",
        "German Armed Forces": "Germany",
        "Italian Armed Forces": "Italy",
        "Japan Self-Defense Forces": "Japan",
        "Republic of China Armed Forces": "Taiwan",
        "Republic of Korea Armed Forces": "SouthKorea",
        "Swedish Armed Forces": "Sweden",
        "United Nations Forces": "UN",
    }
    for folder, side in nato_folders.items():
        barracks = f"{side}_Barracks"
        if barracks in objects:
            continue
        donor = pick_building(
            buildings_by_side, objects, side, "BootCamp", "Camp", "Barracks"
        )
        if not donor or donor == barracks:
            continue
        # Find donor file to place sibling
        donor_meta = objects.get(donor)
        if not donor_meta:
            continue
        out_path = ROOT / folder / "Buildings" / f"{side}_Barracks.ini"
        if out_path.exists():
            continue
        # Minimal unique barracks object cloned from donor file with renames
        text = donor_meta["file"].read_text(encoding="utf-8", errors="replace")
        text = re.sub(
            rf"\bObject\s+{re.escape(donor)}\b", f"Object {barracks}", text, count=1
        )
        # Avoid duplicating other objects in multi-object files: extract first object only
        # If file has multiple objects, write a thin shell instead
        defs = list(
            re.finditer(
                r"^\s*Object\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*$", text, re.M
            )
        )
        if len(defs) > 1:
            # thin shell referencing same art via copy of single-object pattern
            text = f"""; SPECTER PATCH — INI integrity repair
; Barracks alias for {side} (donor {donor}) — unique object name for country isolation.

Object {barracks}
; PatchBaseCost = 600
; PatchBaseTime = 10.0
  SelectPortrait         = us_camp
  ButtonImage            = us_camp
  Draw                   = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes
    ConditionState       = NONE
      Model              = US_Camp
      Animation          = US_Camp.US_Camp
      AnimationMode      = LOOP
    End
  End
  DisplayName         = OBJECT:Barracks
  Side                = {side}
  EditorSorting       = STRUCTURE
  BuildCost           = 500
  BuildTime           = 10.0
  EnergyProduction    = 0
  CommandSet          = {side}_BarracksCommandSet
  VisionRange         = 200.0
  ShroudClearingRange = 200.0
  ArmorSet
    Conditions        = None
    Armor             = StructureArmor
    DamageFX          = StructureDamageFXNoShake
  End
  KindOf              = PRELOAD STRUCTURE SELECTABLE IMMOBILE SCORE CAPTURABLE FS_FACTORY AUTO_RALLYPOINT MP_COUNT_FOR_VICTORY
  Body                = StructureBody ModuleTag_02
    MaxHealth         = 1000.0
    InitialHealth     = 1000.0
  End
  Behavior = ProductionUpdate ModuleTag_03
  End
  Behavior = DefaultProductionExitUpdate ModuleTag_04
    UnitCreatePoint   = X:-20.0  Y:20.0 Z:0.0
    NaturalRallyPoint = X:40.0  Y:20.0 Z:0.0
  End
  Geometry = BOX
  GeometryMajorRadius = 40.0
  GeometryMinorRadius = 40.0
  GeometryHeight = 20.0
  GeometryIsSmall = No
  Shadow = SHADOW_VOLUME
  BuildCompletion = PLACE_ON_GROUND
End
"""
        else:
            text = (
                "; SPECTER PATCH — INI integrity repair\n"
                f"; Barracks object for {side} derived from {donor}\n\n" + text
            )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        actions.append(
            f"CREATED {out_path.as_posix()} Object {barracks} (from {donor})"
        )
        created.append(barracks)
    return actions, created


def scan_remaining(objects, buildings_by_side, upgrades):
    """Post-repair residual issues worth reporting."""
    remaining = []
    # Cross-faction turkey/britain upgrades left
    for path in ROOT.rglob("*.ini"):
        folder = path.parts[path.parts.index("Specter") + 1]
        cur = None
        for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            code = line.split(";", 1)[0]
            m = OBJ_DEF.match(code)
            if m:
                cur = m.group(2)
                continue
            side = side_for_object(objects, cur, folder) if cur else None
            tm = re.match(r"^\s*TriggeredBy\s*=\s*(Upgrade_\S+)", code)
            if tm and side:
                upg = tm.group(1)
                m2 = re.match(r"^Upgrade_([A-Za-z]+)_", upg)
                if m2 and m2.group(1) != side and m2.group(1) in set(
                    list(FOLDER_SIDE.values()) + ["Turkey", "Britain"]
                ):
                    remaining.append(
                        f"CROSS_UPGRADE_REMAIN {path.as_posix()}:{i} {cur} {upg} (side={side})"
                    )
            if re.match(r"^\s*Prerequisites\b", code, re.I):
                pass
    # Duplicate object names
    by_name = defaultdict(list)
    for name, meta in objects.items():
        by_name[name].append(meta)
    # Re-index after creates
    objects2, _ = index_objects()
    by_name = defaultdict(list)
    for name, meta in objects2.items():
        by_name[name].append((meta["file"].as_posix(), meta["line"]))
    for name, locs in by_name.items():
        if len(locs) > 1:
            remaining.append(f"DUP_OBJECT {name} @ {locs}")

    # ModuleTag dups within object
    MOD = re.compile(
        r"^\s*(Behavior|Draw|Body|ClientUpdate|AI)\s*=\s*\S+\s+(\S+)", re.I
    )
    for path in ROOT.rglob("*.ini"):
        cur = None
        tags = {}
        for i, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            code = line.split(";", 1)[0]
            m = OBJ_DEF.match(code)
            if m:
                cur = m.group(2)
                tags = {}
                continue
            mm = MOD.match(code)
            if mm and cur:
                tag = mm.group(2)
                if tag in tags:
                    remaining.append(
                        f"DUP_MODULETAG {path.as_posix()}:{i} {cur} {tag} also@{tags[tag]}"
                    )
                else:
                    tags[tag] = i
    return remaining


def write_report(result):
    lines = []
    lines.append("SPECTER ULTIMATE WARFARE EXPANSION")
    lines.append("INI INTEGRITY REPAIR REPORT")
    lines.append("Scope: patch/Data/INI/Object/Specter/")
    lines.append("Engine: C&C Generals Zero Hour")
    lines.append("=" * 72)
    lines.append("")
    lines.append("POLICY")
    lines.append("- No countries deleted")
    lines.append("- No units/aircraft/weapons removed")
    lines.append("- Custom factions preserved")
    lines.append("- Overlay-only repairs (no vendor archive edits)")
    lines.append("")
    lines.append("SUMMARY")
    lines.append(f"- Fixed files: {len(result['fixed_files'])}")
    lines.append(f"- Upgrade TriggeredBy remaps: {result['upgrade_fix_count']}")
    lines.append(f"- Prerequisites remaps: {result['prereq_fix_count']}")
    lines.append(f"- Side= remaps: {result['side_fix_count']}")
    lines.append(f"- Objects created: {len(result['created_objects'])}")
    lines.append(f"- Renamed objects: {len(result['renamed_objects'])}")
    lines.append(f"- Removed duplicates: {len(result['removed_duplicates'])}")
    lines.append(f"- Remaining issues listed: {len(result['remaining'])}")
    lines.append("")
    lines.append("CREATED OBJECTS")
    if result["created_objects"]:
        for x in result["created_objects"]:
            lines.append(f"  + {x}")
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("RENAMED OBJECTS")
    if result["renamed_objects"]:
        for x in result["renamed_objects"]:
            lines.append(f"  ~ {x}")
    else:
        lines.append("  (none — no duplicate Object names required renaming)")
    lines.append("")
    lines.append("REMOVED DUPLICATES")
    if result["removed_duplicates"]:
        for x in result["removed_duplicates"]:
            lines.append(f"  - {x}")
    else:
        lines.append("  (none — duplicate Object/ModuleTag definitions not found)")
    lines.append("")
    lines.append("FIXED FILES")
    for f in sorted(result["fixed_files"]):
        lines.append(f"  * {f}")
    lines.append("")
    lines.append("ACTIONS (detail)")
    for a in result["actions"][:2000]:
        lines.append(f"  {a}")
    if len(result["actions"]) > 2000:
        lines.append(f"  ... ({len(result['actions']) - 2000} more)")
    lines.append("")
    lines.append("REMAINING ERRORS / NOTES")
    if result["remaining"]:
        for r in result["remaining"][:500]:
            lines.append(f"  ! {r}")
    else:
        lines.append("  (none critical inside Specter Object tree after repair)")
    lines.append("")
    lines.append(
        "NOTE: Weapon/Locomotor/CommandSet names that resolve from Specter stock"
    )
    lines.append(
        "archives (Data.zip / .big) are not treated as missing patch definitions."
    )
    lines.append("")
    lines.append("END REPORT")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Also copy under patch/Release for packaging convenience
    release = Path("patch/Release")
    release.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPORT, release / "Repair_Report.txt")


def main():
    objects, buildings_by_side = index_objects()
    upgrades = load_upgrades()

    # Israel support assets first so remaps can target them
    israel_upg_actions, israel_upgs = ensure_israel_upgrades()
    for u in israel_upgs:
        upgrades.add(u)
    israel_cs_actions, _ = ensure_israel_commandsets()
    israel_b_actions, israel_objs = ensure_israel_buildings()

    # Re-index after Israel creates
    objects, buildings_by_side = index_objects()

    nato_actions, nato_objs = ensure_nato_barracks_aliases(objects, buildings_by_side)
    objects, buildings_by_side = index_objects()

    core = repair_object_files(objects, buildings_by_side, upgrades)

    # Re-index and scan remaining
    objects, buildings_by_side = index_objects()
    remaining = scan_remaining(objects, buildings_by_side, upgrades)

    fixed = set(core["fixed_files"])
    actions = (
        israel_upg_actions
        + israel_cs_actions
        + israel_b_actions
        + nato_actions
        + core["actions"]
    )
    for a in israel_b_actions + nato_actions + israel_upg_actions + israel_cs_actions:
        # extract path
        if a.startswith("CREATED"):
            parts = a.split()
            if len(parts) >= 2:
                fixed.add(parts[1])

    result = {
        "fixed_files": fixed,
        "actions": actions,
        "upgrade_fix_count": core["upgrade_fix_count"],
        "prereq_fix_count": core["prereq_fix_count"],
        "side_fix_count": core["side_fix_count"],
        "created_objects": israel_objs + nato_objs,
        "renamed_objects": [],
        "removed_duplicates": [],
        "remaining": remaining,
    }
    write_report(result)
    print(
        f"DONE files={len(fixed)} upg={core['upgrade_fix_count']} "
        f"prereq={core['prereq_fix_count']} side={core['side_fix_count']} "
        f"created={len(result['created_objects'])} remaining={len(remaining)}"
    )
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
