#!/usr/bin/env python3
"""Populate Iraq M.I.C. slots 1-14 with copies of existing radar/AD objects.

Baseline packed archives: SPECTER_IRAQ_MIC_EMPTY (PR #663).
ART_ONE / ART_TWO are copied byte-identical. DATA last-wins overlay only.

Copy-only: original country objects, buttons, and CommandSets stay intact.
Iraq copies get dedicated Object + UNIT_BUILD names and the requested BuildCost.
Sell moves to slot 15 so slot 14 can hold THAAD.
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
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MIC_EMPTY/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_EMPTY/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_IRAQ_MIC_EMPTY/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MIC_RADAR_AD"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "4384ff901971b9710160cfdb00f356db169fd3f415a0e6cd2413bd61b2d93c35"
SIZE_DATA_SRC = 370746678
SHA_ART1_SRC = "dd53835d7119e7609d2bd955879f234da83a0c6c650d7d7ed1194385d9bbd0f2"
SIZE_ART1_SRC = 2144061050
SHA_ART2_SRC = "daf5e3bb3d4b0f763fee4bd39ceafa06000b9c7261f538a0e84a7b6b54fb7f21"
SIZE_ART2_SRC = 307234369
SAGE_SAFE = 2147483648

# Must sort after CommandSet_ZZZZ_IraqMicToWfEmpty.ini (Empty < RadarAd).
CS_KEY = r"Data\INI\CommandSet_ZZZZ_IraqMicToWfRadarAd.ini"
CB_KEY = r"Data\INI\CommandButton_ZZZZ_IraqMicRadarAd.ini"
OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\AirDefense\Iraq_MIC_RadarAdCopies.ini"
EMPTY_CS_KEY = r"Data\INI\CommandSet_ZZZZ_IraqMicToWfEmpty.ini"
TOWF_KEY = r"Data\INI\CommandSet_ZZZZ_IraqMicToWf.ini"
KARRAR_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Karrar-2.ini"
MIC_OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_MIC.ini"
WF_OBJ_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini"
AA_WF_KEY = r"Data\INI\Object\Specter\Arabic Alliance\Buildings\Warfactory.ini"

MIC_CS_NAMES = (
    "Iraq_MICCommandSet",
    "Iraq_MICCommandSet2",
    "Iraq_MICCommandSet3",
)
WF_CS_NAME = "Iraq_WarFactoryCommandSet_T3"
IRAQ_DOZER_CS = "Iraq_VT72BCommandSet"
MIC_CONSTRUCT = "Command_ConstructIraq_MIC"
SELL = "Command_Sell"
OLD_UPGRADES = (
    "Command_UpgradeIraq_AlAbbas",
    "Command_UpgradeIraq_BMP-2M2",
    "Command_UpgradeIraq_AlHussien",
    "Command_UpgradeIraq_S-8",
    "Command_UpgradeIraq_BMP-1M3",
    "Command_UpgradeIraq_Irq_Tier1",
    "Command_UpgradeIraq_Irq_Tier2",
    "Command_UpgradeIraq_Irq_Tier3",
    "Command_UpgradeIraq_Mi35Mk3",
    "Command_UpgradeIraq_Kab500",
)
MOVE_CMDS = (
    "Command_ConstructIraqVehicleB340",
    "Command_ConstructIraq_Karrar2",
    "Command_ConstructIraqVehicleFahad3",
)
MOVE_OBJS = {
    "Command_ConstructIraqVehicleB340": "IraqVehicleB340",
    "Command_ConstructIraq_Karrar2": "Iraq_Karrar2",
    "Command_ConstructIraqVehicleFahad3": "IraqVehicleFahad3",
}

# Packed last-wins audit (PR #663 DATA). Display names describe the request;
# INI identifiers were resolved from the archive, not assumed.
COPIES = [
    {
        "slot": "1",
        "country": "Israel",
        "source": "Israel_Arrow",
        "src_cmd": "Command_ConstructIsrael_Arrow",
        "src_cs": "AirF_AmericaWarFactoryCommandSet",
        "copy": "Iraq_MIC_Arrow",
        "cmd": "Command_ConstructIraq_MIC_Arrow",
        "cost": "8000",
        "src_cost": "3200",
        "button": "isi_arrow",
        "label": "CONTROLBAR:ConstructIsrael_Arrow",
        "tip": "CONTROLBAR:ToolTipIsrael_Arrow",
        "src_prereq": "AirF_AmericaStrategyCenter",
    },
    {
        "slot": "2",
        "country": "Israel",
        "source": "Israel_AN_TPY2",
        "src_cmd": "Command_ConstructIsrael_AN_TPY2",
        "src_cs": "AirF_AmericaWarFactoryCommandSet",
        "copy": "Iraq_MIC_AN_TPY2",
        "cmd": "Command_ConstructIraq_MIC_AN_TPY2",
        "cost": "6000",
        "src_cost": "2600",
        "button": "isi_tpy2",
        "label": "CONTROLBAR:ConstructIsrael_AN_TPY2",
        "tip": "CONTROLBAR:ToolTipIsrael_AN_TPY2",
        "src_prereq": "AirF_AmericaStrategyCenter",
    },
    {
        "slot": "3",
        "country": "Russia",
        "source": "RussiaVehicle92N6R",
        "src_cmd": "Command_ConstructRussiaVehicle92N6R",
        "src_cs": "RussiaWarFactoryCommandSet",
        "copy": "Iraq_MIC_92N6R",
        "cmd": "Command_ConstructIraq_MIC_92N6R",
        "cost": "6000",
        "src_cost": "2200",
        "button": "rus_92n6r",
        "label": "CONTROLBAR:ConstructRussiaVehicle92N6R",
        "tip": "CONTROLBAR:ToolTipRussiaVehicle92N6R",
        "src_prereq": "RussiaWarFactory",
    },
    {
        "slot": "4",
        "country": "Russia",
        "source": "RussiaVehicleS400",
        "src_cmd": "Command_ConstructRussiaVehicleS400",
        "src_cs": "RussiaWarFactoryCommandSet",
        "copy": "Iraq_MIC_S400",
        "cmd": "Command_ConstructIraq_MIC_S400",
        "cost": "8000",
        "src_cost": "3200",
        "button": "rus_s400r",
        "label": "CONTROLBAR:ConstructRussiaVehicleS400",
        "tip": "CONTROLBAR:ToolTipRussiaVehicleS400",
        "src_prereq": "RussiaWarFactory",
    },
    {
        "slot": "5",
        "country": "Russia",
        "source": "RussiaVehiclePantsirS1M",
        "src_cmd": "Command_ConstructRussiaVehiclePantsirS1M",
        "src_cs": "RussiaWarFactoryCommandSet",
        "copy": "Iraq_MIC_PantsirS1M",
        "cmd": "Command_ConstructIraq_MIC_PantsirS1M",
        "cost": "4000",
        "src_cost": "800",
        "button": "rus_pantsirs1m",
        "label": "CONTROLBAR:ConstructRussiaVehiclePantsirS1M",
        "tip": "CONTROLBAR:ToolTipRussiaVehiclePantsirS1M",
        "src_prereq": "",
    },
    {
        "slot": "6",
        "country": "Russia",
        "source": "RussiaVehicleKrasukha4",
        "src_cmd": "Command_ConstructRussiaVehicleKrasukha4",
        "src_cs": "RussiaWarFactoryCommandSet",
        "copy": "Iraq_MIC_Krasukha4",
        "cmd": "Command_ConstructIraq_MIC_Krasukha4",
        "cost": "12000",
        "src_cost": "5000",
        "button": "rus_krasukha4",
        "label": "CONTROLBAR:ConstructRussiaVehicleKrasukha4",
        "tip": "CONTROLBAR:ToolTipRussiaVehicleKrasukha4",
        "src_prereq": "RussiaWarFactory",
    },
    {
        "slot": "7",
        "country": "Russia",
        "source": "RussiaVehicle96L6TSP",
        "src_cmd": "Command_ConstructRussiaVehicle96L6TSP",
        "src_cs": "RussiaIndsturialComplexCommandSet",
        "copy": "Iraq_MIC_96L6TSP",
        "cmd": "Command_ConstructIraq_MIC_96L6TSP",
        "cost": "15000",
        "src_cost": "5000",
        "button": "rus_96l6tsp",
        "label": "CONTROLBAR:ConstructRussiaVehicle96L6TSP",
        "tip": "CONTROLBAR:ToolTipRussiaVehicle96L6TSP",
        "src_prereq": "RussiaIndustrialComplex + SCIENCE_Rank6",
    },
    {
        "slot": "8",
        "country": "Russia",
        "source": "RussiaVehicleS500",
        "src_cmd": "Command_ConstructRussiaVehicleS500",
        "src_cs": "RussiaIndsturialComplexCommandSet",
        "copy": "Iraq_MIC_S500",
        "cmd": "Command_ConstructIraq_MIC_S500",
        "cost": "15000",
        "src_cost": "6000",
        # Source production button last-wins rus_s400r (S400 art). Object
        # portrait is RUS_S500r; MappedImage rus_s500 exists and matches identity.
        "button": "rus_s500",
        "label": "CONTROLBAR:ConstructRussiaVehicleS500",
        "tip": "CONTROLBAR:ToolTipRussiaVehicleS500",
        "src_prereq": "RussiaIndustrialComplex",
    },
    {
        "slot": "9",
        "country": "China",
        "source": "ChinaVehicleHQ9",
        "src_cmd": "Command_ConstructChinaVehicleHQ9",
        "src_cs": "PLAWarFactoryCommandSet",
        "copy": "Iraq_MIC_HQ9",
        "cmd": "Command_ConstructIraq_MIC_HQ9",
        "cost": "8000",
        "src_cost": "3200",
        "button": "pla_hq9b",
        "label": "CONTROLBAR:ConstructChinaVehicleHQ9",
        "tip": "CONTROLBAR:ToolTipChinaVehicleHQ9",
        "src_prereq": "ChinaWarFactory",
    },
    {
        "slot": "10",
        "country": "China",
        "source": "ChinaVehicleHT233",
        "src_cmd": "Command_ConstructChinaVehicleHT233",
        "src_cs": "PLAWarFactoryCommandSet",
        "copy": "Iraq_MIC_HT233",
        "cmd": "Command_ConstructIraq_MIC_HT233",
        "cost": "5000",
        "src_cost": "2200",
        "button": "pla_ht233",
        "label": "CONTROLBAR:ConstructChinaVehicleHT233",
        "tip": "CONTROLBAR:ToolTipChinaVehicleHT233",
        "src_prereq": "ChinaWarFactory",
    },
    {
        "slot": "11",
        "country": "NATO",
        "source": "NatoVehicleTRML4D",
        "src_cmd": "Command_ConstructNatoVehicleTRML4D",
        "src_cs": "NatoWarfactoryCommandSet",
        "copy": "Iraq_MIC_TRML4D",
        "cmd": "Command_ConstructIraq_MIC_TRML4D",
        "cost": "5000",
        "src_cost": "2200",
        "button": "Nat_trml4d",
        "label": "CONTROLBAR:ConstructNatoVehicleTRML4D",
        "tip": "CONTROLBAR:ToolTipNatoVehicleTRML4D",
        "src_prereq": "NatoStrategyCenter",
    },
    {
        "slot": "12",
        "country": "NATO",
        "source": "NatoVehicleIRIST",
        "src_cmd": "Command_ConstructNatoVehicleIRIST",
        "src_cs": "NatoWarfactoryCommandSet",
        "copy": "Iraq_MIC_IRIST",
        "cmd": "Command_ConstructIraq_MIC_IRIST",
        "cost": "7000",
        "src_cost": "1700",
        "button": "Nat_irist",
        "label": "CONTROLBAR:ConstructNatoVehicleIRIST",
        "tip": "CONTROLBAR:ToolTipNatoVehicleIRIST",
        "src_prereq": "NatoStrategyCenter",
    },
    {
        "slot": "13",
        "country": "USA",
        "source": "US_AN_TPY2",
        "src_cmd": "Command_ConstructAmericaVehicleAN_TPY2",
        "src_cs": "AmericaWarFactoryCommandSet",
        "copy": "Iraq_MIC_US_AN_TPY2",
        "cmd": "Command_ConstructIraq_MIC_US_AN_TPY2",
        "cost": "10000",
        "src_cost": "2600",
        "button": "us_tpy2",
        "label": "CONTROLBAR:ConstructAmericatpy2",
        "tip": "CONTROLBAR:ToolTipUSABuildtpy2",
        "src_prereq": "",
    },
    {
        "slot": "14",
        "country": "USA",
        "source": "US_THAAD",
        "src_cmd": "Command_ConstructAmericaVehicleTHAAD",
        "src_cs": "AmericaWarFactoryCommandSet",
        "copy": "Iraq_MIC_THAAD",
        "cmd": "Command_ConstructIraq_MIC_THAAD",
        "cost": "15000",
        "src_cost": "3000",
        "button": "us_thaad",
        "label": "CONTROLBAR:ConstructAmericathaad",
        "tip": "CONTROLBAR:ToolTipUSABuildthaad",
        "src_prereq": "AmericaStrategyCenter AmericaStrategyCenter_T",
    },
]

PREREQ_RE = re.compile(
    r"(?ms)^([ \t]*)Prerequisites[ \t]*\r?\n"
    r"(?:[ \t]*(?:Object[ \t]*=[^\r\n]+|Science[ \t]*=[^\r\n]+|;[^\r\n]*)\r?\n)+"
    r"[ \t]*End[ \t]*\r?$"
)
SLOT_RE = re.compile(r"(?m)^[ \t]*(\d+)[ \t]*=[ \t]*(\S+)")
WEAPON_SLOTS = {"PRIMARY", "SECONDARY", "TERTIARY"}
FROZEN = [
    EMPTY_CS_KEY,
    TOWF_KEY,
    MIC_OBJ_KEY,
    WF_OBJ_KEY,
    AA_WF_KEY,
    KARRAR_KEY,
    r"Data\INI\CommandButton.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\Object\Specter\Iraq Army\AirDefense\B340.ini",
    r"Data\INI\Object\Specter\Iraq Army\AirDefense\Fahad3.ini",
    r"Data\INI\Object\Specter\Israel Defense Forces\Airdefense\Arrow.ini",
    r"Data\INI\Object\Specter\Israel Defense Forces\Airdefense\AN_TPY2.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\92N6R.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\S400.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\Pantsir.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Wheeled\Krasukha-4.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\96L6TSP.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\AirDefense\S500.ini",
    r"Data\INI\Object\Specter\PLA\AirDefense\HQ9B.ini",
    r"Data\INI\Object\Specter\PLA\AirDefense\HT233.ini",
    r"Data\INI\Object\Specter\NATO\Airdefense\TRML4D.ini",
    r"Data\INI\Object\Specter\NATO\Airdefense\IRIST_SLX.ini",
    r"Data\INI\Object\Specter\United States Of America\AirDefense\US_AN_TPY2.ini",
    r"Data\INI\Object\Specter\United States Of America\AirDefense\US_M1120.ini",
]


def last_from(order, files, kind, name):
    return sk.last_block_from_files(order, files, kind, name)


def field(block: str, key: str) -> str:
    return sk.field(block, key)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def slot_map(block: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in SLOT_RE.finditer(block or "")}


def prereq_block(block: str) -> str:
    m = re.search(r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", block or "")
    return m.group(0) if m else ""


def prereq_has_objects(block: str) -> bool:
    body = "\n".join(
        m.group(0)
        for m in re.finditer(
            r"(?ms)^\s*Prerequisites\s*\r?\n.*?(?:^\s*End)\s*$", block or ""
        )
    )
    return bool(re.search(r"(?m)^\s*(?:Object|Science)\s*=", body))


def weapon_names(block: str) -> list[str]:
    found = []
    for m in re.finditer(r"(?m)^\s*Weapon\s*=\s+(.+?)\s*$", block or ""):
        parts = [p for p in m.group(1).split() if not p.startswith(";")]
        if not parts:
            continue
        if parts[0].upper() in WEAPON_SLOTS:
            if len(parts) > 1:
                found.append(parts[1])
        else:
            found.append(parts[0])
    return found


def clone_object(src_block: str, item: dict) -> str:
    lines = src_block.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines or not re.match(rf"Object\s+{re.escape(item['source'])}\s*$", lines[0]):
        raise SystemExit(f"unexpected object header for {item['source']}: {lines[0]!r}")
    note = (
        f"; SPECTER Iraq M.I.C. copy of {item['source']}. "
        f"Adaptations: Side=Iraq; BuildCost={item['cost']}; "
        f"Prerequisites emptied"
    )
    if item["src_prereq"]:
        note += f" (source required {item['src_prereq']})"
    note += "."
    lines[0] = f"Object {item['copy']}"
    text = "\n".join(lines)
    text = re.sub(r"(?m)^(\s*Side\s*=\s*)\S+", r"\1Iraq", text, count=1)
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


def make_commandset(name: str) -> str:
    lines = [f"CommandSet {name}"]
    for item in COPIES:
        lines.append(f"  {item['slot']} = {item['cmd']}")
    lines.append(f"  15 = {SELL}")
    lines.append("End")
    return "\n".join(lines) + "\n"


def projectile_names(weapon_block: str) -> list[str]:
    names = []
    for key in ("ProjectileObject", "ProjectileNugget"):
        for m in re.finditer(rf"(?m)^\s*{key}\s*=\s*(\S+)", weapon_block or ""):
            val = m.group(1)
            if val and not val.startswith(";"):
                names.append(val)
    return names


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_IRAQ_MIC_EMPTY")
    if sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline mismatch")
    if sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline mismatch")

    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)

    obj_parts = []
    btn_parts = []
    src_blocks = {}
    for item in COPIES:
        src_file, src_blk = last_from(order, files, "Object", item["source"])
        if not src_blk:
            raise SystemExit(f"missing source object {item['source']}")
        if field(src_blk, "BuildCost") != item["src_cost"]:
            raise SystemExit(
                f"{item['source']} BuildCost {field(src_blk, 'BuildCost')} != {item['src_cost']}"
            )
        src_blocks[item["source"]] = (src_file, src_blk)
        obj_parts.append(clone_object(src_blk, item))
        btn_parts.append(make_button(item))
        _, exist_copy = last_from(order, files, "Object", item["copy"])
        if exist_copy:
            raise SystemExit(f"copy object already exists: {item['copy']}")
        _, exist_cmd = last_from(order, files, "CommandButton", item["cmd"])
        if exist_cmd:
            raise SystemExit(f"copy command already exists: {item['cmd']}")

    cs_text = "".join(make_commandset(n) for n in MIC_CS_NAMES)
    files[OBJ_KEY] = sk.to_crlf("\n".join(obj_parts) + "\n")
    files[CB_KEY] = sk.to_crlf("\n".join(btn_parts) + "\n")
    files[CS_KEY] = sk.to_crlf(cs_text)

    if CS_KEY.lower() <= EMPTY_CS_KEY.lower():
        raise SystemExit(f"{CS_KEY} does not sort after {EMPTY_CS_KEY}")

    for key in FROZEN:
        if files.get(key) != original.get(key):
            raise SystemExit(f"frozen mutated: {key}")

    data_big = sk.build_big(files)
    packed, packed_order = sk.parse_big_ordered(data_big)

    fails = []
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))

    src_dozer, dozer = last_from(packed_order, packed, "CommandSet", IRAQ_DOZER_CS)
    src_mic_obj, mic_obj = last_from(packed_order, packed, "Object", "Iraq_MIC")
    src_wf_obj, wf_obj = last_from(packed_order, packed, "Object", "Iraq_WarFactory_T")
    src_wf_cs, wf_cs = last_from(packed_order, packed, "CommandSet", WF_CS_NAME)
    src_karrar, karrar = last_from(packed_order, packed, "Object", "Iraq_Karrar2")
    src_aa, aa_obj = last_from(packed_order, packed, "Object", "ArabicArmy_WarFactory")

    expected_slots = {item["slot"]: item["cmd"] for item in COPIES}
    expected_slots["15"] = SELL
    for name in MIC_CS_NAMES:
        src, blk = last_from(packed_order, packed, "CommandSet", name)
        if src != CS_KEY:
            fails.append(f"{name} last-wins {src}")
        slots = slot_map(blk)
        if slots != expected_slots:
            fails.append(f"{name} slots {slots}")
        if slots.get("14") != "Command_ConstructIraq_MIC_THAAD":
            fails.append(f"{name} slot 14 is not THAAD")
        if slots.get("15") != SELL:
            fails.append(f"{name} Sell is not slot 15")
        if SELL in {slots.get(str(i)) for i in range(1, 15)}:
            fails.append(f"{name} Sell overwrote a production slot")
        for old in OLD_UPGRADES + MOVE_CMDS:
            if old in blk:
                fails.append(f"{name} regained {old}")

    if src_wf_cs != TOWF_KEY:
        fails.append(f"{WF_CS_NAME} last-wins {src_wf_cs}")
    wf_slots = slot_map(wf_cs)
    if wf_slots.get("9") != "Command_ConstructIraqVehicleB340":
        fails.append("WF lost B340")
    if wf_slots.get("10") != "Command_ConstructIraq_Karrar2":
        fails.append("WF lost Karrar2")
    if wf_slots.get("12") != "Command_ConstructIraqVehicleFahad3":
        fails.append("WF lost Fahad3")
    orig_wf = last_from(order, original, "CommandSet", WF_CS_NAME)[1]
    if slot_map(orig_wf) != wf_slots:
        fails.append("WF T3 slots changed")

    for cmd, obj in MOVE_OBJS.items():
        _, btn = last_from(packed_order, packed, "CommandButton", cmd)
        if field(btn, "Command") != "UNIT_BUILD" or field(btn, "Object") != obj:
            fails.append(f"{cmd} button broken")

    if prereq_has_objects(karrar):
        fails.append("Iraq_Karrar2 regained object prerequisites")
    if re.search(r"(?ms)Prerequisites\s*\r?\n.*?Iraq_MIC", karrar or ""):
        fails.append("Iraq_Karrar2 still depends on Iraq_MIC")
    if field(karrar, "BuildCost") != "2200":
        fails.append("Iraq_Karrar2 BuildCost changed")

    if field(mic_obj, "CommandSet") != "Iraq_MICCommandSet":
        fails.append("Iraq_MIC CommandSet pointer changed")
    if "Irq_MIC" not in (mic_obj or ""):
        fails.append("Iraq_MIC model lost")
    if prereq_has_objects(mic_obj):
        fails.append("Iraq_MIC regained object prerequisites")
    dozer_slots = slot_map(dozer)
    if dozer_slots.get("6") != MIC_CONSTRUCT:
        fails.append(f"Iraq dozer slot 6 is {dozer_slots.get('6')}")
    if field(wf_obj, "CommandSet") != WF_CS_NAME:
        fails.append("Iraq_WarFactory_T CommandSet changed")
    if src_mic_obj != MIC_OBJ_KEY:
        fails.append(f"Iraq_MIC last-wins {src_mic_obj}")
    if src_karrar != KARRAR_KEY:
        fails.append(f"Iraq_Karrar2 last-wins {src_karrar}")

    aa_prereq = prereq_block(aa_obj)
    if aa_prereq and "Iraq_" in aa_prereq:
        fails.append("Arabic Alliance War Factory gained Iraq prereq")

    for item in COPIES:
        src, blk = last_from(packed_order, packed, "Object", item["copy"])
        if src != OBJ_KEY:
            fails.append(f"{item['copy']} last-wins {src}")
        if field(blk, "BuildCost") != item["cost"]:
            fails.append(f"{item['copy']} cost {field(blk, 'BuildCost')}")
        if field(blk, "Side") != "Iraq":
            fails.append(f"{item['copy']} Side {field(blk, 'Side')}")
        if prereq_has_objects(blk):
            fails.append(f"{item['copy']} still has object prerequisites")
        if field(blk, "DisplayName") != field(src_blocks[item["source"]][1], "DisplayName"):
            fails.append(f"{item['copy']} DisplayName changed")
        _, btn = last_from(packed_order, packed, "CommandButton", item["cmd"])
        btn_src, _ = last_from(packed_order, packed, "CommandButton", item["cmd"])
        if btn_src != CB_KEY:
            fails.append(f"{item['cmd']} last-wins {btn_src}")
        if field(btn, "Command") != "UNIT_BUILD":
            fails.append(f"{item['cmd']} is not UNIT_BUILD")
        if field(btn, "Object") != item["copy"]:
            fails.append(f"{item['cmd']} points at {field(btn, 'Object')}")
        if field(btn, "ButtonImage") != item["button"]:
            fails.append(f"{item['cmd']} art {field(btn, 'ButtonImage')}")
        img_src, img = last_from(packed_order, packed, "MappedImage", item["button"])
        if not img:
            fails.append(f"MappedImage missing {item['button']}")

        # Source object and source production command unchanged.
        osrc, oblk = last_from(packed_order, packed, "Object", item["source"])
        orig_src, orig_blk = last_from(order, original, "Object", item["source"])
        if osrc != orig_src or oblk != orig_blk:
            fails.append(f"source object mutated {item['source']}")
        if field(oblk, "BuildCost") != item["src_cost"]:
            fails.append(f"source cost changed {item['source']}")
        csrc, cblk = last_from(packed_order, packed, "CommandButton", item["src_cmd"])
        orig_c, orig_cblk = last_from(order, original, "CommandButton", item["src_cmd"])
        if csrc != orig_c or cblk != orig_cblk:
            fails.append(f"source command mutated {item['src_cmd']}")
        if field(cblk, "Object") != item["source"]:
            fails.append(f"{item['src_cmd']} no longer builds {item['source']}")
        cssrc, csblk = last_from(packed_order, packed, "CommandSet", item["src_cs"])
        orig_cs, orig_csblk = last_from(order, original, "CommandSet", item["src_cs"])
        if cssrc != orig_cs or csblk != orig_csblk:
            fails.append(f"source CommandSet mutated {item['src_cs']}")
        if item["src_cmd"] not in (csblk or ""):
            fails.append(f"{item['src_cs']} lost {item['src_cmd']}")

        # Text-resolve selected CommandSet, weapons, upgrades.
        unit_cs = field(blk, "CommandSet")
        if unit_cs:
            _, unit_cs_blk = last_from(packed_order, packed, "CommandSet", unit_cs)
            if not unit_cs_blk:
                fails.append(f"{item['copy']} CommandSet missing {unit_cs}")
        for wep in weapon_names(blk):
            _, wblk = last_from(packed_order, packed, "Weapon", wep)
            if not wblk:
                fails.append(f"{item['copy']} weapon missing {wep}")
            for proj in projectile_names(wblk or ""):
                _, pblk = last_from(packed_order, packed, "Object", proj)
                if not pblk:
                    fails.append(f"{item['copy']} projectile missing {proj}")
        for upg in re.findall(r"(?m)^\s*TriggeredBy\s*=\s*(\S+)", blk):
            _, ublk = last_from(packed_order, packed, "Upgrade", upg)
            if not ublk:
                fails.append(f"{item['copy']} upgrade missing {upg}")

    for name in (
        "NorthKorea_MICCommandSet",
        "SouthKorea_MICCommandSet",
        "Japan_MICCommandSet",
    ):
        src, blk = last_from(packed_order, packed, "CommandSet", name)
        orig = last_from(order, original, "CommandSet", name)[1]
        if blk != orig:
            fails.append(f"other-country {name} mutated")

    allowed = {CS_KEY, CB_KEY, OBJ_KEY}
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

    (LOOSE / "CommandSet_ZZZZ_IraqMicToWfRadarAd.ini").write_bytes(files[CS_KEY])
    (LOOSE / "CommandButton_ZZZZ_IraqMicRadarAd.ini").write_bytes(files[CB_KEY])
    obj_loose = (
        ROOT
        / "patch/Data/INI/Object/Specter/Iraq Army/AirDefense/Iraq_MIC_RadarAdCopies.ini"
    )
    obj_loose.parent.mkdir(parents=True, exist_ok=True)
    obj_loose.write_bytes(files[OBJ_KEY])

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    for name in MIC_CS_NAMES:
        _, blk = last_from(packed_order, packed, "CommandSet", name)
        (ext / f"{name}.ini").write_text(blk + "\n", encoding="utf-8")
    (ext / f"{WF_CS_NAME}.ini").write_text(wf_cs + "\n", encoding="utf-8")
    (ext / "Iraq_MIC_RadarAdCopies.ini").write_bytes(files[OBJ_KEY])
    (ext / "CommandButton_IraqMicRadarAd.ini").write_bytes(files[CB_KEY])
    table_lines = [
        "slot|country|source_object|iraq_copy|cost|button|src_cmd|validation",
    ]
    for item in COPIES:
        table_lines.append(
            f"{item['slot']}|{item['country']}|{item['source']}|{item['copy']}|"
            f"{item['cost']}|{item['button']}|{item['src_cmd']}|STATIC_PASS"
        )
    (ext / "SLOT_TABLE.txt").write_text("\n".join(table_lines) + "\n", encoding="utf-8")

    (OUT / "INSTALL.txt").write_text(
        "\n".join(
            [
                "SPECTER IRAQ M.I.C. RADAR/AIR-DEFENSE COPIES — INSTALL",
                "",
                "Keep the split ART arrangement. Do not recombine ART.",
                "Place all three uncompressed BIGs next to generals.exe:",
                "  _SPEC_DATA_ONE.big",
                "  _SPEC_ART_ONE.big",
                "  _SPEC_ART_TWO.big",
                "",
                "Zero Hour auto-loads every *.big in that folder.",
                "Each .big must start with BIGF. Do not install gzip as .big.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "Iraq_MICCommandSet slots 1-14 produce dedicated Iraq copies of "
        "Israel/Russia/China/NATO/US radar and air-defense vehicles. "
        "Sell is slot 15. Original country objects and menus are unchanged. "
        "B340, Karrar-2, and Fahad-3 stay on Iraq War Factory T3.\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_IRAQ_MIC_RADAR_AD.zip"
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
    tag = "s-iraq-mic-radar-ad"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )

    adaptations = [
        "ADAPTATIONS (Iraq copies only; originals unchanged):",
        "- Side rewritten to Iraq on every copy.",
        "- BuildCost set to the requested Iraq M.I.C. price.",
        "- Country-specific Prerequisites emptied so MIC production is not gated",
        "  on Israel/Russia/China/NATO/US buildings.",
        "- Iraq_MIC_96L6TSP also drops SCIENCE_Rank6 (source second Prerequisites).",
        "- CombatMode/PackMode/FireControl companion objects stay shared by name.",
        "- Source weapons, projectiles, models, and selected-unit CommandSets reused.",
        "- Slot 8 button uses MappedImage rus_s500 (source UNIT_BUILD last-wins",
        "  rus_s400r; object portrait RUS_S500r).",
        "- Sell is slot 15 (project already uses 15+; slot 14 is THAAD).",
    ]
    report = "\n".join(
        [
            "STATIC VALIDATION: PASS",
            "RUNTIME_TEST=NOT RUN",
            "BASELINE: PR #663 SPECTER_IRAQ_MIC_EMPTY",
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
            f"CHANGED_PACKED_FILES={CS_KEY};{CB_KEY};{OBJ_KEY}",
            "MIC_SLOTS=1-14_COPIES_SELL_15",
            "WF_TRANSFER_PRESERVED=YES",
            "KARRAR2_MIC_PREREQ=REMOVED",
            "MIC_START_GAME_PRESERVED=YES",
            "SOURCE_MENUS_PRESERVED=YES",
            "ART_CHANGED=NO",
            "WEAPON_PROJECTILE_RESOLVE=TEXT_ONLY",
            "MODEL_RESOLVE=INHERITED_FROM_SOURCE_TEXT",
            "RUNTIME_TEST=NOT RUN",
            "",
            *table_lines,
            "",
            *adaptations,
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
                "ZIP_FILE=SPECTER_IRAQ_MIC_RADAR_AD.zip",
                f"ZIP_SIZE={zip_path.stat().st_size}",
                f"ZIP_SHA256={zip_sha}",
                "BASELINE=PR #663",
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
                "ART textures (unchanged):",
                f"  {rel_base}/_SPEC_ART_ONE.big",
                f"  SIZE={art1_path.stat().st_size}",
                f"  SHA256={art1_sha}",
                "",
                "ART models (unchanged):",
                f"  {rel_base}/_SPEC_ART_TWO.big",
                f"  SIZE={art2_path.stat().st_size}",
                f"  SHA256={art2_sha}",
                "",
                "ZIP:",
                f"  {rel_base}/SPECTER_IRAQ_MIC_RADAR_AD.zip",
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
                "# Iraq M.I.C. radar and air-defense copies",
                "",
                "Iraq M.I.C. slots 1-14 produce dedicated Iraq copies of existing",
                "Israeli, Russian, Chinese, NATO, and US radar/air-defense vehicles.",
                "Sell is slot 15. Original country objects and production menus are",
                "unchanged. M.I.C. stays start-buildable. War Factory T3 still has",
                "B340, Karrar-2, and Fahad-3.",
                "",
                "ART_ONE and ART_TWO are byte-identical to PR #663.",
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
    _, mic_cs = last_from(packed_order, packed, "CommandSet", "Iraq_MICCommandSet")
    print("MIC")
    print(mic_cs)
    print("WF")
    print(wf_cs)
    print("\n".join(table_lines))
    print("STATIC VALIDATION: PASS")
    print("RUNTIME_TEST=NOT RUN")


if __name__ == "__main__":
    main()
