#!/usr/bin/env python3
"""Add four country-sourced UAV/launcher options to 18 radar menus.

Slots 9-12 on each target country's effective radar CommandSet:
  9  SpecterRadar_Heron            (Israel Heron)                 $10,000
  10 SpecterRadar_MQ4              (USA MQ-4 Global Hawk)         $12,000
  11 SpecterRadar_Orlan10          (Russia Orlan-10)              $10,000
  12 SpecterRadar_ShahedLauncher   (Iran Shahed-136 launcher)     $8,000

Baseline packed archives: SPECTER_IRAQ_MIC_MENU_FIX (PR #665).
ART_ONE / ART_TWO are copied byte-identical. DATA last-wins overlay only.

Live catalogs CommandSet.ini and CommandButton.ini are patched (PR #664
ZZZZ-only menus did not appear in-game). CommandSet_ZZZZ_SpySatelliteRadar.ini
is also patched because it currently last-wins these 18 CommandSets.

Copy-only: original source objects, source buttons, and source-country
radar menus stay intact. Shared copies exist so BuildCost and Orlan-10
prerequisites can change without mutating Israel/USA/Russia/Iran units.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_iraq_mic_radar_ad as rad  # noqa: E402
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MIC_MENU_FIX/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_MENU_FIX/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_MENU_FIX/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_RADAR_UAV_SLOTS"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "2de43345a2fa3b1789c50c0bad4d0bf8279e8a6c9e6919d5aa47f337e57e75c8"
SIZE_DATA_SRC = 370871289
SHA_ART1_SRC = rad.SHA_ART1_SRC
SIZE_ART1_SRC = rad.SIZE_ART1_SRC
SHA_ART2_SRC = rad.SHA_ART2_SRC
SIZE_ART2_SRC = rad.SIZE_ART2_SRC
SAGE_SAFE = 2147483648

CS_INI = r"Data\INI\CommandSet.ini"
CB_INI = r"Data\INI\CommandButton.ini"
CS_ZZZZ = r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini"
CS_PAK = r"Data\INI\CommandSet_Pakistan.ini"
OBJ_KEY = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
MIC_OBJ_KEY = rad.MIC_OBJ_KEY
WF_OBJ_KEY = rad.WF_OBJ_KEY
AA_WF_KEY = rad.AA_WF_KEY
KARRAR_KEY = rad.KARRAR_KEY
MIC_CS_NAMES = rad.MIC_CS_NAMES
WF_CS_NAME = rad.WF_CS_NAME
SELL = rad.SELL
PREREQ_RE = rad.PREREQ_RE

# Internal ids from packed PlayerTemplate / radar objects, not display names.
COUNTRIES = [
    {"display": "Sweden", "radar": "SwedenRadarGM406", "cs": "SwedenGM406CommandSet"},
    {"display": "Ukraine", "radar": "UkraineRadarGM406", "cs": "UkraineGM406CommandSet"},
    {"display": "Turkey", "radar": "TurkeyRadarGM406", "cs": "TurkeyGM406CommandSet"},
    {"display": "Italy", "radar": "ItalyRadarGM406", "cs": "ItalyGM406CommandSet"},
    {"display": "Britain", "radar": "BritainRadarGM406", "cs": "BritainGM406CommandSet"},
    {"display": "Germany", "radar": "GermanyRadarGM406", "cs": "GermanyGM406CommandSet"},
    {"display": "France", "radar": "FranceRadarGM406", "cs": "FranceGM406CommandSet"},
    {"display": "Iraq", "radar": "Iraq_RadarStation", "cs": "Iraq_RadarStationCommandSet"},
    {"display": "India", "radar": "India_RadarStation", "cs": "India_RadarCommandSet"},
    {"display": "Pakistan", "radar": "Pakistan_RadarStation", "cs": "Pakistan_RadarCommandSet"},
    {"display": "Syria", "radar": "Syria_RadarStation", "cs": "Syria_RadarCommandSet"},
    {"display": "Saudi Arabia", "radar": "SaudiArabia_RadarStation", "cs": "SaudiArabia_RadarCommandSet"},
    {"display": "United Arab Emirates", "radar": "UAE_RadarStation", "cs": "UAE_RadarCommandSet"},
    {"display": "Libya", "radar": "Libya_RadarStation", "cs": "Libya_RadarCommandSet"},
    {"display": "South Africa", "radar": "SouthAfrica_RadarStation", "cs": "SouthAfrica_RadarCommandSet"},
    {"display": "South Korea", "radar": "SouthKorea_RadarStation", "cs": "SouthKorea_RadarStationCommandSet"},
    {"display": "Japan", "radar": "Japan_RadarStation", "cs": "Japan_RadarStationCommandSet"},
    {"display": "Vietnam", "radar": "Vietnam_RadarStation", "cs": "Vietnam_RadarStationCommandSet"},
]
CS_NAMES = tuple(c["cs"] for c in COUNTRIES)

# Source identity resolved from packed last-wins, not guessed names.
COPIES = [
    {
        "slot": "9",
        "country": "Israel",
        "source": "IsraelDroneHeron",
        "src_cmd": "Command_ConstructIsraelDroneHeron",
        "src_cs": "IsraelRadarStationCommandSet",
        "copy": "SpecterRadar_Heron",
        "cmd": "Command_ConstructSpecterRadarHeron",
        "cost": "10000",
        "src_cost": "900",
        "button": "Nat_heron",
        "label": "CONTROLBAR:ConstructIsraelDroneHeron",
        "tip": "CONTROLBAR:ToolTipIsraelDroneHeron",
        "src_prereq": "",
        "src_file": r"Data\INI\Object\Specter\Israel Defense Forces\Drones\Heron.ini",
        "display": "OBJECT:Heron",
        "side": "Israel",
    },
    {
        "slot": "10",
        "country": "USA",
        "source": "AmericaDroneMQ4",
        "src_cmd": "Command_ConstructAmericaDroneMQ4",
        "src_cs": "AmericaRadarStationCommandSet",
        "copy": "SpecterRadar_MQ4",
        "cmd": "Command_ConstructSpecterRadarMQ4",
        "cost": "12000",
        "src_cost": "2200",
        "button": "us_mq4",
        "label": "CONTROLBAR:ConstructAmericaJetMQ4",
        "tip": "CONTROLBAR:ToolTipUSABuildMQ4",
        "src_prereq": "",
        "src_file": r"Data\INI\Object\Specter\United States Of America\Drones\Mq4.ini",
        "display": "OBJECT:MQ4D",
        "side": "America",
    },
    {
        "slot": "11",
        "country": "Russia",
        "source": "RussiaDroneOrlan10",
        "src_cmd": "Command_ConstructRussiaDroneOrlan10",
        "src_cs": "RussiaRadarStationCommandSet",
        "copy": "SpecterRadar_Orlan10",
        "cmd": "Command_ConstructSpecterRadarOrlan10",
        "cost": "10000",
        "src_cost": "1500",
        "button": "rus_orlan10",
        "label": "CONTROLBAR:ConstructRussiaDroneOrlan10",
        "tip": "CONTROLBAR:ToolTipRussiaDroneOrlan10",
        "src_prereq": "Russia91N6E",
        "src_file": r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Drones\Orlan10.ini",
        "display": "OBJECT:Olan10",
        "side": "Russia",
    },
    {
        "slot": "12",
        "country": "Iran",
        "source": "IranVehicleShahedLauncher",
        "src_cmd": "Command_ConstructIranVehicleShahedLauncher",
        "src_cs": "IranWarFactoryCommandSet",
        "copy": "SpecterRadar_ShahedLauncher",
        "cmd": "Command_ConstructSpecterRadarShahedLauncher",
        "cost": "8000",
        "src_cost": "1500",
        "button": "irn_shahedlncher",
        "label": "CONTROLBAR:ConstructIranVehicleShahedLauncher",
        "tip": "CONTROLBAR:ToolTipBuildIranVehicleShahedLauncher",
        "src_prereq": "",
        "src_file": r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini",
        "display": "OBJECT:ShahedLauncher",
        "side": "Iran",
    },
]
UAV_SLOTS = {item["slot"]: item["cmd"] for item in COPIES}

UNRELATED_CS = (
    "NatoGM406CommandSet",
    "IranExpandedRadarCommandSet",
    "ChinaRadarStationCommandSet",
    "RussiaRadarStationCommandSet",
    "IsraelRadarStationCommandSet",
    "AmericaRadarStationCommandSet",
    "NorthKorea_RadarStationCommandSet",
)

FROZEN_SOURCE = [
    r"Data\INI\Object\Specter\Israel Defense Forces\Drones\Heron.ini",
    r"Data\INI\Object\Specter\United States Of America\Drones\Mq4.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Drones\Orlan10.ini",
    r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini",
    MIC_OBJ_KEY,
    WF_OBJ_KEY,
    AA_WF_KEY,
    KARRAR_KEY,
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_RadarStation.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\GM406.ini",
    r"Data\INI\CommandSet_ZZZZ_IraqMicToWfRadarAd.ini",
    r"Data\INI\CommandSet_ZZZZ_IraqMicToWf.ini",
    r"Data\INI\CommandButton_ZZZZ_IraqMicRadarAd.ini",
]

LOOSE_CS_FILES = [
    LOOSE / "CommandSet.ini",
    LOOSE / "CommandSet_ZZZZ_SpySatelliteRadar.ini",
    LOOSE / "CommandSet_Pakistan.ini",
    LOOSE / "CommandSet_Sweden.ini",
    LOOSE / "CommandSet_France.ini",
    LOOSE / "CommandSet_Britain.ini",
    LOOSE / "CommandSet_Italy.ini",
    LOOSE / "CommandSet_Germany.ini",
    LOOSE / "CommandSet_India.ini",
    LOOSE / "CommandSet_SaudiArabia.ini",
    LOOSE / "CommandSet_UAE.ini",
    LOOSE / "CommandSet_Libya.ini",
    LOOSE / "CommandSet_Syria.ini",
    LOOSE / "CommandSet_SouthAfrica.ini",
]


def last_from(order, files, kind, name):
    return sk.last_block_from_files(order, files, kind, name)


def field(block: str, key: str) -> str:
    return sk.field(block, key)


def sha256_path(path: Path) -> str:
    return rad.sha256_path(path)


def slot_map(block: str) -> dict[str, str]:
    return rad.slot_map(block)


def catalog_block(text: str, kind: str, name: str) -> str:
    return sk.last_block(text, kind, name)


def clone_object(src_block: str, item: dict) -> str:
    lines = src_block.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines or not re.match(rf"Object\s+{re.escape(item['source'])}\s*$", lines[0]):
        raise SystemExit(f"unexpected object header for {item['source']}: {lines[0]!r}")
    note = (
        f"; SPECTER radar UAV copy of {item['source']}. "
        f"Adaptations: BuildCost={item['cost']}"
    )
    if item["src_prereq"]:
        note += f"; Prerequisites emptied (source required {item['src_prereq']})"
    note += ". Side/DisplayName/model/weapon unchanged."
    lines[0] = f"Object {item['copy']}"
    text = "\n".join(lines)
    text = re.sub(r"(?m)^(\s*BuildCost\s*=\s*)\S+", rf"\g<1>{item['cost']}", text, count=1)
    emptied, n = PREREQ_RE.subn(r"\1Prerequisites\n\1End", text)
    if n:
        text = emptied
    text = f"{lines[0]}\n{note}\n" + "\n".join(text.split("\n")[1:])
    if not text.endswith("\n"):
        text += "\n"
    return text


def make_button(item: dict) -> str:
    return (
        f"CommandButton {item['cmd']}\n"
        f"  Command       = UNIT_BUILD\n"
        f"  Object        = {item['copy']}\n"
        f"  TextLabel     = {item['label']}\n"
        f"  ButtonImage   = {item['button']}\n"
        f"  ButtonBorderType        = BUILD\n"
        f"  DescriptLabel           = {item['tip']}\n"
        f"End\n"
    )


def patch_commandset(block: str, cs_name: str) -> str:
    sl = slot_map(block)
    for slot, cmd in UAV_SLOTS.items():
        existing = sl.get(slot)
        if existing and existing != cmd:
            raise SystemExit(f"{cs_name} slot {slot} occupied by {existing}")
    lines = block.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    if not lines or lines[-1].strip() != "End":
        raise SystemExit(f"{cs_name} missing End")
    kept = []
    slot_line = re.compile(r"^[ \t]*(\d+)[ \t]*=")
    for line in lines[:-1]:
        m = slot_line.match(line)
        if m and m.group(1) in UAV_SLOTS:
            continue
        kept.append(line)
    for slot in ("9", "10", "11", "12"):
        kept.append(f"  {slot} = {UAV_SLOTS[slot]}")
    kept.append("End")
    return "\n".join(kept)


def patch_text_commandsets(text: str) -> tuple[str, list[str]]:
    text = text.replace("\r\n", "\n")
    patched = []
    for name in CS_NAMES:
        blk = catalog_block(text, "CommandSet", name)
        if not blk:
            continue
        text = sk.replace_last(text, "CommandSet", name, patch_commandset(blk, name))
        patched.append(name)
    return text, patched


def ensure_buttons(cb_text: str) -> str:
    cb_text = cb_text.replace("\r\n", "\n")
    missing = []
    for item in COPIES:
        blk = catalog_block(cb_text, "CommandButton", item["cmd"])
        if not blk:
            missing.append(make_button(item).rstrip() + "\n")
            continue
        if field(blk, "Object") != item["copy"] or field(blk, "Command") != "UNIT_BUILD":
            cb_text = sk.replace_last(cb_text, "CommandButton", item["cmd"], make_button(item).rstrip())
        if field(blk, "ButtonImage") != item["button"]:
            cb_text = sk.replace_last(cb_text, "CommandButton", item["cmd"], make_button(item).rstrip())
        if "SelectPortrait" in (blk or ""):
            cb_text = sk.replace_last(cb_text, "CommandButton", item["cmd"], make_button(item).rstrip())
    if missing:
        if not cb_text.endswith("\n"):
            cb_text += "\n"
        cb_text += "\n" + "\n".join(missing)
    return cb_text


def models_of(block: str) -> list[str]:
    return re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", block or "")


def weapons_of(block: str) -> list[str]:
    return rad.weapon_names(block)


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_IRAQ_MIC_MENU_FIX")
    if sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline mismatch")
    if sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline mismatch")

    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)

    obj_parts = []
    btn_parts = []
    for item in COPIES:
        src_file, src_blk = last_from(order, files, "Object", item["source"])
        if not src_blk:
            raise SystemExit(f"missing source object {item['source']}")
        if src_file != item["src_file"]:
            raise SystemExit(f"{item['source']} last-wins {src_file}")
        if field(src_blk, "BuildCost") != item["src_cost"]:
            raise SystemExit(
                f"{item['source']} BuildCost {field(src_blk, 'BuildCost')} != {item['src_cost']}"
            )
        if field(src_blk, "Side") != item["side"]:
            raise SystemExit(f"{item['source']} Side {field(src_blk, 'Side')}")
        if field(src_blk, "DisplayName") != item["display"]:
            raise SystemExit(f"{item['source']} DisplayName {field(src_blk, 'DisplayName')}")
        if field(src_blk, "SelectPortrait") != item["button"]:
            raise SystemExit(f"{item['source']} SelectPortrait {field(src_blk, 'SelectPortrait')}")
        if field(src_blk, "ButtonImage") != item["button"]:
            raise SystemExit(f"{item['source']} ButtonImage {field(src_blk, 'ButtonImage')}")
        _, exist_copy = last_from(order, files, "Object", item["copy"])
        if exist_copy:
            raise SystemExit(f"copy object already exists: {item['copy']}")
        _, exist_cmd = last_from(order, files, "CommandButton", item["cmd"])
        if exist_cmd:
            raise SystemExit(f"copy command already exists: {item['cmd']}")
        obj_parts.append(clone_object(src_blk, item))
        btn_parts.append(make_button(item))

    files[OBJ_KEY] = sk.to_crlf("\n".join(obj_parts) + "\n")

    changed_cs_files = []
    for key in list(files):
        blob = files[key]
        if not key.lower().endswith(".ini"):
            continue
        if b"CommandSet " not in blob:
            continue
        if not any(f"CommandSet {name}".encode("ascii") in blob for name in CS_NAMES):
            continue
        text, patched = patch_text_commandsets(blob.decode("latin1"))
        if patched:
            files[key] = sk.to_crlf(text)
            changed_cs_files.append(f"{key}:{','.join(patched)}")

    cb_text = files[CB_INI].decode("latin1")
    files[CB_INI] = sk.to_crlf(ensure_buttons(cb_text))

    for key in FROZEN_SOURCE:
        if files.get(key) != original.get(key):
            raise SystemExit(f"frozen mutated: {key}")

    data_big = sk.build_big(files)
    packed, packed_order = sk.parse_big_ordered(data_big)
    fails = []
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))

    live_cs = packed[CS_INI].decode("latin1")
    live_cb = packed[CB_INI].decode("latin1")
    zzzz_cs = packed[CS_ZZZZ].decode("latin1")

    table = [
        "country|radar_object|commandset|slot9|cost9|slot10|cost10|slot11|cost11|slot12|cost12|live_cs|zzzz_cs"
    ]

    for country in COUNTRIES:
        src_obj, radar = last_from(packed_order, packed, "Object", country["radar"])
        if field(radar, "CommandSet") != country["cs"]:
            fails.append(
                f"{country['display']} radar CS {field(radar, 'CommandSet')} != {country['cs']}"
            )
        orig_obj, orig_radar = last_from(order, original, "Object", country["radar"])
        if src_obj != orig_obj or radar != orig_radar:
            fails.append(f"{country['radar']} object mutated")

        live_blk = catalog_block(live_cs, "CommandSet", country["cs"])
        zzzz_blk = catalog_block(zzzz_cs, "CommandSet", country["cs"])
        src_cs, packed_blk = last_from(packed_order, packed, "CommandSet", country["cs"])
        orig_src, orig_blk = last_from(order, original, "CommandSet", country["cs"])
        live_slots = slot_map(live_blk)
        zzzz_slots = slot_map(zzzz_blk)
        packed_slots = slot_map(packed_blk)
        orig_slots = slot_map(orig_blk)

        if not live_blk:
            fails.append(f"LIVE CommandSet.ini missing {country['cs']}")
        if not zzzz_blk:
            fails.append(f"ZZZZ missing {country['cs']}")

        for item in COPIES:
            if live_slots.get(item["slot"]) != item["cmd"]:
                fails.append(
                    f"LIVE {country['cs']} slot {item['slot']}={live_slots.get(item['slot'])}"
                )
            if zzzz_slots.get(item["slot"]) != item["cmd"]:
                fails.append(
                    f"ZZZZ {country['cs']} slot {item['slot']}={zzzz_slots.get(item['slot'])}"
                )
            if packed_slots.get(item["slot"]) != item["cmd"]:
                fails.append(
                    f"PACKED {country['cs']} last-wins {src_cs} slot {item['slot']}={packed_slots.get(item['slot'])}"
                )

        preserved = {k: v for k, v in orig_slots.items() if k not in UAV_SLOTS}
        current_preserved = {k: v for k, v in packed_slots.items() if k not in UAV_SLOTS}
        if preserved != current_preserved:
            fails.append(f"{country['cs']} lost existing slots {preserved} vs {current_preserved}")
        live_preserved = {k: v for k, v in live_slots.items() if k not in UAV_SLOTS}
        orig_live = slot_map(catalog_block(original[CS_INI].decode("latin1"), "CommandSet", country["cs"]))
        orig_live_preserved = {k: v for k, v in orig_live.items() if k not in UAV_SLOTS}
        if live_preserved != orig_live_preserved:
            fails.append(f"LIVE {country['cs']} lost existing slots")

        cmds = list(packed_slots.values())
        if cmds.count(UAV_SLOTS["12"]) != 1:
            fails.append(f"{country['cs']} Shahed button count {cmds.count(UAV_SLOTS['12'])}")
        table.append(
            "|".join(
                [
                    country["display"],
                    country["radar"],
                    country["cs"],
                    UAV_SLOTS["9"],
                    "10000",
                    UAV_SLOTS["10"],
                    "12000",
                    UAV_SLOTS["11"],
                    "10000",
                    UAV_SLOTS["12"],
                    "8000",
                    "YES" if all(live_slots.get(s) == UAV_SLOTS[s] for s in UAV_SLOTS) else "NO",
                    "YES" if all(zzzz_slots.get(s) == UAV_SLOTS[s] for s in UAV_SLOTS) else "NO",
                ]
            )
        )

    for item in COPIES:
        live_btn = catalog_block(live_cb, "CommandButton", item["cmd"])
        src_btn, packed_btn = last_from(packed_order, packed, "CommandButton", item["cmd"])
        src_obj, obj = last_from(packed_order, packed, "Object", item["copy"])
        img_src, img = last_from(packed_order, packed, "MappedImage", item["button"])
        if not live_btn:
            fails.append(f"LIVE CommandButton.ini missing {item['cmd']}")
        if field(live_btn, "Object") != item["copy"]:
            fails.append(f"LIVE {item['cmd']} -> {field(live_btn, 'Object')}")
        if field(live_btn, "Command") != "UNIT_BUILD":
            fails.append(f"LIVE {item['cmd']} not UNIT_BUILD")
        if field(live_btn, "ButtonImage") != item["button"]:
            fails.append(f"LIVE {item['cmd']} ButtonImage {field(live_btn, 'ButtonImage')}")
        if "SelectPortrait" in (live_btn or ""):
            fails.append(f"LIVE {item['cmd']} mixed SelectPortrait onto the button")
        if field(packed_btn, "Object") != item["copy"]:
            fails.append(f"PACKED {item['cmd']} -> {field(packed_btn, 'Object')}")
        if src_obj != OBJ_KEY:
            fails.append(f"{item['copy']} last-wins {src_obj}")
        if field(obj, "BuildCost") != item["cost"]:
            fails.append(f"{item['copy']} cost {field(obj, 'BuildCost')}")
        if field(obj, "Side") != item["side"]:
            fails.append(f"{item['copy']} Side {field(obj, 'Side')}")
        if field(obj, "DisplayName") != item["display"]:
            fails.append(f"{item['copy']} DisplayName {field(obj, 'DisplayName')}")
        if field(obj, "SelectPortrait") != item["button"]:
            fails.append(f"{item['copy']} SelectPortrait {field(obj, 'SelectPortrait')}")
        if field(obj, "ButtonImage") != item["button"]:
            fails.append(f"{item['copy']} object ButtonImage {field(obj, 'ButtonImage')}")
        orig_src, orig_blk = last_from(order, original, "Object", item["source"])
        new_src, new_blk = last_from(packed_order, packed, "Object", item["source"])
        if orig_src != new_src or orig_blk != new_blk:
            fails.append(f"source mutated {item['source']}")
        if models_of(obj) != models_of(orig_blk):
            fails.append(f"{item['copy']} models changed")
        if weapons_of(obj) != weapons_of(orig_blk):
            fails.append(f"{item['copy']} weapons changed")
        if field(obj, "KindOf") != field(orig_blk, "KindOf"):
            fails.append(f"{item['copy']} KindOf changed")
        if item["src_prereq"] and rad.prereq_has_objects(obj):
            fails.append(f"{item['copy']} still has object prerequisites")
        if not img:
            fails.append(f"MappedImage missing {item['button']}")
        src_cmd_src, src_cmd_blk = last_from(packed_order, packed, "CommandButton", item["src_cmd"])
        orig_cmd_src, orig_cmd_blk = last_from(order, original, "CommandButton", item["src_cmd"])
        if field(src_cmd_blk, "Object") != item["source"]:
            fails.append(f"{item['src_cmd']} retargeted")
        if orig_cmd_blk != src_cmd_blk:
            fails.append(f"{item['src_cmd']} mutated")
        for wpn in weapons_of(obj):
            wsrc, wblk = last_from(packed_order, packed, "Weapon", wpn)
            if not wblk:
                fails.append(f"missing weapon {wpn}")
            for proj in rad.projectile_names(wblk):
                psrc, pblk = last_from(packed_order, packed, "Object", proj)
                if not pblk:
                    fails.append(f"missing projectile {proj}")

    expect_mic = {item["slot"]: item["cmd"] for item in rad.COPIES}
    expect_mic["15"] = SELL
    for name in MIC_CS_NAMES:
        live_mic = slot_map(catalog_block(live_cs, "CommandSet", name))
        src_mic, packed_mic = last_from(packed_order, packed, "CommandSet", name)
        if live_mic != expect_mic:
            fails.append(f"LIVE MIC {name} {live_mic}")
        if slot_map(packed_mic) != expect_mic:
            fails.append(f"PACKED MIC {name} from {src_mic}")
    live_t3 = slot_map(catalog_block(live_cs, "CommandSet", WF_CS_NAME))
    src_t3, packed_t3 = last_from(packed_order, packed, "CommandSet", WF_CS_NAME)
    if live_t3.get("9") != "Command_ConstructIraqVehicleB340":
        fails.append("LIVE T3 missing B340")
    if live_t3.get("10") != "Command_ConstructIraq_Karrar2":
        fails.append("LIVE T3 missing Karrar2")
    if live_t3.get("12") != "Command_ConstructIraqVehicleFahad3":
        fails.append("LIVE T3 missing Fahad3")
    orig_t3 = slot_map(last_from(order, original, "CommandSet", WF_CS_NAME)[1])
    if slot_map(packed_t3) != orig_t3:
        fails.append("WF T3 slots changed")

    for name in UNRELATED_CS:
        orig_src, orig_blk = last_from(order, original, "CommandSet", name)
        new_src, new_blk = last_from(packed_order, packed, "CommandSet", name)
        if slot_map(orig_blk) != slot_map(new_blk):
            fails.append(f"unrelated CS mutated {name}")
        for cmd in UAV_SLOTS.values():
            if cmd in (new_blk or ""):
                fails.append(f"{name} gained UAV command")

    saudi_live = slot_map(catalog_block(live_cs, "CommandSet", "SaudiArabia_RadarCommandSet"))
    if saudi_live.get("2") != "Command_ConstructSaudiArabiaDroneMQ4":
        fails.append("Saudi slot 2 country MQ4 lost")
    if saudi_live.get("10") != UAV_SLOTS["10"]:
        fails.append("Saudi slot 10 is not USA Global Hawk copy")

    iraq_live = catalog_block(live_cs, "CommandSet", "Iraq_RadarStationCommandSet")
    if "Command_IraqiCamoflage" not in iraq_live or "Command_ConstructIraq_Sarab3" not in iraq_live:
        fails.append("Iraq radar lost country products")
    if "Command_ConstructIraq_Lamiaa" not in iraq_live:
        fails.append("Iraq radar lost Lamiaa")

    src_mic_obj, mic_obj = last_from(packed_order, packed, "Object", "Iraq_MIC")
    if field(mic_obj, "CommandSet") != "Iraq_MICCommandSet":
        fails.append("Iraq_MIC CommandSet pointer changed")
    src_karrar, karrar = last_from(packed_order, packed, "Object", "Iraq_Karrar2")
    if rad.prereq_has_objects(karrar):
        fails.append("Iraq_Karrar2 regained prerequisites")

    allowed = {CS_INI, CB_INI, CS_ZZZZ, CS_PAK, OBJ_KEY}
    for key in original:
        if key in allowed:
            continue
        if packed.get(key) != original[key]:
            fails.append(f"unrelated mutated {key}")

    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art1_path = OUT / "_SPEC_ART_ONE.big"
    art2_path = OUT / "_SPEC_ART_TWO.big"
    data_path.write_bytes(data_big)
    shutil.copy2(SRC_ART1, art1_path)
    shutil.copy2(SRC_ART2, art2_path)

    obj_loose = ROOT / "patch/Data/INI/Object/Specter/SpecterRadarUavs.ini"
    obj_loose.parent.mkdir(parents=True, exist_ok=True)
    obj_loose.write_bytes(files[OBJ_KEY])

    loose_cb = LOOSE / "CommandButton.ini"
    loose_cb.write_text(ensure_buttons(loose_cb.read_text(encoding="latin1")), encoding="latin1")
    for path in LOOSE_CS_FILES:
        if not path.exists():
            continue
        raw = path.read_bytes()
        crlf = b"\r\n" in raw
        text, patched = patch_text_commandsets(raw.decode("latin1"))
        if patched:
            if not text.endswith("\n"):
                text += "\n"
            encoded = text.replace("\n", "\r\n") if crlf else text
            path.write_bytes(encoded.encode("latin1"))

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "SLOT_TABLE.txt").write_text("\n".join(table) + "\n", encoding="utf-8")
    (ext / "CommandSet.ini.Iraq_RadarStationCommandSet.ini").write_text(
        catalog_block(live_cs, "CommandSet", "Iraq_RadarStationCommandSet") + "\n",
        encoding="utf-8",
    )
    (ext / "CommandSet.ini.SwedenGM406CommandSet.ini").write_text(
        catalog_block(live_cs, "CommandSet", "SwedenGM406CommandSet") + "\n",
        encoding="utf-8",
    )
    (ext / "CHANGED_CS_FILES.txt").write_text("\n".join(changed_cs_files) + "\n", encoding="utf-8")
    (ext / "GAMEPLAY_CHANGES.txt").write_text(
        "\n".join(
            [
                "Copy-only adaptations on SpecterRadar_* objects:",
                "1. BuildCost set to 10000 / 12000 / 10000 / 8000.",
                "2. SpecterRadar_Orlan10 Prerequisites emptied because the source",
                "   RussiaDroneOrlan10 requires Object=Russia91N6E, which the 18",
                "   target countries do not own. Required for buildability.",
                "No weapon, damage, speed, targeting, reload, KindOf, Side,",
                "DisplayName, model, or SelectPortrait changes.",
                "ButtonImage stays on the CommandButton; SelectPortrait stays on",
                "the object.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER RADAR UAV SLOTS — INSTALL",
                "",
                "Keep the split ART arrangement. Do not recombine ART.",
                "Place all three uncompressed BIGs next to generals.exe:",
                "  _SPEC_DATA_ONE.big",
                "  _SPEC_ART_ONE.big",
                "  _SPEC_ART_TWO.big",
                "",
                "Zero Hour auto-loads every *.big in that folder.",
                "Each .big must start with BIGF. Do not install gzip as .big.",
                "Replace any older SPECTER_IRAQ_MIC_MENU_FIX DATA file.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "18-country radar menus gain Heron / MQ-4 Global Hawk / Orlan-10 / "
        "Shahed-136 Mobile Launcher in slots 9-12 at $10000/$12000/$10000/$8000. "
        "ART unchanged. RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_RADAR_UAV_SLOTS.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "_SPEC_ART_TWO.big",
            "INSTALL.txt",
            "README.txt",
            "Launch_Specter.bat",
            "Install_SpecterPatch.bat",
        ):
            zf.write(OUT / name, name)

    if sha256_path(art1_path) != SHA_ART1_SRC or art1_path.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE copy is not byte-identical")
    if sha256_path(art2_path) != SHA_ART2_SRC or art2_path.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO copy is not byte-identical")
    if art1_path.stat().st_size >= SAGE_SAFE or art2_path.stat().st_size >= SAGE_SAFE:
        raise SystemExit("ART archive exceeds SAGE 2GiB signed offset limit")

    data_sha = sha256_path(data_path)
    art1_sha = sha256_path(art1_path)
    art2_sha = sha256_path(art2_path)
    zip_sha = sha256_path(zip_path)
    tag = "s-radar-uav-slots"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )
    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #665 SPECTER_IRAQ_MIC_MENU_FIX",
            "LIVE_CATALOG_PATCHED=CommandSet.ini+CommandButton.ini",
            "ZZZZ_PATCHED=CommandSet_ZZZZ_SpySatelliteRadar.ini",
            "ART_ONE_UNCHANGED=YES",
            "ART_TWO_UNCHANGED=YES",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_ONE_SIZE={art1_path.stat().st_size}",
            f"ART_ONE_SHA256={art1_sha}",
            f"ART_TWO_SIZE={art2_path.stat().st_size}",
            f"ART_TWO_SHA256={art2_sha}",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            f"CHANGED_PACKED_FILES={';'.join(sorted({CS_INI, CB_INI, CS_ZZZZ, CS_PAK, OBJ_KEY}))}",
            "MIC_LIVE_PRESERVED=YES",
            "WF_T3_LIVE_PRESERVED=YES",
            "SOURCE_UNITS_UNCHANGED=YES",
            "UNRELATED_COUNTRIES_UNCHANGED=YES",
            "ART_CHANGED=NO",
            "ORLAN_PREREQ_EMPTIED_ON_COPY_ONLY=YES",
            "RUNTIME_TEST=NOT RUN",
            "",
            *table,
            "",
            "GAMEPLAY_CHANGES:",
            "BuildCost on copies only. SpecterRadar_Orlan10 Prerequisites emptied",
            "(source required Russia91N6E). No weapon/damage/speed/targeting changes.",
            "",
        ]
    )
    (OUT / "VALIDATE_REPORT.txt").write_text(report, encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "\n".join(
            [
                "DATA_CHANGED=YES",
                "ART_CHANGED=NO",
                f"DATA_SIZE={data_path.stat().st_size}",
                f"DATA_SHA256={data_sha}",
                f"ART_ONE_SIZE={art1_path.stat().st_size}",
                f"ART_ONE_SHA256={art1_sha}",
                f"ART_TWO_SIZE={art2_path.stat().st_size}",
                f"ART_TWO_SHA256={art2_sha}",
                "ZIP_FILE=SPECTER_RADAR_UAV_SLOTS.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #665",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA:",
                f"  {rel_base}/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART textures (unchanged from PR #665 / tag s-iraq-mic-menu-fix):",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-mic-menu-fix/_SPEC_ART_ONE.big",
                f"  SIZE={art1_path.stat().st_size}",
                f"  SHA256={art1_sha}",
                "",
                "ART models (unchanged from PR #665 / tag s-iraq-mic-menu-fix):",
                "  https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/s-iraq-mic-menu-fix/_SPEC_ART_TWO.big",
                f"  SIZE={art2_path.stat().st_size}",
                f"  SHA256={art2_sha}",
                "",
                "ZIP:",
                f"  {rel_base}/SPECTER_RADAR_UAV_SLOTS.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                f"TAG={tag}",
                f"RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/{tag}",
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "\n".join(
            [
                "# 18-country radar UAV / launcher slots 9-12",
                "",
                "Adds dedicated copies of Israel Heron, USA MQ-4 Global Hawk,",
                "Russia Orlan-10, and Iran Shahed-136 Mobile Launcher to the",
                "radar production menus of 18 SPECTER countries at",
                "$10,000 / $12,000 / $10,000 / $8,000.",
                "",
                "Live catalogs CommandSet.ini and CommandButton.ini are patched",
                "alongside CommandSet_ZZZZ_SpySatelliteRadar.ini last-wins.",
                "Original source-country units are unchanged. Iraq M.I.C. and",
                "War Factory T3 menus are frozen.",
                "",
                "ART_ONE and ART_TWO are byte-identical to PR #665.",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("PACKED", data_path.stat().st_size, data_sha)
    print("ART_ONE", art1_path.stat().st_size, art1_sha)
    print("ART_TWO", art2_path.stat().st_size, art2_sha)
    print("ZIP", zip_path.stat().st_size, zip_sha)
    print("CHANGED_CS_FILES")
    print("\n".join(changed_cs_files))
    print("\n".join(table))
    print("STATIC VALIDATION: PASS")
    print("RUNTIME_TEST=NOT RUN")


if __name__ == "__main__":
    main()
