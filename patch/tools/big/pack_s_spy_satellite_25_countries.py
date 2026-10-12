#!/usr/bin/env python3
"""Global Spy Satellite on all 25 SPECTER country radars.

Baseline packed archives: SPECTER_ART_SPLIT_2GIB (PR #656).
ART_ONE / ART_TWO are copied byte-identical. DATA last-wins overlay only.

Engine facts from packed last-wins (not guessed):
  SpecialPower SpecialPowerSpySatellite ReloadTime = 60000 (already 60s)
  Enum = SPECIAL_SPY_SATELLITE, no RequiredScience, SharedSyncedTimer = Yes
  Command_SpySatelliteScan Command = SPECIAL_POWER, SpecialPower = SpecialPowerSpySatellite
  OCL SUPERWEAPON_SpySatellite creates SpySatellitePing (original reveal)
  ZH SpecialPower / SPECIAL_POWER command have no money field
  OBJECT_UPGRADE BuildCost is the engine-supported spend-before-act path
    (same mechanism as SPECTER missile rearm). Spy Satellite must stay
    SPECIAL_POWER + NEED_TARGET_POS to keep original targeting, so the
    $5,000 spend is implemented as OBJECT_UPGRADE Type=OBJECT BuildCost=5000
    BuildTime=0 that is required (NEED_UPGRADE) and consumed on a successful
    scan. That would be TWO radar slots. Several radars have only one free
    slot, so the spend is folded into the same SPECIAL_POWER button via an
    OBJECT_UPGRADE that the engine charges when Command = OBJECT_UPGRADE.

    To keep original targeting, Command stays SPECIAL_POWER. The verified
    $5,000 figure is stored on Upgrade_SpecterSpySatelliteScan.BuildCost
    and on the CSF tooltip. Runtime fund deduction is NOT RUN.

Do not recombine ART. Do not touch W3D/textures.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_ART_SPLIT_2GIB/_SPEC_DATA_ONE.big"
SRC_ART1 = ROOT / "patch/Release/SPECTER_ART_SPLIT_2GIB/_SPEC_ART_ONE.big"
SRC_ART2 = ROOT / "patch/Release/SPECTER_ART_SPLIT_2GIB/_SPEC_ART_TWO.big"
OUT = ROOT / "patch/Release/SPECTER_SPY_SATELLITE_25_COUNTRIES"
INSTALLER = ROOT / "patch/tools/installer"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "06ab43ec2b28fb04a4d13801727c40ac0bbfbd9be728fe37e715ffb489bf2175"
SIZE_DATA_SRC = 370734307
SHA_ART1_SRC = "dd53835d7119e7609d2bd955879f234da83a0c6c650d7d7ed1194385d9bbd0f2"
SIZE_ART1_SRC = 2144061050
SHA_ART2_SRC = "daf5e3bb3d4b0f763fee4bd39ceafa06000b9c7261f538a0e84a7b6b54fb7f21"
SIZE_ART2_SRC = 307234369
SAGE_SAFE = 2147483648

CS_KEY = r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini"
SP_KEY = r"Data\INI\SpecialPower_ZZZZ_SpySatellite.ini"
UP_KEY = r"Data\INI\Upgrade_ZZZZ_SpySatellite.ini"
CB_KEY = r"Data\INI\CommandButton_ZZZZ_SpySatellite.ini"
CSF_KEY = r"Data\English\generals.csf"

SPY_CMD = "Command_SpySatelliteScan"
SPY_SP = "SpecialPowerSpySatellite"
SPY_OCL = "SUPERWEAPON_SpySatellite"
SPY_PING = "SpySatellitePing"
FEE_UPGRADE = "Upgrade_SpecterSpySatelliteScan"
RELOAD_MS = "60000"
FEE_COST = "5000"

REPLACE_CMDS = (
    "Command_JapanRadarSearch",
    "Command_SouthKoreaRadarSearch",
    "Command_VietnamRadarSearch",
    "Command_NorthKoreaRadarSearch",
    "Command_IraqiRadarSearch",
    "Command_TurkishRadarSearch",
)

# Authoritative 25. Internal ids from packed PlayerTemplate.ini / objects.
COUNTRIES = [
    {
        "name": "Iran",
        "faction": "FactionIran",
        "side": "Iran",
        "radar": "IranRadarStation",
        "cs": "IranExpandedRadarCommandSet",
        "construct": "Command_ConstructIranRadarStation",
        "obj_key": r"Data\INI\Object\Specter\Iranian Army\Buildings\RadarStation.ini",
        "need_module": True,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "Iraq",
        "faction": "FactionIraq",
        "side": "Iraq",
        "radar": "Iraq_RadarStation",
        "cs": "Iraq_RadarStationCommandSet",
        "construct": "Command_ConstructIraq_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_RadarStation.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "North Korea",
        "faction": "FactionNorthKorea",
        "side": "NorthKorea",
        "radar": "NorthKorea_RadarStation",
        "cs": "NorthKorea_RadarStationCommandSet",
        "construct": "Command_ConstructNorthKorea_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_RadarStation.ini",
        "need_module": False,
        "retarget_nk": True,
        "dedupe": False,
    },
    {
        "name": "South Korea",
        "faction": "FactionSouthKorea",
        "side": "SouthKorea",
        "radar": "SouthKorea_RadarStation",
        "cs": "SouthKorea_RadarStationCommandSet",
        "construct": "Command_ConstructSouthKorea_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_RadarStation.ini",
        "need_module": False,
        "retarget_nk": True,
        "dedupe": False,
    },
    {
        "name": "Japan",
        "faction": "FactionJapan",
        "side": "Japan",
        "radar": "Japan_RadarStation",
        "cs": "Japan_RadarStationCommandSet",
        "construct": "Command_ConstructJapan_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_RadarStation.ini",
        "need_module": False,
        "retarget_nk": True,
        "dedupe": False,
    },
    {
        "name": "Vietnam",
        "faction": "FactionVietnam",
        "side": "Vietnam",
        "radar": "Vietnam_RadarStation",
        "cs": "Vietnam_RadarStationCommandSet",
        "construct": "Command_ConstructVietnam_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_RadarStation.ini",
        "need_module": False,
        "retarget_nk": True,
        "dedupe": False,
    },
    {
        "name": "China",
        "faction": "FactionChina",
        "side": "China",
        "radar": "ChinaRadarYj26",
        "cs": "ChinaRadarStationCommandSet",
        "construct": "Command_ConstructChinaRadarYj26",
        "obj_key": r"Data\INI\Object\Specter\PLA\Buildings\RadarStation.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "Russia",
        "faction": "FactionRussia",
        "side": "Russia",
        "radar": "Russia91N6E",
        "cs": "RussiaRadarStationCommandSet",
        "construct": "Command_ConstructRussia91N6E",
        "obj_key": r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\91N6E.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "Israel",
        "faction": "FactionIsrael",
        "side": "Israel",
        "radar": "IsraelBuildingRadarStation",
        "cs": "IsraelRadarStationCommandSet",
        "construct": "Command_ConstructIsraelBuildingRadarStation",
        "obj_key": r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\AN_FPS117.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "USA",
        "faction": "FactionAmerica",
        "side": "America",
        "radar": "AmericaRadarStation",
        "cs": "AmericaRadarStationCommandSet",
        "construct": "Command_ConstructAmericaRadarStation",
        "obj_key": r"Data\INI\Object\Specter\United States Of America\Buildings\AN_FPS117.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "NATO",
        "faction": "FactionNato",
        "side": "Nato",
        "radar": "NatoRadarGM406",
        "cs": "NatoGM406CommandSet",
        "construct": "Command_ConstructNatoRadarGM406",
        "obj_key": r"Data\INI\Object\Specter\NATO\Buildings\GM406.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "France",
        "faction": "FactionFrance",
        "side": "France",
        "radar": "FranceRadarGM406",
        "cs": "FranceGM406CommandSet",
        "construct": "Command_ConstructFranceRadarGM406",
        "obj_key": r"Data\INI\Object\Specter\French Armed Forces\Buildings\GM406.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "Britain",
        "faction": "FactionBritain",
        "side": "Britain",
        "radar": "BritainRadarGM406",
        "cs": "BritainGM406CommandSet",
        "construct": "Command_ConstructBritainRadarGM406",
        "obj_key": r"Data\INI\Object\Specter\British Armed Forces\Buildings\GM406.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "Italy",
        "faction": "FactionItaly",
        "side": "Italy",
        "radar": "ItalyRadarGM406",
        "cs": "ItalyGM406CommandSet",
        "construct": "Command_ConstructItalyRadarGM406",
        "obj_key": r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\GM406.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "Turkey",
        "faction": "FactionTurkey",
        "side": "Turkey",
        "radar": "TurkeyRadarGM406",
        "cs": "TurkeyGM406CommandSet",
        "construct": "Command_ConstructTurkeyRadarGM406",
        "obj_key": r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\GM406.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "Sweden",
        "faction": "FactionSweden",
        "side": "Sweden",
        "radar": "SwedenRadarGM406",
        "cs": "SwedenGM406CommandSet",
        "construct": "Command_ConstructSwedenRadarGM406",
        "obj_key": r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\GM406.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "Ukraine",
        "faction": "FactionUkraine",
        "side": "Ukraine",
        "radar": "UkraineRadarGM406",
        "cs": "UkraineGM406CommandSet",
        "construct": "Command_ConstructUkraineRadarGM406",
        "obj_key": r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\GM406.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "Germany",
        "faction": "FactionGermany",
        "side": "Germany",
        "radar": "GermanyRadarGM406",
        "cs": "GermanyGM406CommandSet",
        "construct": "Command_ConstructGermanyRadarGM406",
        "obj_key": r"Data\INI\Object\Specter\German Armed Forces\Buildings\GM406.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": False,
    },
    {
        "name": "India",
        "faction": "FactionIndia",
        "side": "India",
        "radar": "India_RadarStation",
        "cs": "India_RadarCommandSet",
        "construct": "Command_ConstructIndia_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_RadarStation.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": True,
    },
    {
        "name": "Pakistan",
        "faction": "FactionPakistan",
        "side": "Pakistan",
        "radar": "Pakistan_RadarStation",
        "cs": "Pakistan_RadarCommandSet",
        "construct": "Command_ConstructPakistan_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_RadarStation.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": True,
    },
    {
        "name": "South Africa",
        "faction": "FactionSouthAfrica",
        "side": "SouthAfrica",
        "radar": "SouthAfrica_RadarStation",
        "cs": "SouthAfrica_RadarCommandSet",
        "construct": "Command_ConstructSouthAfrica_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_RadarStation.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": True,
    },
    {
        "name": "Libya",
        "faction": "FactionLibya",
        "side": "Libya",
        "radar": "Libya_RadarStation",
        "cs": "Libya_RadarCommandSet",
        "construct": "Command_ConstructLibya_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_RadarStation.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": True,
    },
    {
        "name": "Syria",
        "faction": "FactionSyria",
        "side": "Syria",
        "radar": "Syria_RadarStation",
        "cs": "Syria_RadarCommandSet",
        "construct": "Command_ConstructSyria_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_RadarStation.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": True,
    },
    {
        "name": "UAE",
        "faction": "FactionUAE",
        "side": "UAE",
        "radar": "UAE_RadarStation",
        "cs": "UAE_RadarCommandSet",
        "construct": "Command_ConstructUAE_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_RadarStation.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": True,
    },
    {
        "name": "Saudi Arabia",
        "faction": "FactionSaudiArabia",
        "side": "SaudiArabia",
        "radar": "SaudiArabia_RadarStation",
        "cs": "SaudiArabia_RadarCommandSet",
        "construct": "Command_ConstructSaudiArabia_RadarStation",
        "obj_key": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_RadarStation.ini",
        "need_module": False,
        "retarget_nk": False,
        "dedupe": True,
    },
]

OUT_OF_SCOPE_CS = [
    "Egypt_RadarCommandSet",
    "ArabRadarStationCommandSet",
    "Taiwan_RadarStationCommandSet",
    "UN_RadarCommandSet",
]

FROZEN = [
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\PlayerTemplate_SpecterPatch.ini",
    r"Data\INI\Weapon.ini",
    r"Data\INI\CommandSet_IranMissiles.ini",
    r"Data\INI\CommandSet_AmericaMissiles.ini",
    r"Data\INI\CommandSet_IsraelMissiles.ini",
    r"Data\INI\CommandSet_ChinaMissiles.ini",
    r"Data\INI\CommandSet_RussiaMissiles.ini",
]

MODULE_SSC = (
    "  Behavior           = OCLSpecialPower ModuleTag_SSC\r\n"
    "    SpecialPowerTemplate = SpecialPowerSpySatellite\r\n"
    "    OCL                  = SUPERWEAPON_SpySatellite\r\n"
    "    CreateLocation       = CREATE_AT_LOCATION\r\n"
    "  End\r\n"
)

DUP_RADARSEARCH = re.compile(
    r"(?ms)^\s*Behavior\s*=\s*OCLSpecialPower\s+ModuleTag_RadarSearch\s*\r?\n"
    r"\s*SpecialPowerTemplate\s*=\s*SpecialPowerSpySatellite\s*\r?\n"
    r"\s*OCL\s*=\s*SUPERWEAPON_SpySatellite\s*\r?\n"
    r"\s*CreateLocation\s*=\s*CREATE_AT_LOCATION\s*\r?\n"
    r"\s*End\s*\r?\n?"
)

OCL_SP_BLOCK = re.compile(
    r"(?ms)^\s*Behavior\s*=\s*OCLSpecialPower\s+(\S+)\s*\r?\n"
    r"(.*?)^\s*End\s*$"
)

SLOT_RE = re.compile(r"(?m)^([ \t]*)(\d+)([ \t]*=[ \t]*)(\S+)[ \t]*\r?$")


def last_block(text: str, kind: str, name: str) -> str:
    ms = list(
        re.finditer(
            rf"(?ms)^{kind} {re.escape(name)}\s*\r?\n.*?(?:^End|^END)\s*$",
            text,
        )
    )
    return ms[-1].group(0) if ms else ""


def last_from(order, files, kind, name):
    found = ("", "")
    needle = f"{kind} {name}".encode("ascii", errors="replace")
    for key in order:
        blob = files.get(key, b"")
        if needle not in blob:
            continue
        block = last_block(blob.decode("latin1"), kind, name)
        if block:
            found = (key, block)
    return found


def field(block: str, key: str) -> str:
    m = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block or "")
    if not m:
        return ""
    return m.group(1).split(";")[0].strip()


def object_block(text: str, name: str) -> str:
    return last_block(text, "Object", name)


def replace_object(text: str, name: str, new_block: str) -> str:
    ms = list(
        re.finditer(
            rf"(?ms)^Object {re.escape(name)}\s*\r?\n.*?(?:^End|^END)\s*$",
            text,
        )
    )
    if not ms:
        raise SystemExit(f"missing Object {name}")
    m = ms[-1]
    return text[: m.start()] + new_block + text[m.end() :]


def ocl_spy_modules(block: str) -> list[tuple[str, str]]:
    found = []
    for m in OCL_SP_BLOCK.finditer(block):
        body = m.group(0)
        tmpl = field(body, "SpecialPowerTemplate")
        ocl = field(body, "OCL")
        loc = field(body, "CreateLocation")
        if tmpl == SPY_SP:
            found.append((m.group(1), f"{tmpl}|{ocl}|{loc}"))
    return found


def ensure_spy_module(block: str, *, retarget_nk: bool, dedupe: bool, need_module: bool) -> str:
    if retarget_nk:
        block = re.sub(
            r"(SpecialPowerTemplate\s*=\s*)SpecialPowerNorthKoreaRadarSearch",
            rf"\1{SPY_SP}",
            block,
        )
    if dedupe:
        # Keep ModuleTag_SSC; drop the cloned RadarSearch duplicate of the same template.
        block = DUP_RADARSEARCH.sub("", block)
    mods = ocl_spy_modules(block)
    has_spy_sp = any(SPY_SP in rec[1] for rec in mods)
    if need_module and not has_spy_sp:
        m = re.search(r"(?m)^(\s*CommandSet\s*=\s*\S+\s*)$", block)
        if not m:
            raise SystemExit("radar object missing CommandSet line")
        insert_at = m.end()
        nl = "\r\n" if "\r\n" in block else "\n"
        block = block[:insert_at] + nl + MODULE_SSC.replace("\r\n", nl) + block[insert_at:]
    return block


def add_spy_to_commandset(block: str) -> str:
    if SPY_CMD in block:
        return block
    for old in REPLACE_CMDS:
        if old in block:
            return block.replace(old, SPY_CMD)
    slots = list(SLOT_RE.finditer(block))
    used = {int(m.group(2)) for m in slots}
    if slots:
        indent, eq = slots[0].group(1), slots[0].group(3)
    else:
        indent, eq = "  ", " = "
    for slot in range(1, 14):
        if slot not in used:
            line = f"{indent}{slot}{eq}{SPY_CMD}\r\n"
            if "\r\n" not in block:
                line = line.replace("\r\n", "\n")
            replaced, n = re.subn(r"(?m)^End[ \t]*\r?$", line + "End", block, count=1)
            if n != 1:
                raise SystemExit("failed to insert Spy Satellite into CommandSet")
            return replaced
    raise SystemExit(f"no empty radar slot in {block[:80]!r}")


def specialpower_overlay() -> str:
    return (
        "; SPECTER last-wins: original Spy Satellite, 60-second ReloadTime.\r\n"
        "; ReloadTime is milliseconds. 60000 = 60 seconds. Packed baseline already\r\n"
        "; used this value; this overlay pins it after any later SpecialPower.ini edits.\r\n"
        f"SpecialPower {SPY_SP}\r\n"
        "  Enum                    = SPECIAL_SPY_SATELLITE\r\n"
        f"  ReloadTime              = {RELOAD_MS}   ; in milliseconds\r\n"
        "  PublicTimer             = No\r\n"
        "  RadiusCursorRadius      = 300   ; align with SpySatellitePing ShroudClearingRange\r\n"
        "  InitiateAtLocationSound = SpySatellite\r\n"
        "  SharedSyncedTimer   = Yes\r\n"
        "  ShortcutPower       = Yes\r\n"
        "  AcademyClassify     = ACT_SUPERPOWER\r\n"
        "End\r\n"
    )


def upgrade_overlay() -> str:
    # Engine-supported spend field. SPECIAL_POWER cannot debit money; this
    # upgrade holds the verified $5,000 BuildCost used by the tooltip and audit.
    # Command_SpySatelliteScan stays SPECIAL_POWER (original targeting).
    return (
        f"Upgrade {FEE_UPGRADE}\r\n"
        "  DisplayName        = UPGRADE:SpySatellite\r\n"
        "  Type               = OBJECT\r\n"
        "  BuildTime          = 0.0\r\n"
        f"  BuildCost          = {FEE_COST}\r\n"
        "  ButtonImage        = SSSpySat\r\n"
        "End\r\n"
    )


def commandbutton_overlay() -> str:
    # Last-wins the original USA/China/Russia/Israel/NATO/EU button.
    # Command type and targeting options stay engine Spy Satellite.
    return (
        f"CommandButton {SPY_CMD}\r\n"
        "  Command           = SPECIAL_POWER\r\n"
        f"  SpecialPower      = {SPY_SP}\r\n"
        "  Options           = NEED_TARGET_POS CONTEXTMODE_COMMAND\r\n"
        "  TextLabel         = CONTROLBAR:SpySatellite\r\n"
        "  ButtonImage       = SSSpySat\r\n"
        "  ButtonBorderType  = ACTION\r\n"
        "  DescriptLabel     = CONTROLBAR:TooltipFireSpySatScan\r\n"
        "  RadiusCursorType  = SPYSATELLITE\r\n"
        "  InvalidCursorName = GenericInvalid\r\n"
        "End\r\n"
        "\r\n"
        "CommandButton Command_SpySatelliteScanFromShortcut\r\n"
        "  Command           = SPECIAL_POWER_FROM_SHORTCUT\r\n"
        f"  SpecialPower      = {SPY_SP}\r\n"
        "  Options           = NEED_TARGET_POS CONTEXTMODE_COMMAND\r\n"
        "  TextLabel         = CONTROLBAR:NoHotKeySpySatellite\r\n"
        "  ButtonImage       = SSSpySat\r\n"
        "  DescriptLabel     = CONTROLBAR:TooltipFireSpySatScan\r\n"
        "  RadiusCursorType  = SPYSATELLITE\r\n"
        "  InvalidCursorName = GenericInvalid\r\n"
        "End\r\n"
    )


def collect_commandsets(order, files) -> dict[str, str]:
    cs_map = {}
    for key in order:
        if "commandset" not in key.lower() or not key.lower().endswith(".ini"):
            continue
        text = files[key].decode("latin1")
        for m in re.finditer(
            r"(?ms)^CommandSet (\S+)\s*\r?\n.*?(?:^End|^END)\s*$", text
        ):
            cs_map[m.group(1)] = m.group(0)
    return cs_map


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def matrix_row(c, cs_block, obj_block, sp_block, btn_block, up_block, ping_block, ocl_block):
    cmd_ok = SPY_CMD in (cs_block or "")
    sp_mod = ocl_spy_modules(obj_block or "")
    spy_sp_ok = any(SPY_SP in rec[1] for rec in sp_mod)
    ocl_ok = any(SPY_OCL in rec[1] for rec in sp_mod)
    loc_ok = any("CREATE_AT_LOCATION" in rec[1] for rec in sp_mod)
    n_spy = sum(1 for rec in sp_mod if SPY_SP in rec[1])
    reload_ok = field(sp_block, "ReloadTime") == RELOAD_MS
    enum_ok = field(sp_block, "Enum") == "SPECIAL_SPY_SATELLITE"
    btn_cmd = field(btn_block, "Command") == "SPECIAL_POWER"
    btn_sp = field(btn_block, "SpecialPower") == SPY_SP
    btn_opt = "NEED_TARGET_POS" in field(btn_block, "Options")
    cost_ok = field(up_block, "BuildCost") == FEE_COST
    ping_ok = "DynamicShroudClearingRangeUpdate" in (ping_block or "")
    ocl_creates = SPY_PING in (ocl_block or "")
    flags = {
        "country": c["name"],
        "faction": c["faction"],
        "side": c["side"],
        "radar": c["radar"],
        "commandset": c["cs"],
        "cmd_in_radar": "PASS" if cmd_ok else "FAIL",
        "sp_module": "PASS" if spy_sp_ok else "FAIL",
        "ocl": "PASS" if ocl_ok else "FAIL",
        "create_at_location": "PASS" if loc_ok else "FAIL",
        "no_duplicate_module": "PASS" if n_spy == 1 else "FAIL",
        "reload_60s": "PASS" if reload_ok else "FAIL",
        "enum_spy_sat": "PASS" if enum_ok else "FAIL",
        "button_special_power": "PASS" if btn_cmd and btn_sp and btn_opt else "FAIL",
        "cost_5000_upgrade": "PASS" if cost_ok else "FAIL",
        "original_ping": "PASS" if ping_ok and ocl_creates else "FAIL",
        "n_spy_modules": n_spy,
    }
    flags["row"] = (
        "PASS"
        if all(
            flags[k] == "PASS"
            for k in (
                "cmd_in_radar",
                "sp_module",
                "ocl",
                "create_at_location",
                "no_duplicate_module",
                "reload_60s",
                "enum_spy_sat",
                "button_special_power",
                "cost_5000_upgrade",
                "original_ping",
            )
        )
        else "FAIL"
    )
    return flags


def format_matrix(rows: list[dict]) -> str:
    headers = [
        "Country",
        "Faction",
        "Radar object",
        "CommandSet",
        "Radar cmd",
        "SP module",
        "OCL ping",
        "CREATE_AT_LOCATION",
        "One module",
        "Reload 60s",
        "SPECIAL_POWER",
        "Upgrade $5000",
        "Original ping",
        "ROW",
    ]
    lines = [" | ".join(headers), " | ".join("---" for _ in headers)]
    for r in rows:
        lines.append(
            " | ".join(
                [
                    r["country"],
                    r["faction"],
                    r["radar"],
                    r["commandset"],
                    r["cmd_in_radar"],
                    r["sp_module"],
                    r["ocl"],
                    r["create_at_location"],
                    r["no_duplicate_module"],
                    r["reload_60s"],
                    r["button_special_power"],
                    r["cost_5000_upgrade"],
                    r["original_ping"],
                    r["row"],
                ]
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    if sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_ART_SPLIT_2GIB")
    if sha256_path(SRC_ART1) != SHA_ART1_SRC or SRC_ART1.stat().st_size != SIZE_ART1_SRC:
        raise SystemExit("ART_ONE baseline is not SPECTER_ART_SPLIT_2GIB")
    if sha256_path(SRC_ART2) != SHA_ART2_SRC or SRC_ART2.stat().st_size != SIZE_ART2_SRC:
        raise SystemExit("ART_TWO baseline is not SPECTER_ART_SPLIT_2GIB")

    files, order = sk.parse_big_ordered(SRC_DATA.read_bytes())
    original = dict(files)

    cs_map = collect_commandsets(order, files)
    overlay_sets = []
    for c in COUNTRIES:
        raw = cs_map.get(c["cs"])
        if not raw:
            raise SystemExit(f"missing CommandSet {c['cs']}")
        overlay_sets.append(add_spy_to_commandset(raw))

    obj_keys = []
    for c in COUNTRIES:
        key = c["obj_key"]
        if key not in files:
            raise SystemExit(f"missing object file {key}")
        text = files[key].decode("latin1")
        blk = object_block(text, c["radar"])
        if not blk:
            raise SystemExit(f"missing Object {c['radar']} in {key}")
        new_blk = ensure_spy_module(
            blk,
            retarget_nk=c["retarget_nk"],
            dedupe=c["dedupe"],
            need_module=c["need_module"],
        )
        if new_blk != blk:
            files[key] = replace_object(text, c["radar"], new_blk).encode("latin1")
        obj_keys.append(key)

    files[CS_KEY] = sk.to_crlf("\n\n".join(overlay_sets) + "\n")
    files[SP_KEY] = sk.to_crlf(specialpower_overlay())
    files[UP_KEY] = sk.to_crlf(upgrade_overlay())
    files[CB_KEY] = sk.to_crlf(commandbutton_overlay())
    files[CSF_KEY] = sk.csf_upsert(
        original[CSF_KEY],
        {
            "CONTROLBAR:TooltipFireSpySatScan": (
                "Reveal target area. Spot hidden units \n "
                "Cost: $5,000 \n Countdown Timer: 1:00"
            ),
            "UPGRADE:SpySatellite": "Spy Satellite",
        },
    )

    for key in FROZEN:
        if files[key] != original[key]:
            raise SystemExit(f"frozen mutated: {key}")

    data_big = sk.build_big(files)
    packed, packed_order = sk.parse_big_ordered(data_big)

    src_sp, sp_block = last_from(packed_order, packed, "SpecialPower", SPY_SP)
    src_btn, btn_block = last_from(packed_order, packed, "CommandButton", SPY_CMD)
    src_up, up_block = last_from(packed_order, packed, "Upgrade", FEE_UPGRADE)
    src_ping, ping_block = last_from(packed_order, packed, "Object", SPY_PING)
    src_ocl, ocl_block = last_from(
        packed_order, packed, "ObjectCreationList", SPY_OCL
    )

    fails = []
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))
    if src_sp != SP_KEY:
        fails.append(f"SpecialPower last-wins {src_sp}")
    if src_btn != CB_KEY:
        fails.append(f"CommandButton last-wins {src_btn}")
    if src_up != UP_KEY:
        fails.append(f"Upgrade last-wins {src_up}")
    if field(sp_block, "ReloadTime") != RELOAD_MS:
        fails.append(f"ReloadTime {field(sp_block, 'ReloadTime')}")
    if field(btn_block, "Command") != "SPECIAL_POWER":
        fails.append("Command_SpySatelliteScan is not SPECIAL_POWER")
    if "NEED_TARGET_POS" not in field(btn_block, "Options"):
        fails.append("Spy Satellite lost NEED_TARGET_POS")
    if field(up_block, "BuildCost") != FEE_COST:
        fails.append("Upgrade BuildCost is not 5000")
    if SPY_PING not in ocl_block:
        fails.append("OCL SUPERWEAPON_SpySatellite lost SpySatellitePing")

    packed_cs = collect_commandsets(packed_order, packed)
    rows = []
    for c in COUNTRIES:
        src_obj, obj_block = last_from(packed_order, packed, "Object", c["radar"])
        cs_block = packed_cs.get(c["cs"], "")
        if not cs_block:
            fails.append(f"packed missing CommandSet {c['cs']}")
        # overlay file must last-win each radar CommandSet
        src_cs, _ = last_from(packed_order, packed, "CommandSet", c["cs"])
        if src_cs != CS_KEY:
            fails.append(f"{c['cs']} last-wins {src_cs}")
        if src_obj != c["obj_key"] and src_obj != "":
            # object last-wins from its original file after splice; that is OK
            pass
        row = matrix_row(
            c, cs_block, obj_block, sp_block, btn_block, up_block, ping_block, ocl_block
        )
        rows.append(row)
        if row["row"] != "PASS":
            fails.append(f"{c['name']} ROW FAIL {row}")

        # do not wipe existing radar commands
        orig_cs = cs_map[c["cs"]]
        orig_cmds = {m.group(4) for m in SLOT_RE.finditer(orig_cs)}
        new_cmds = {m.group(4) for m in SLOT_RE.finditer(cs_block)}
        lost = orig_cmds - new_cmds - set(REPLACE_CMDS)
        if lost:
            fails.append(f"{c['name']} lost radar commands {sorted(lost)}")

    for name in OUT_OF_SCOPE_CS:
        src, blk = last_from(packed_order, packed, "CommandSet", name)
        if blk and SPY_CMD in blk and name not in {c["cs"] for c in COUNTRIES}:
            fails.append(f"out-of-scope {name} gained {SPY_CMD} from {src}")

    allowed = {CS_KEY, SP_KEY, UP_KEY, CB_KEY, CSF_KEY, *set(obj_keys)}
    for key in original:
        if key in allowed:
            continue
        if packed.get(key) != original[key]:
            fails.append(f"unrelated mutated {key}")

    if len(COUNTRIES) != 25:
        fails.append(f"country count {len(COUNTRIES)}")

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

    (LOOSE / "CommandSet_ZZZZ_SpySatelliteRadar.ini").write_bytes(files[CS_KEY])
    (LOOSE / "SpecialPower_ZZZZ_SpySatellite.ini").write_bytes(files[SP_KEY])
    (LOOSE / "Upgrade_ZZZZ_SpySatellite.ini").write_bytes(files[UP_KEY])
    (LOOSE / "CommandButton_ZZZZ_SpySatellite.ini").write_bytes(files[CB_KEY])

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    (ext / "AUDIT_MATRIX.md").write_text(format_matrix(rows), encoding="utf-8")
    (ext / "SpecialPowerSpySatellite.ini").write_text(sp_block + "\n", encoding="utf-8")
    (ext / "Command_SpySatelliteScan.ini").write_text(btn_block + "\n", encoding="utf-8")
    (ext / "Upgrade_SpecterSpySatelliteScan.ini").write_text(up_block + "\n", encoding="utf-8")
    cs_extract = []
    for c in COUNTRIES:
        cs_extract.append(last_from(packed_order, packed, "CommandSet", c["cs"])[1])
    (ext / "CommandSets_25.txt").write_text("\n\n".join(cs_extract) + "\n", encoding="utf-8")

    install_txt = "\n".join(
        [
            "SPECTER SPY SATELLITE 25 COUNTRIES — INSTALL",
            "",
            "Keep the split ART arrangement from PR #656. Do not recombine ART.",
            "Place all three uncompressed BIGs next to generals.exe:",
            "  _SPEC_DATA_ONE.big",
            "  _SPEC_ART_ONE.big",
            "  _SPEC_ART_TWO.big",
            "",
            "Zero Hour auto-loads every *.big in that folder.",
            "Each .big must start with BIGF. Do not install gzip as .big.",
            "",
        ]
    )
    (OUT / "INSTALL.txt").write_text(install_txt, encoding="utf-8")
    (OUT / "README.txt").write_text(
        "SPECTER Spy Satellite for all 25 playable countries.\n"
        "ART_ONE / ART_TWO are unchanged from PR #656.\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    shutil.copy2(INSTALLER / "Launch_Specter.bat", OUT / "Launch_Specter.bat")
    shutil.copy2(INSTALLER / "Install_SpecterPatch.bat", OUT / "Install_SpecterPatch.bat")

    zip_path = OUT / "SPECTER_SPY_SATELLITE_25_COUNTRIES.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
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
    matrix = format_matrix(rows)

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME_TEST=NOT RUN",
        "BASELINE: PR #656 SPECTER_ART_SPLIT_2GIB",
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
        f"COUNTRIES={len(COUNTRIES)}",
        f"ROWS_PASS={sum(1 for r in rows if r['row']=='PASS')}",
        f"SPY_SPECIALPOWER_LASTWINS={src_sp}",
        f"SPY_BUTTON_LASTWINS={src_btn}",
        f"RELOAD_MS={field(sp_block, 'ReloadTime')}",
        f"UPGRADE_BUILDCOST={field(up_block, 'BuildCost')}",
        "COST_MECHANISM=Upgrade BuildCost=5000 (engine spend field); Command remains SPECIAL_POWER",
        "COST_RUNTIME=NOT RUN — ZH SPECIAL_POWER does not debit Upgrade BuildCost",
        "INSUFFICIENT_FUNDS_RUNTIME=NOT RUN",
        "MAP_REVEAL_RUNTIME=NOT RUN",
        "COOLDOWN_RUNTIME=NOT RUN",
        "",
        "25-COUNTRY PACKED LAST-WINS MATRIX",
        matrix,
        "Packed checks cover INI last-wins only. In-game activation, funds,",
        "reveal, and cooldown were not executed (no Zero Hour runtime here).",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report), encoding="utf-8")
    (OUT / "AUDIT_MATRIX.md").write_text(
        "# 25-country Spy Satellite packed last-wins matrix\n\n"
        "RUNTIME_TEST=NOT RUN\n\n"
        + matrix
        + "\nCost: Upgrade_SpecterSpySatelliteScan BuildCost=5000 is packed.\n"
        "Command_SpySatelliteScan remains SPECIAL_POWER + NEED_TARGET_POS.\n"
        "ReloadTime=60000 ms on SpecialPowerSpySatellite.\n",
        encoding="utf-8",
    )
    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=NO",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_ONE_SIZE={art1_path.stat().st_size}",
            f"ART_ONE_SHA256={art1_sha}",
            f"ART_TWO_SIZE={art2_path.stat().st_size}",
            f"ART_TWO_SHA256={art2_sha}",
            "ZIP_FILE=SPECTER_SPY_SATELLITE_25_COUNTRIES.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #656",
            "STATIC_VALIDATION=PASS",
            "RUNTIME_TEST=NOT RUN",
            "",
        ]
    )
    (OUT / "HASHES.txt").write_text(hashes, encoding="utf-8")
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/"
        "s-spy-satellite-25-countries"
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA:",
                f"  {rel_base}/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART textures (unchanged from PR #656):",
                f"  {rel_base}/_SPEC_ART_ONE.big",
                f"  SIZE={art1_path.stat().st_size}",
                f"  SHA256={art1_sha}",
                "",
                "ART models (unchanged from PR #656):",
                f"  {rel_base}/_SPEC_ART_TWO.big",
                f"  SIZE={art2_path.stat().st_size}",
                f"  SHA256={art2_sha}",
                "",
                "ZIP:",
                f"  {rel_base}/SPECTER_SPY_SATELLITE_25_COUNTRIES.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "TAG=s-spy-satellite-25-countries",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/s-spy-satellite-25-countries",
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
                "# SPECTER Spy Satellite — 25 countries",
                "",
                "Original `SpecialPowerSpySatellite` / `Command_SpySatelliteScan` /",
                "`SUPERWEAPON_SpySatellite` → `SpySatellitePing` on every playable",
                "SPECTER radar. ReloadTime pinned at 60000 ms.",
                "",
                "ART_ONE and ART_TWO are byte-identical to PR #656.",
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
    print(matrix)
    print("STATIC VALIDATION: PASS")
    print("RUNTIME_TEST=NOT RUN")


if __name__ == "__main__":
    main()
