#!/usr/bin/env python3
"""Pack UK-only air-force diversity + fire fix.

Base: europe_weapon_fire BIGs.
Does not rewrite France/Germany/Italy/Russia/China/USA CommandSets or objects.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_china_heavy_aircraft as ch
import pack_europe_airforce as eu
import pack_europe_weapon_fire as fire
import pack_france_airforce as fr

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
BASE_DATA = Path("/tmp/europe_weapon_fire/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/europe_weapon_fire/_SPEC_ART_ONE.big")

EUROPE_MARKER = b"\n; ===== SPECTER EUROPE AIRFORCE WEAPONS =====\n"
UK_SP_MARKER = b"\n; ===== SPECTER BRITAIN E7 SCAN =====\n"

PROTECT_SETS = [
    "FranceAirfieldCommandSet",
    "France_LargeAirBaseCommandSet",
    "France_HeavyAirBaseCommandSet",
    "FranceDozerCommandSet",
    "GermanyAirfieldCommandSet",
    "Germany_LargeAirBaseCommandSet",
    "Germany_HeavyAirBaseCommandSet",
    "GermanyDozerCommandSet",
    "ItalyAirfieldCommandSet",
    "Italy_LargeAirBaseCommandSet",
    "Italy_HeavyAirBaseCommandSet",
    "ItalyDozerCommandSet",
    "PLAAirfieldCommandSet",
    "China_LargeAirBaseCommandSet",
    "China_HeavyAirBaseCommandSet",
    "RussiaAirfieldCommandSet",
    "Russia_LargeAirBaseCommandSet",
    "Russia_HeavyAirBaseCommandSet",
]

FIGHTER_BTNS = [
    "Command_ConstructBritainJetF35B",
    "Command_ConstructBritainJetTyphoonFGR4",
    "Command_ConstructBritainJetTyphoonT3",
    "Command_ConstructBritainJetHarrierGR9",
    "Command_ConstructBritainJetTornadoGR4",
    "Command_ConstructBritainJetJaguarGR3",
    "Command_ConstructBritainJetSeaHarrierFA2",
    "Command_ConstructBritainJetPhantomFG1",
    "Command_ConstructBritainJetLightningF6",
    "Command_ConstructBritainJetHawk200",
    "Command_ConstructBritainHelicopterApache",
    "Command_ConstructBritainJetTornadoF3",
]

HEAVY_BTNS = [
    "Command_ConstructBritainJetA400M",
    "Command_ConstructBritainJetC17",
    "Command_ConstructBritainAircraftE7",
    "Command_ConstructBritainDroneMQ9",
    "Command_ConstructBritainBomberVulcan",
    "Command_ConstructBritainHelicopterChinook",
    "Command_ConstructBritainHelicopterMerlin",
    "Command_ConstructBritainHelicopterWildcat",
    "Command_ConstructBritainHelicopterPuma",
    "Command_ConstructBritainJetPhantomFGR2",
]

CSF_LABELS = {
    "OBJECT:BritainJetTornadoF3": "Tornado F3",
    "CONTROLBAR:ConstructBritainJetTornadoF3": "Tornado F3",
    "CONTROLBAR:ToolTipBritainJetTornadoF3": "British Tornado F3 long-range interceptor. Meteor, AMRAAM, ASRAAM.",
    "OBJECT:BritainJetPhantomFGR2": "Phantom FGR.2",
    "CONTROLBAR:ConstructBritainJetPhantomFGR2": "Phantom FGR.2",
    "CONTROLBAR:ToolTipBritainJetPhantomFGR2": "British Phantom FGR.2 heavy interceptor. AMRAAM, ASRAAM, cannon.",
    "CONTROLBAR:BritainE7Scan": "Radar Scan",
    "CONTROLBAR:ToolTipBritainE7Scan": "E-7 Wedgetail active radar scan. Reveals the targeted area.",
    "CONTROLBAR:ToolTipBritainJetTyphoonFGR4": "British Typhoon FGR4. Meteor, ASRAAM, Brimstone.",
    "CONTROLBAR:ToolTipBritainJetF35B": "British F-35B stealth fighter. AMRAAM, ASRAAM, SDB.",
    "CONTROLBAR:ToolTipBritainJetTornadoGR4": "British Tornado GR4 strike. Storm Shadow, Paveway, bombs.",
    "CONTROLBAR:ToolTipBritainJetJaguarGR3": "British Jaguar GR3. Paveway, bombs, rockets.",
    "CONTROLBAR:ToolTipBritainJetHarrierGR9": "British Harrier GR9 CAS. Paveway, Brimstone, ASRAAM.",
    "CONTROLBAR:ToolTipBritainJetSeaHarrierFA2": "British Sea Harrier FA2 naval fighter. AMRAAM and ASRAAM.",
    "CONTROLBAR:ToolTipBritainJetLightningF6": "British Lightning F6 interceptor. Meteor and ASRAAM.",
    "CONTROLBAR:ToolTipBritainJetHawk200": "British Hawk 200 light fighter. ASRAAM, light bombs, cannon.",
    "CONTROLBAR:ToolTipBritainJetTyphoonT3": "British Typhoon Tranche 3. Meteor and ASRAAM.",
    "CONTROLBAR:ToolTipBritainJetPhantomFG1": "British Phantom FG1. AMRAAM and ASRAAM.",
    "CONTROLBAR:ToolTipBritainAircraftE7": "British E-7 Wedgetail AWACS. Radar scan, no weapons.",
    "CONTROLBAR:ToolTipBritainHelicopterMerlin": "British Merlin support helicopter. Light anti-surface missiles.",
    "CONTROLBAR:ToolTipBritainHelicopterPuma": "British Puma transport helicopter. Light defensive gun.",
    "CONTROLBAR:ToolTipBritainHelicopterWildcat": "British Wildcat attack helicopter. Cannon, missiles, rockets.",
    "OBJECT:BritainJetHawk200": "Hawk 200",
    "OBJECT:BritainAircraftE7": "E-7 Wedgetail",
}

PORTRAIT_SRC = {
    "SPEC_BritainHawk200.tga": "Art/Textures/F16TB.tga",
    "SPEC_BritainSeaHarrierFA2.tga": "Art/Textures/US_FA18E.dds",
    "SPEC_BritainTyphoonT3.tga": "Art/Textures/NAT_EF2000T4.dds",
    "SPEC_BritainJaguarGR3.tga": "Art/Textures/LSFFRF1.dds",
    "SPEC_BritainTornadoF3.tga": "Art/Textures/LSFTornado.dds",
    "SPEC_BritainPhantomFGR2.tga": "Art/Textures/LSFJPF4.dds",
}

DONOR_NAMES = (
    "AVHawk",
    "KVE737",
    "E-737",
    "E737",
    "FA-18",
    "FA18",
    "F-16",
    "F16",
    "Mirage",
    "Rafale",
    "MiG",
    "Su-35",
    "B-52",
    "F-4",
)

W3D_TABLE = [
    ("Typhoon FGR4", "exact Typhoon", "LSFEUEF2000", "packed ART"),
    ("Typhoon T3", "closest distinct Typhoon", "NAT_EF2000T4", "packed ART"),
    ("F-35B", "exact F-35", "US_F35A", "packed ART"),
    ("Tornado GR4", "exact Tornado", "LSFTornado", "packed ART"),
    ("Tornado F3", "exact Tornado interceptor", "LSFTornado", "packed ART"),
    ("Jaguar GR3", "closest swept strike", "LSFFRF1", "packed ART"),
    ("Harrier GR9", "exact Harrier", "LSFAV8B", "packed ART"),
    ("Sea Harrier FA2", "closest naval fighter", "US_FA18E", "packed ART"),
    ("Lightning F6", "closest classic delta", "LSFMirage3", "packed ART"),
    ("Phantom FG1", "exact Phantom", "JPF4", "packed ART"),
    ("Phantom FGR.2", "exact Phantom", "JPF4", "packed ART"),
    ("Hawk 200", "closest compact light fighter", "LSFF16", "packed ART"),
    ("Vulcan", "B-52 class bomber (scale only)", "LSFUSAB52", "packed ART"),
    ("E-7 Wedgetail", "exact E-737", "KVE737", "packed ART"),
    ("Merlin", "keep NH90 visual", "LSFGENH90", "packed ART"),
    ("Puma", "keep Mi-17 visual", "LSFRUMi171", "packed ART"),
    ("Wildcat", "keep Lynx visual", "LSFLynxAHMK", "packed ART"),
]


def cs_block(name: str, buttons: list[str]) -> str:
    lines = [f"CommandSet {name}"]
    for i, btn in enumerate(buttons, 1):
        lines.append(f"  {i}  = {btn}")
    lines.append("  13 = Command_SetRallyPoint")
    lines.append("  14 = Command_Sell")
    lines.append("End")
    return "\n".join(lines) + "\n"


def collect_uk_overlay() -> dict[str, bytes]:
    overlay: dict[str, bytes] = {}
    keep = re.compile(r"^Britain(Jet|Aircraft|Drone|Bomber|Helicopter)")
    for sub in ("Airforce", "Rotary"):
        d = PATCH / "INI/Object/Specter/British Armed Forces" / sub
        for path in sorted(d.glob("*.ini")):
            if not keep.match(path.stem):
                continue
            dest = "Data\\INI\\" + path.relative_to(PATCH / "INI").as_posix().replace("/", "\\")
            overlay[dest] = ch.lf(path.read_bytes())
    overlay[r"Data\INI\Weapon_EuropeAirforce.ini"] = ch.lf(
        (PATCH / "INI/Weapon_EuropeAirforce.ini").read_bytes()
    )
    overlay[r"Data\INI\SpecialPower_BritainAirforce.ini"] = ch.lf(
        (PATCH / "INI/SpecialPower_BritainAirforce.ini").read_bytes()
    )
    overlay[r"Data\INI\CommandButton_EuropeAirforce.ini"] = ch.lf(
        (PATCH / "INI/CommandButton_EuropeAirforce.ini").read_bytes()
    )
    overlay[r"Data\INI\MappedImages\HandCreated\zEurope_AirbasePortrait_Images.INI"] = ch.lf(
        (PATCH / "INI/MappedImages/HandCreated/zEurope_AirbasePortrait_Images.INI").read_bytes()
    )
    return overlay


def extract_named_buttons(text: str, names: list[str]) -> str:
    parts = []
    for name in names:
        m = re.search(rf"CommandButton {re.escape(name)}\s*\n.*?^End\s*$", text, re.M | re.S)
        if not m:
            raise SystemExit(f"missing CommandButton {name}")
        parts.append(m.group(0).rstrip())
    return "\n\n".join(parts) + "\n"


def insert_before(cs_text: str, needle: str, payload: str) -> str:
    idx = cs_text.find(needle)
    if idx < 0:
        raise SystemExit(f"{needle} not found")
    return cs_text[:idx] + payload.rstrip() + "\n\n" + cs_text[idx:]


def strip_blocks(cs_text: str, names: list[str]) -> str:
    for name in names:
        cs_text, _n = re.subn(
            rf"CommandButton {re.escape(name)}\s*\n.*?^End\s*\n?",
            "",
            cs_text,
            count=1,
            flags=re.M | re.S,
        )
        cs_text, _n = re.subn(
            rf"CommandSet {re.escape(name)}\s*\n.*?^End\s*\n?",
            "",
            cs_text,
            count=1,
            flags=re.M | re.S,
        )
    return cs_text


def patch_csf(data: bytes) -> bytes:
    version, unk, lang, labels = ch.parse_csf(data)
    have_idx = {name: i for i, (_, name, _) in enumerate(labels)}
    added = updated = 0
    for key, value in CSF_LABELS.items():
        if any(ord(c) > 127 for c in key) or any(ord(c) > 127 for c in value):
            raise SystemExit(f"non-ASCII CSF {key!r}")
        if key in have_idx:
            i = have_idx[key]
            mag, name, _strings = labels[i]
            labels[i] = (mag, name, [(ch.CSF_STR_MAGIC, value, b"")])
            updated += 1
        else:
            labels.append((ch.CSF_LBL_MAGIC, key, [(ch.CSF_STR_MAGIC, value, b"")]))
            added += 1
            have_idx[key] = len(labels) - 1
    print(f"CSF added {added} labels, updated {updated}")
    return ch.build_csf(version, unk, lang, labels)


def art_leaf_map(art_map: dict[str, tuple[str, bytes]]) -> dict[str, bytes]:
    out = {}
    for key, (_name, blob) in art_map.items():
        leaf = key.split("\\")[-1].lower()
        out[leaf] = blob
    return out


def validate(
    overlay: dict[str, bytes],
    cs_text: str,
    cb_text: str,
    wpn_text: str,
    sp_text: str,
    hc_text: str,
    data_map: dict[str, tuple[str, bytes]],
    art_map: dict[str, tuple[str, bytes]],
    csf_blob: bytes,
) -> list[str]:
    errors: list[str] = []
    objects = fire.parse_objects("\n".join(v.decode("latin1") for v in overlay.values() if b"Object " in v[:2000] or b"\nObject " in v))
    # parse overlay objects properly
    objects = {}
    for dest, content in overlay.items():
        if dest.lower().endswith(".ini") and b"Object " in content:
            objects.update(fire.parse_objects(content.decode("latin1")))
    weapons = fire.parse_weapons(wpn_text)
    packed_objects = fire.collect_packed_objects(data_map)
    art_leaves = {k.split("\\")[-1].lower() for k in art_map}
    mapped = set(re.findall(r"^MappedImage (\S+)\s*$", hc_text, re.M))
    _, _, _, csf_labels = ch.parse_csf(csf_blob)
    csf_keys = {name for _m, name, _s in csf_labels}

    fighter = ch.grab_block(cs_text, "BritainAirfieldCommandSet")
    large = ch.grab_block(cs_text, "Britain_LargeAirBaseCommandSet")
    heavy = ch.grab_block(cs_text, "Britain_HeavyAirBaseCommandSet")
    dozer = ch.grab_block(cs_text, "BritainDozerCommandSet")
    e7cs = ch.grab_block(cs_text, "Britain_E7AWACSCommandSet")
    helics = ch.grab_block(cs_text, "Britain_TransportHeliCommandSet")

    for name in ("BritainAirfieldCommandSet", "Britain_LargeAirBaseCommandSet", "Britain_HeavyAirBaseCommandSet"):
        if cs_text.count(f"CommandSet {name}") != 1:
            errors.append(f"CommandSet uniqueness fail {name} count={cs_text.count(f'CommandSet {name}')}")
    if cs_text.count("CommandSet Britain_E7AWACSCommandSet") != 1:
        errors.append("Britain_E7AWACSCommandSet uniqueness fail")
    if cs_text.count("CommandSet Britain_TransportHeliCommandSet") != 1:
        errors.append("Britain_TransportHeliCommandSet uniqueness fail")

    if "Command_ConstructBritainJetTornadoF3" not in fighter or "Command_ConstructBritainJetTornadoF3" not in large:
        errors.append("Tornado F3 missing from fighter/large airbase")
    if "Command_ConstructBritainJetPhantomFGR2" not in heavy:
        errors.append("Phantom FGR.2 missing from heavy airbase")
    if "Command_SetRallyPoint" not in fighter or "Command_Sell" not in fighter:
        errors.append("Rally/Sell missing from fighter airbase")
    if "Command_ConstructAmericaLgm30" not in dozer:
        errors.append("Dozer missing nuclear AmericaLgm30")
    if "HelicopterBase" in fighter or "HelicopterBase" in heavy:
        errors.append("Helicopter Base leaked onto airbase")
    if re.search(r"^\s*15\s*=", fighter, re.M) or re.search(r"^\s*15\s*=", heavy, re.M):
        errors.append("used invisible slot 15+ on UK airbase")

    if "Command_FireMainWeapon" in e7cs or "Command_AttackMove" in e7cs:
        errors.append("E-7 commandset still has attack commands")
    if "Command_Britain_E7Scan" not in e7cs:
        errors.append("E-7 missing scan button")
    if "Command_ChinookUnload" not in helics:
        errors.append("transport heli commandset missing unload")

    e7 = objects.get("BritainAircraftE7", "")
    if "WeaponSet" in e7:
        errors.append("E-7 still has WeaponSet")
    if "Britain_SpecialPower_E7Scan" not in e7:
        errors.append("E-7 missing scan special")
    if "CAN_ATTACK" in e7:
        errors.append("E-7 KindOf still CAN_ATTACK")
    if "StealthDetectorUpdate" not in e7:
        errors.append("E-7 missing StealthDetectorUpdate")
    if "SpecialPower Britain_SpecialPower_E7Scan" not in sp_text:
        errors.append("Britain_SpecialPower_E7Scan missing from SpecialPower.ini")

    hawk = objects.get("BritainJetHawk200", "")
    if "AVHawk" in hawk or "KVE737" in hawk:
        errors.append("Hawk 200 still uses AWACS-like ART")
    if "LSFF16" not in hawk:
        errors.append("Hawk 200 not using LSFF16")
    if not re.search(r"Scale\s*=\s*0\.86", hawk):
        errors.append("Hawk 200 scale not 0.86")

    vulcan = objects.get("BritainBomberVulcan", "")
    if not re.search(r"Scale\s*=\s*0\.96", vulcan):
        errors.append("Vulcan scale not reduced to 0.96")

    scale_expect = {
        "BritainJetHarrierGR9": "0.93",
        "BritainJetSeaHarrierFA2": "0.90",
        "BritainJetJaguarGR3": "0.95",
        "BritainJetLightningF6": "1.02",
    }
    for obj, sc in scale_expect.items():
        block = objects.get(obj, "")
        if not re.search(rf"Scale\s*=\s*{re.escape(sc)}", block):
            errors.append(f"{obj} scale not {sc}")

    sea = objects.get("BritainJetSeaHarrierFA2", "")
    if "LSFAV8B" in sea:
        errors.append("Sea Harrier still cloned from Harrier AV-8B")
    jag = objects.get("BritainJetJaguarGR3", "")
    if "LSFTornado" in jag:
        errors.append("Jaguar still cloned from Tornado mesh")
    t3 = objects.get("BritainJetTyphoonT3", "")
    if "LSFEUEF2000" in t3:
        errors.append("Typhoon T3 still cloned from FGR4 mesh")

    a2a = {
        "BritainJetTyphoonFGR4": "Britain_Weapon_Meteor",
        "BritainJetF35B": "Britain_Weapon_AMRAAM",
        "BritainJetTornadoF3": "Britain_Weapon_Meteor_Long",
        "BritainJetPhantomFGR2": "Britain_Weapon_AMRAAM",
        "BritainJetSeaHarrierFA2": "Britain_Weapon_AMRAAM",
        "BritainJetLightningF6": "Britain_Weapon_Meteor",
    }
    for obj, wpn in a2a.items():
        if wpn not in objects.get(obj, ""):
            errors.append(f"{obj} missing A2A weapon {wpn}")
        if obj == "BritainJetTornadoF3":
            block = objects[obj]
            if any(x in block for x in ("Britain_Weapon_Bomb", "Britain_Weapon_Paveway", "Britain_Weapon_StormShadow")):
                errors.append("Tornado F3 has A2G bombs")

    if "Britain_Weapon_StormShadow" not in objects.get("BritainJetTornadoGR4", ""):
        errors.append("Tornado GR4 missing Storm Shadow")
    if "Britain_Weapon_Bomb_Heavy" not in objects.get("BritainJetTornadoGR4", ""):
        errors.append("Tornado GR4 missing heavy bomb payload")
    if "Britain_Weapon_JetRockets" not in objects.get("BritainJetJaguarGR3", ""):
        errors.append("Jaguar missing rockets")
    if "Britain_Weapon_Brimstone" not in objects.get("BritainJetHarrierGR9", ""):
        errors.append("Harrier GR9 missing Brimstone")

    for heli in ("BritainHelicopterMerlin", "BritainHelicopterPuma", "BritainHelicopterWildcat"):
        block = objects.get(heli, "")
        if "JetAIUpdate" not in block:
            errors.append(f"{heli} missing JetAIUpdate")
        if "ChinookAIUpdate" in block:
            errors.append(f"{heli} still ChinookAIUpdate")
        if "ComancheLocomotor" not in block:
            errors.append(f"{heli} missing ComancheLocomotor")
        if "NeedsRunway = No" not in block:
            errors.append(f"{heli} missing NeedsRunway = No")
        if "CAN_ATTACK" not in block:
            errors.append(f"{heli} missing CAN_ATTACK")
    if "Britain_Weapon_HeliATGM" not in objects.get("BritainHelicopterWildcat", ""):
        errors.append("Wildcat missing ground-attack ATGM")

    used_w3d: dict[str, list[str]] = {}
    for obj, block in objects.items():
        if not obj.startswith("Britain"):
            continue
        for model in re.findall(r"^\s*Model\s+=\s+(\S+)", block, re.M):
            leaf = f"{model}.w3d".lower()
            if leaf not in art_leaves and f"{model.lower()}.w3d" not in art_leaves:
                errors.append(f"{obj} Model {model} W3D missing from ART")
            used_w3d.setdefault(model, []).append(obj)
        for wslot, wname in re.findall(r"Weapon\s+=\s+(PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", block):
            if wname not in weapons:
                errors.append(f"{obj} {wslot} weapon {wname} missing")
            else:
                proj = re.search(r"ProjectileObject\s+=\s+(\S+)", weapons[wname])
                if proj and proj.group(1) not in packed_objects:
                    errors.append(f"{wname} projectile {proj.group(1)} not packed")
        portrait = re.search(r"SelectPortrait\s+=\s+(\S+)", block)
        if portrait and portrait.group(1) not in mapped:
            errors.append(f"{obj} portrait {portrait.group(1)} missing MappedImage")
        disp = re.search(r"DisplayName\s+=\s+(\S+)", block)
        if disp and disp.group(1) not in csf_keys:
            errors.append(f"{obj} CSF {disp.group(1)} missing")

    # Button refs for UK sets
    core = set(re.findall(r"^CommandButton (\S+)\s*$", cb_text, re.M))
    for name in (
        "BritainAirfieldCommandSet",
        "Britain_LargeAirBaseCommandSet",
        "Britain_HeavyAirBaseCommandSet",
        "Britain_E7AWACSCommandSet",
        "Britain_TransportHeliCommandSet",
        "BritainDozerCommandSet",
    ):
        idx = cs_text.find(f"CommandSet {name}")
        declared = core | set(re.findall(r"^CommandButton (\S+)\s*$", cs_text[:idx], re.M))
        block = ch.grab_block(cs_text, name)
        for line in block.splitlines():
            m = re.match(r"^\s*\d+\s*=\s*(Command_\S+)\s*$", line)
            if m and m.group(1) not in declared:
                errors.append(f"{name} refs unknown CommandButton {m.group(1)}")

    for key, value in CSF_LABELS.items():
        if key not in csf_keys:
            errors.append(f"CSF missing {key}")
        for donor in DONOR_NAMES:
            if donor.lower() in value.lower() and donor not in ("Meteor",):
                # Allow nothing that looks like a donor aircraft name in UK labels.
                if donor in ("F-16", "F16", "FA-18", "FA18", "AVHawk", "Mirage", "Rafale", "MiG", "B-52", "F-4"):
                    errors.append(f"CSF donor name {donor} in {key}={value}")

    new_btns = (
        "Command_ConstructBritainJetTornadoF3",
        "Command_ConstructBritainJetPhantomFGR2",
        "Command_Britain_E7Scan",
    )
    for btn in new_btns:
        if f"CommandButton {btn}" not in cs_text and f"CommandButton {btn}" not in cb_text:
            errors.append(f"CommandButton {btn} not declared")
        tip = f"CONTROLBAR:ToolTip{btn.replace('Command_Construct', '').replace('Command_', '')}" if False else None
    for key in (
        "CONTROLBAR:ConstructBritainJetTornadoF3",
        "CONTROLBAR:ConstructBritainJetPhantomFGR2",
        "CONTROLBAR:BritainE7Scan",
    ):
        if key not in csf_keys:
            errors.append(f"CSF missing {key}")

    return errors, used_w3d, objects


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/uk_airforce_diversity"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    overlay = collect_uk_overlay()
    ch.parse_check(overlay)
    print(f"overlay files {len(overlay)}")

    data_entries, data_raw = ch.read_big(BASE_DATA)
    art_entries, art_raw = ch.read_big(BASE_ART)
    data_map: dict[str, tuple[str, bytes]] = {}
    data_keys = []
    for name, off, size in data_entries:
        key = ch.norm_key(name)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (name.replace("/", "\\"), data_raw[off : off + size])
    art_map: dict[str, tuple[str, bytes]] = {}
    art_keys = []
    for name, off, size in art_entries:
        key = ch.norm_key(name)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (name.replace("/", "\\"), art_raw[off : off + size])

    protect_hash = {
        n: hashlib.sha256(ch.grab_block(data_map["data\\ini\\commandset.ini"][1].decode("latin1"), n).encode("latin1")).hexdigest()
        for n in PROTECT_SETS
    }
    dozer_before = ch.grab_block(data_map["data\\ini\\commandset.ini"][1].decode("latin1"), "BritainDozerCommandSet")

    wpn_key = "data\\ini\\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    eu_wpn = overlay[r"Data\INI\Weapon_EuropeAirforce.ini"]
    wpn_blob = fire.replace_marked_block(wpn_blob, EUROPE_MARKER, None, eu_wpn)
    data_map[wpn_key] = (wpn_name, ch.lf(wpn_blob))
    wpn_text = data_map[wpn_key][1].decode("latin1")
    for required in (
        "Britain_Weapon_Meteor_Long",
        "Britain_Weapon_SDB",
        "Britain_Weapon_Paveway_Heavy",
        "Britain_Weapon_Bomb_Heavy",
        "Britain_Weapon_HawkBomb",
        "Britain_Weapon_JetRockets",
        "Britain_Weapon_HeliATGM_Light",
        "Britain_Weapon_HeliCannon_Light",
        "Germany_Weapon_Meteor",
        "Italy_Weapon_JetCannon",
    ):
        if f"Weapon {required}" not in wpn_text:
            raise SystemExit(f"Weapon.ini missing {required}")
    print("Inlined Europe/UK weapons into Weapon.ini")

    sp_key = "data\\ini\\specialpower.ini"
    sp_name, sp_blob = data_map[sp_key]
    sp_payload = overlay[r"Data\INI\SpecialPower_BritainAirforce.ini"]
    if b"SpecialPower Britain_SpecialPower_E7Scan" not in sp_blob:
        sp_blob = sp_blob.rstrip() + UK_SP_MARKER + sp_payload
    else:
        sp_blob = fire.replace_marked_block(sp_blob, UK_SP_MARKER, None, sp_payload)
    data_map[sp_key] = (sp_name, ch.lf(sp_blob))
    print("Inlined Britain_SpecialPower_E7Scan into SpecialPower.ini")

    cs_key = "data\\ini\\commandset.ini"
    cb_key = "data\\ini\\commandbutton.ini"
    cs_name, cs_blob = data_map[cs_key]
    cb_name, cb_blob = data_map[cb_key]
    cs_text = cs_blob.decode("latin1")
    cb_text = cb_blob.decode("latin1")
    btn_src = overlay[r"Data\INI\CommandButton_EuropeAirforce.ini"].decode("ascii")
    new_btns = extract_named_buttons(
        btn_src,
        [
            "Command_ConstructBritainJetTornadoF3",
            "Command_ConstructBritainJetPhantomFGR2",
            "Command_Britain_E7Scan",
        ],
    )
    extra_sets = (
        "CommandSet Britain_E7AWACSCommandSet\n"
        "  1 = Command_Britain_E7Scan\n"
        "  13 = Command_Guard\n"
        "  14 = Command_Stop\n"
        "End\n\n"
        "CommandSet Britain_TransportHeliCommandSet\n"
        "  11 = Command_AttackMove\n"
        "  12 = Command_ChinookUnload\n"
        "  13 = Command_Guard\n"
        "  14 = Command_Stop\n"
        "End\n"
    )
    cs_text = strip_blocks(
        cs_text,
        [
            "Command_ConstructBritainJetTornadoF3",
            "Command_ConstructBritainJetPhantomFGR2",
            "Command_Britain_E7Scan",
            "Britain_E7AWACSCommandSet",
            "Britain_TransportHeliCommandSet",
        ],
    )
    cs_text = insert_before(
        cs_text,
        "CommandSet BritainAirfieldCommandSet",
        new_btns + "\n" + extra_sets,
    )
    cs_text = fr.replace_block(cs_text, "BritainAirfieldCommandSet", cs_block("BritainAirfieldCommandSet", FIGHTER_BTNS))
    cs_text = fr.replace_block(
        cs_text,
        "Britain_LargeAirBaseCommandSet",
        cs_block("Britain_LargeAirBaseCommandSet", FIGHTER_BTNS),
    )
    cs_text = fr.replace_block(
        cs_text,
        "Britain_HeavyAirBaseCommandSet",
        cs_block("Britain_HeavyAirBaseCommandSet", HEAVY_BTNS),
    )
    dozer_after = ch.grab_block(cs_text, "BritainDozerCommandSet")
    if dozer_after != dozer_before:
        raise SystemExit("BritainDozerCommandSet mutated")
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))
    print("Patched UK CommandSets (fighter slot 12 Tornado F3, heavy slot 10 Phantom FGR.2)")

    hc_key = "data\\ini\\mappedimages\\handcreated\\handcreatedmappedimages.ini"
    hc_name, hc_blob = data_map[hc_key]
    portraits_ini = overlay[r"Data\INI\MappedImages\HandCreated\zEurope_AirbasePortrait_Images.INI"].decode("ascii")
    hc_text = hc_blob.decode("latin1")
    for name in ("SPEC_BritainTornadoF3", "SPEC_BritainPhantomFGR2"):
        hc_text = re.sub(
            rf"^MappedImage {re.escape(name)}\s*\n.*?^End\s*$\n?",
            "",
            hc_text,
            count=1,
            flags=re.M | re.S,
        )
    extra_map = []
    for m in re.finditer(
        r"^MappedImage (SPEC_BritainTornadoF3|SPEC_BritainPhantomFGR2)\s*\n.*?^End\s*$",
        portraits_ini,
        re.M | re.S,
    ):
        extra_map.append(m.group(0).rstrip())
    if not hc_text.endswith("\n"):
        hc_text += "\n"
    hc_text += "\n" + "\n\n".join(extra_map) + "\n"
    data_map[hc_key] = (hc_name, ch.lf(hc_text.encode("latin1")))

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_blob = data_map[csf_key]
    csf_new = patch_csf(csf_blob)
    ch.validate_csf(csf_new, list(CSF_LABELS))
    data_map[csf_key] = (csf_name, csf_new)

    skip_inject = {
        "data\\ini\\commandbutton_europeairforce.ini",
        "data\\ini\\commandset_britain.ini",
    }
    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key in skip_inject:
            continue
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    packed_tex = art_leaf_map(art_map)
    for dest_name, src_rel in PORTRAIT_SRC.items():
        leaf = Path(src_rel).name.lower()
        if leaf not in packed_tex:
            raise SystemExit(f"missing portrait source {src_rel}")
        tmp = Path("/tmp") / leaf
        tmp.write_bytes(packed_tex[leaf])
        tga = eu.make_portrait_any(tmp)
        dest = f"Art\\Textures\\{dest_name}"
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, tga)
        print("ART portrait", dest)

    cs_text = data_map[cs_key][1].decode("latin1")
    cb_text = data_map[cb_key][1].decode("latin1")
    wpn_text = data_map[wpn_key][1].decode("latin1")
    sp_text = data_map[sp_key][1].decode("latin1")
    hc_text = data_map[hc_key][1].decode("latin1")
    ch.validate_commandset_button_refs(cs_text, cb_text)
    errors, used_w3d, objects = validate(
        overlay,
        cs_text,
        cb_text,
        wpn_text,
        sp_text,
        hc_text,
        data_map,
        art_map,
        csf_new,
    )
    if errors:
        raise SystemExit("VALIDATE FAIL\n" + "\n".join(errors))
    print("VALIDATE PASS weapons/CommandButton/CommandSet/ART/MappedImage/CSF")

    cs_after = data_map[cs_key][1].decode("latin1")
    for n in PROTECT_SETS:
        h = hashlib.sha256(ch.grab_block(cs_after, n).encode("latin1")).hexdigest()
        if h != protect_hash[n]:
            raise SystemExit(f"PROTECTED CommandSet mutated: {n}")
    print("PROTECT CHECK PASS France/Germany/Italy/China/Russia CommandSets unchanged")

    out_data_map = {data_map[k][0]: data_map[k][1] for k in data_keys}
    out_art_map = {art_map[k][0]: art_map[k][1] for k in art_keys}
    data_big = ch.build_big(out_data_map)
    art_big = ch.build_big(out_art_map)
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_big)
    out_art.write_bytes(art_big)

    # Re-extract both BIGs and confirm changed files are inside.
    v_data_entries, v_data_raw = ch.read_big(out_data)
    v_art_entries, v_art_raw = ch.read_big(out_art)
    v_data = {ch.norm_key(n): v_data_raw[off : off + size] for n, off, size in v_data_entries}
    v_art = {ch.norm_key(n): v_art_raw[off : off + size] for n, off, size in v_art_entries}
    must_data = [
        r"data\ini\object\specter\british armed forces\airforce\britainjettornadof3.ini",
        r"data\ini\object\specter\british armed forces\airforce\britainjetphantomfgr2.ini",
        r"data\ini\object\specter\british armed forces\airforce\britainjethawk200.ini",
        r"data\ini\object\specter\british armed forces\airforce\britainaircrafte7.ini",
        r"data\ini\object\specter\british armed forces\rotary\britainhelicoptermerlin.ini",
        r"data\ini\object\specter\british armed forces\rotary\britainhelicopterpuma.ini",
        r"data\ini\object\specter\british armed forces\rotary\britainhelicopterwildcat.ini",
        r"data\ini\weapon.ini",
        r"data\ini\commandset.ini",
        r"data\ini\specialpower.ini",
    ]
    for key in must_data:
        if key not in v_data:
            raise SystemExit(f"re-extract missing DATA {key}")
    hawk = v_data[r"data\ini\object\specter\british armed forces\airforce\britainjethawk200.ini"].decode("latin1")
    if "AVHawk" in hawk or "LSFF16" not in hawk:
        raise SystemExit("re-extract Hawk ART check fail")
    e7 = v_data[r"data\ini\object\specter\british armed forces\airforce\britainaircrafte7.ini"].decode("latin1")
    if "WeaponSet" in e7 or "Britain_SpecialPower_E7Scan" not in e7:
        raise SystemExit("re-extract E-7 check fail")
    wild = v_data[r"data\ini\object\specter\british armed forces\rotary\britainhelicopterwildcat.ini"].decode("latin1")
    if "JetAIUpdate" not in wild or "Britain_Weapon_HeliATGM" not in wild:
        raise SystemExit("re-extract Wildcat check fail")
    cst = v_data[r"data\ini\commandset.ini"].decode("latin1")
    if "Command_ConstructBritainJetTornadoF3" not in ch.grab_block(cst, "BritainAirfieldCommandSet"):
        raise SystemExit("re-extract fighter CommandSet missing Tornado F3")
    if "Command_ConstructBritainJetPhantomFGR2" not in ch.grab_block(cst, "Britain_HeavyAirBaseCommandSet"):
        raise SystemExit("re-extract heavy CommandSet missing Phantom FGR.2")
    wpn = v_data[r"data\ini\weapon.ini"].decode("latin1")
    if "Weapon Britain_Weapon_Meteor_Long" not in wpn:
        raise SystemExit("re-extract Weapon.ini missing Meteor_Long")
    for portrait in PORTRAIT_SRC:
        key = ch.norm_key(f"Art\\Textures\\{portrait}")
        if key not in v_art:
            raise SystemExit(f"re-extract missing ART {portrait}")
    print("RE-EXTRACT VERIFY PASS")

    install = (
        "Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into the Specter Data folder.\n"
        "Keep EnglishZH.big and AudioZH.big unchanged.\n"
        "UNITED KINGDOM air force visual diversity and fire fix only.\n"
        "Does not change France, Germany, Italy, Russia, China, USA, or other countries.\n"
        "Fighter Airbase + Heavy/Large Airbase preserved. Nuclear/Atomic dozer slot preserved.\n"
        "New interceptors: Tornado F3 (fighter slot 12), Phantom FGR.2 (heavy slot 10).\n"
        "E-7 Wedgetail is AWACS scan only. Merlin/Puma/Wildcat fly as helicopters.\n"
    )
    zpath = out / "UK_AIRFORCE_DIVERSITY_FIRE_FIX.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.writestr("INSTALL.txt", install)
    verify = out / "zip_verify"
    if verify.exists():
        shutil.rmtree(verify)
    verify.mkdir()
    with zipfile.ZipFile(zpath, "r") as zf:
        zf.extractall(verify)
        names = set(zf.namelist())
    if names != {"_SPEC_DATA_ONE.big", "_SPEC_ART_ONE.big", "INSTALL.txt"}:
        raise SystemExit(f"ZIP contents unexpected: {sorted(names)}")
    if hashlib.sha256((verify / "_SPEC_DATA_ONE.big").read_bytes()).digest() != hashlib.sha256(data_big).digest():
        raise SystemExit("ZIP DATA hash mismatch")
    if hashlib.sha256((verify / "_SPEC_ART_ONE.big").read_bytes()).digest() != hashlib.sha256(art_big).digest():
        raise SystemExit("ZIP ART hash mismatch")
    print("ZIP extract verify PASS")

    data_sha = hashlib.sha256(data_big).hexdigest()
    art_sha = hashlib.sha256(art_big).hexdigest()
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    table_lines = ["UK AIRCRAFT | ORIGINAL/EXACT MODEL | SELECTED W3D | SOURCE"]
    for row in W3D_TABLE:
        table_lines.append(" | ".join(row))
    report = out / "PACK_REPORT.txt"
    report.write_text(
        f"DATA sha256 {data_sha}\n"
        f"ART  sha256 {art_sha}\n"
        f"ZIP  sha256 {zip_sha}\n"
        f"DATA bytes {len(data_big)}\n"
        f"ART  bytes {len(art_big)}\n"
        "PARSER CHECK PASS\n"
        "WEAPON reference PASS\n"
        "CommandButton PASS\n"
        "CommandSet uniqueness PASS\n"
        "ART/W3D PASS\n"
        "MappedImage PASS\n"
        "CSF PASS\n"
        "PROTECT CHECK PASS France/Germany/Italy/China/Russia\n"
        "RE-EXTRACT VERIFY PASS\n"
        "ZIP extract verify PASS\n"
        "UK ONLY\n"
        "Fighter slot 12 = Tornado F3\n"
        "Heavy slot 10 = Phantom FGR.2\n"
        "Dozer slot 12 = Command_ConstructAmericaLgm30\n"
        "\n" + "\n".join(table_lines) + "\n",
        encoding="ascii",
    )
    print(report.read_text())
    print("wrote", zpath)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
