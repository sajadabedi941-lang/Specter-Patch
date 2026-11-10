#!/usr/bin/env python3
"""Complete radar-sarab-lamina for all 19 listed countries.

Source: RADAR_SARAB_LAMINA DATA (18 countries already have SpecterRadar_Sarab3
$500 and SpecterRadar_Lamina $5000 on empty Radar slots 7/8).

Spain live structure (not guessed):
  No PlayerTemplate FactionSpain, no SIDE:Spain CSF, no Spain dozer/CC/Radar.
  Spain content is Side=Nato: Spain_MissileFactory on NatoDozerCommandSet slot 14.
  NatoDozerCommandSet slots 1-18 are full (cannot add Radar without replacing).
  Spain_MissileFactoryCommandSet last-win (CommandSet_SpainMissiles.ini) has
  empty slots 11, 12, 15-18. CommandSet.ini copy has empty 15-18.

This packer adds a Spain-only Radar clone of NatoRadarGM406:
  Object SpainRadarGM406
  CommandSet Spain_RadarCommandSet  slots 7/8 = Sarab_3 / Lamina, 14 = Sell
  Construct button on Spain_MissileFactory slot 15 (empty in both CS copies)
  Spy Satellite special power omitted on the Spain clone
  NATO Radar / NATO dozer / other countries unchanged

North Korea already has both drones from the previous pack; kept.

Does not restore India CombatDrone, Spy Satellite, Israel Strategy Center,
ART, or 0_ overlays. Does not edit Iraq originals.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/RADAR_SARAB_LAMINA/_SPEC_DATA_ONE.big"
SRC_SHA = "91964a69e3d39f8143c1dc2ae9c6d3577a025a46cc6f3641dd4e6307ee693f2d"
OUT_DIR = ROOT / "Release/RADAR_SARAB_LAMINA_19"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
ZIP_NAME = "SPECTER_RADAR_SARAB_LAMINA_19_INSTALL.zip"
MARKER = "SPECTER_PATCH RADAR_SARAB_LAMINA_19"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_PT = r"Data\INI\PlayerTemplate.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_UAV = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_SPY = r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini"
K_PK = r"Data\INI\CommandSet_Pakistan.ini"
K_SPAIN_CS = r"Data\INI\CommandSet_SpainMissiles.ini"
K_NATO_RADAR = r"Data\INI\Object\Specter\NATO\Buildings\GM406.ini"
K_SPAIN_RADAR = (
    r"Data\INI\Object\Specter\Spanish Armed Forces\Buildings\Spain_RadarGM406.ini"
)
K_SPAIN_FACTORY = (
    r"Data\INI\Object\Specter\Spanish Armed Forces\Buildings\Spain_MissileFactory.ini"
)
K_SARAB_SRC = r"Data\INI\Object\Specter\Iraq Army\Drones\Sarab3.ini"
K_LAM_SRC = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Lamiaa.ini"
K_MAP = r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI"
K_LOCO = r"Data\INI\Locomotor.ini"
K_NK_RADAR = r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_RadarStation.ini"

BTN_SARAB = "Command_ConstructSpecterRadarSarab3"
BTN_LAMINA = "Command_ConstructSpecterRadarLamina"
BTN_SPAIN_RADAR = "Command_ConstructSpainRadarGM406"
OBJ_SARAB = "SpecterRadar_Sarab3"
OBJ_LAMINA = "SpecterRadar_Lamina"
OBJ_SPAIN_RADAR = "SpainRadarGM406"
CS_SPAIN_RADAR = "Spain_RadarCommandSet"
CS_SPAIN_FACTORY = "Spain_MissileFactoryCommandSet"

RADAR_SETS_18 = (
    "SaudiArabia_RadarCommandSet",
    "UAE_RadarCommandSet",
    "Syria_RadarCommandSet",
    "India_RadarCommandSet",
    "Pakistan_RadarCommandSet",
    "SouthAfrica_RadarCommandSet",
    "Libya_RadarCommandSet",
    "TurkeyGM406CommandSet",
    "SwedenGM406CommandSet",
    "UkraineGM406CommandSet",
    "ItalyGM406CommandSet",
    "BritainGM406CommandSet",
    "GermanyGM406CommandSet",
    "FranceGM406CommandSet",
    "Vietnam_RadarStationCommandSet",
    "SouthKorea_RadarStationCommandSet",
    "Japan_RadarStationCommandSet",
    "NorthKorea_RadarStationCommandSet",
)

COUNTRY_ROWS = (
    ("عربستان", "SaudiArabia_RadarCommandSet", "object SaudiArabia_RadarStation"),
    ("امارات", "UAE_RadarCommandSet", "object UAE_RadarStation"),
    ("سوریه", "Syria_RadarCommandSet", "object Syria_RadarStation"),
    ("هند", "India_RadarCommandSet", "object India_RadarStation"),
    ("پاکستان", "Pakistan_RadarCommandSet", "object Pakistan_RadarStation"),
    ("آفریقای جنوبی", "SouthAfrica_RadarCommandSet", "object SouthAfrica_RadarStation"),
    ("لیبی", "Libya_RadarCommandSet", "object Libya_RadarStation"),
    ("ترکیه", "TurkeyGM406CommandSet", "object TurkeyRadarGM406"),
    ("سوئد", "SwedenGM406CommandSet", "object SwedenRadarGM406"),
    ("اوکراین", "UkraineGM406CommandSet", "object UkraineRadarGM406"),
    ("ایتالیا", "ItalyGM406CommandSet", "object ItalyRadarGM406"),
    ("بریتانیا", "BritainGM406CommandSet", "object BritainRadarGM406"),
    ("آلمان", "GermanyGM406CommandSet", "object GermanyRadarGM406"),
    ("فرانسه", "FranceGM406CommandSet", "object FranceRadarGM406"),
    (
        "اسپانیا",
        CS_SPAIN_RADAR,
        "new object SpainRadarGM406 (clone of NatoRadarGM406); "
        "no FactionSpain — NATO builds Spain_MissileFactory then Spain Radar",
    ),
    ("ویتنام", "Vietnam_RadarStationCommandSet", "object Vietnam_RadarStation"),
    ("کره جنوبی", "SouthKorea_RadarStationCommandSet", "object SouthKorea_RadarStation"),
    ("ژاپن", "Japan_RadarStationCommandSet", "object Japan_RadarStation"),
    ("کره شمالی", "NorthKorea_RadarStationCommandSet", "object NorthKorea_RadarStation"),
)

KEEP_SHARED = (
    "Command_ConstructSpecterRadarHeron",
    "Command_ConstructSpecterRadarMQ4",
    "Command_ConstructSpecterRadarOrlan10",
    "Command_ConstructSpecterRadarShahedLauncher",
)

SPAIN_RADAR_CS = f"""
CommandSet {CS_SPAIN_RADAR}
  7 = {BTN_SARAB} ; {MARKER}
  8 = {BTN_LAMINA}
 14 = Command_Sell
End
"""

SPAIN_RADAR_BTN = f"""
CommandButton {BTN_SPAIN_RADAR}
  Command       = DOZER_CONSTRUCT
  Object        = {OBJ_SPAIN_RADAR}
  TextLabel     = CONTROLBAR:ConstructNatoRadarGM406
  ButtonImage   = Button_Radar
  ButtonBorderType        = BUILD
  DescriptLabel           = CONTROLBAR:ToolTipUSABuildNatoRadarGM406
End
; {MARKER} Spain-only Radar construct; NATO dozer 1-18 full so this sits on
; Spain_MissileFactoryCommandSet empty slot 15 (both CS.ini and SpainMissiles overlay)
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index, blobs, offset = [], [], header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def block(text: str, kind: str, name: str) -> str:
    m = re.search(
        rf"^{kind} {re.escape(name)}(?:\s*;[^\r\n]*)?\s*\r?\n",
        text,
        re.M,
    )
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    n2 = re.search(rf"^{kind} ", text[m.end() :], re.M)
    end = m.end() + n2.start() if n2 else len(text)
    return text[m.start() : end]


def used_slots(body: str) -> dict[int, str]:
    slots: dict[int, str] = {}
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith(";") or s.startswith("CommandSet") or s == "End":
            continue
        m = re.match(r"(\d+)\s*=\s*(\S+)", s)
        if m:
            slots[int(m.group(1))] = m.group(2)
    return slots


def active_has(body: str, needle: str) -> bool:
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        if needle in s:
            return True
    return False


def nl_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def insert_before_end(body: str, insert: str) -> str:
    m = re.search(r"^End\s*$", body, re.M)
    require(m is not None, "CommandSet End missing")
    return body[: m.start()] + insert + body[m.start() :]


def add_factory_slot15(body: str) -> str:
    slots = used_slots(body)
    require(15 not in slots, f"Spain factory slot 15 occupied: {slots.get(15)}")
    require(BTN_SPAIN_RADAR not in body, "Spain Radar construct already on factory")
    nl = nl_of(body)
    insert = f"  15 = {BTN_SPAIN_RADAR} ; {MARKER}{nl}"
    return insert_before_end(body, insert)


def patch_named_factory(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    old = block(text, "CommandSet", CS_SPAIN_FACTORY)
    new = add_factory_slot15(old)
    require(text.count(old) == 1, f"duplicate {CS_SPAIN_FACTORY}")
    return text.replace(old, new, 1).encode("latin1")


def clone_spain_radar(src: bytes) -> bytes:
    text = src.decode("latin1")
    require("Object NatoRadarGM406" in text, "NatoRadarGM406 missing")
    require("CommandSet          = NatoGM406CommandSet" in text, "Nato GM406 CS")
    require("Behavior = ProductionUpdate ModuleTag_0595" in text, "prod 0595")
    require("Behavior = DefaultProductionExitUpdate ModuleTag_13" in text, "exit")
    require("RadarUpgrade" in text, "RadarUpgrade")
    new = text.replace("Object NatoRadarGM406", f"Object {OBJ_SPAIN_RADAR}", 1)
    new = new.replace(
        "CommandSet          = NatoGM406CommandSet",
        f"CommandSet          = {CS_SPAIN_RADAR}",
        1,
    )
    spy_mod = (
        "  Behavior           = OCLSpecialPower ModuleTag_SSC\r\n"
        "    SpecialPowerTemplate = SpecialPowerSpySatellite\r\n"
        "    OCL                  = SUPERWEAPON_SpySatellite\r\n"
        "    CreateLocation       = CREATE_AT_LOCATION\r\n"
        "  End"
    )
    if spy_mod not in new:
        spy_mod = spy_mod.replace("\r\n", "\n")
    require(spy_mod in new, "Spy Satellite module pattern drifted")
    new = new.replace(
        spy_mod,
        f"  ; {MARKER} Spy Satellite special power omitted on Spain Radar",
        1,
    )
    require("SpecialPowerSpySatellite" not in new, "spy power still on Spain Radar")
    require(CS_SPAIN_RADAR in new, "Spain CS not applied")
    require("NatoGM406CommandSet" not in new, "still points at NATO CS")
    header = (
        f"; {MARKER} Spain-only Radar. Clone of NatoRadarGM406.\r\n"
        f"; Side stays Nato (Spain_MissileFactory is Side=Nato; no FactionSpain).\r\n"
        f"; ART/model Nat_RadarSt reused; no new ART or 0_ overlay.\r\n"
    )
    return (header + new).encode("latin1")


def last_buildcost(body: str) -> str | None:
    costs = re.findall(r"^\s*BuildCost\s*=\s*(\d+)", body, re.M)
    return costs[-1] if costs else None


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_PT] == new[K_PT], "PlayerTemplate.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    require(orig[K_UAV] == new[K_UAV], "UAV file changed")
    require(orig[K_SARAB_SRC] == new[K_SARAB_SRC], "Iraq_Sarab3 source edited")
    require(orig[K_LAM_SRC] == new[K_LAM_SRC], "Iraq_Lamiaa source edited")
    require(orig[K_MAP] == new[K_MAP], "MappedImages changed")
    require(orig[K_LOCO] == new[K_LOCO], "Locomotor.ini changed")
    require(orig[K_NATO_RADAR] == new[K_NATO_RADAR], "NatoRadarGM406 edited")
    require(orig[K_SPAIN_FACTORY] == new[K_SPAIN_FACTORY], "Spain factory object edited")
    require(orig[K_PK] == new[K_PK], "Pakistan.ini changed")
    require(K_SPAIN_RADAR in new, "Spain Radar object missing from BIG")
    require(K_SPAIN_RADAR not in orig, "Spain Radar already existed")

    expected = {K_CS, K_CB, K_SPY, K_SPAIN_CS}
    changed = [k for k in orig if orig[k] != new[k]]
    require(set(changed) == expected, f"unexpected files changed: {changed}")

    orig_cs = orig[K_CS].decode("latin1")
    new_cs = new[K_CS].decode("latin1")
    require("SPECTER_PATCH ISRAEL_GS" in new_cs, "Israel GS lost")
    require("SPECTER_PATCH INDIA_NO_DRONES" in new_cs, "India drone hide lost")
    require("SPECTER_PATCH RADAR_SARAB_LAMINA" in new_cs, "18-country marker lost")
    require(
        not active_has(
            block(new_cs, "CommandSet", "India_RadarCommandSet"),
            "Command_ConstructIndia_CombatDrone",
        ),
        "India CombatDrone restored",
    )
    require(
        block(orig_cs, "CommandSet", "Iraq_RadarStationCommandSet")
        == block(new_cs, "CommandSet", "Iraq_RadarStationCommandSet"),
        "Iraq radar edited",
    )
    require(
        block(orig_cs, "CommandSet", "NatoDozerCommandSet")
        == block(new_cs, "CommandSet", "NatoDozerCommandSet"),
        "NATO dozer edited",
    )
    require(
        block(orig_cs, "CommandSet", "NatoGM406CommandSet")
        == block(new_cs, "CommandSet", "NatoGM406CommandSet"),
        "NATO Radar CS edited",
    )

    for name in RADAR_SETS_18:
        body = block(new_cs, "CommandSet", name)
        slots = used_slots(body)
        require(slots.get(7) == BTN_SARAB, f"{name} slot 7")
        require(slots.get(8) == BTN_LAMINA, f"{name} slot 8")
        orig_slots = used_slots(block(orig_cs, "CommandSet", name))
        for n, btn in orig_slots.items():
            require(slots.get(n) == btn, f"{name} lost slot {n} {btn}")
        require(
            not any("SpySatellite" in v for v in slots.values()),
            f"{name} gained Spy Satellite",
        )

    nk = block(new_cs, "CommandSet", "NorthKorea_RadarStationCommandSet")
    nk_slots = used_slots(nk)
    require(nk_slots.get(7) == BTN_SARAB, "NK missing Sarab_3")
    require(nk_slots.get(8) == BTN_LAMINA, "NK missing Lamina")
    require("Command_ConstructNorthKoreaDrone_Recon" in nk, "NK recon drone lost")

    spain_cs = block(new_cs, "CommandSet", CS_SPAIN_RADAR)
    spain_slots = used_slots(spain_cs)
    require(spain_slots.get(7) == BTN_SARAB, "Spain Radar slot 7")
    require(spain_slots.get(8) == BTN_LAMINA, "Spain Radar slot 8")
    require(spain_slots.get(14) == "Command_Sell", "Spain Radar sell")
    require(7 in spain_slots and 8 in spain_slots, "Spain slots missing")
    from collections import Counter

    counts = Counter(re.findall(r"^CommandSet (\S+)", new_cs, re.M))
    require(counts[CS_SPAIN_RADAR] == 1, "duplicate Spain_RadarCommandSet in CS.ini")
    dups = [n for n, k in counts.items() if k > 1]
    require(not dups, f"duplicate CommandSets: {dups[:8]}")

    factory = block(new_cs, "CommandSet", CS_SPAIN_FACTORY)
    require(used_slots(factory).get(15) == BTN_SPAIN_RADAR, "CS.ini factory slot 15")
    orig_factory_slots = used_slots(block(orig_cs, "CommandSet", CS_SPAIN_FACTORY))
    for n, btn in orig_factory_slots.items():
        require(
            used_slots(factory).get(n) == btn,
            f"Spain factory lost slot {n} {btn}",
        )

    spy = new[K_SPY].decode("latin1")
    spy_spain = block(spy, "CommandSet", CS_SPAIN_RADAR)
    require(used_slots(spy_spain).get(7) == BTN_SARAB, "spy Spain slot 7")
    require(used_slots(spy_spain).get(8) == BTN_LAMINA, "spy Spain slot 8")
    orig_spy = orig[K_SPY].decode("latin1")
    require(
        used_slots(block(orig_spy, "CommandSet", "NatoGM406CommandSet"))
        == used_slots(block(spy, "CommandSet", "NatoGM406CommandSet")),
        "spy overlay NATO radar edited",
    )
    for name in RADAR_SETS_18:
        require(
            used_slots(block(orig_spy, "CommandSet", name))
            == used_slots(block(spy, "CommandSet", name)),
            f"spy overlay {name} slots edited",
        )

    spain_ov = new[K_SPAIN_CS].decode("latin1")
    ov_factory = block(spain_ov, "CommandSet", CS_SPAIN_FACTORY)
    require(
        used_slots(ov_factory).get(15) == BTN_SPAIN_RADAR,
        "SpainMissiles overlay factory slot 15",
    )
    orig_ov = orig[K_SPAIN_CS].decode("latin1")
    orig_ov_slots = used_slots(block(orig_ov, "CommandSet", CS_SPAIN_FACTORY))
    for n, btn in orig_ov_slots.items():
        require(
            used_slots(ov_factory).get(n) == btn,
            f"SpainMissiles factory lost slot {n}",
        )
    require(
        block(orig_ov, "CommandSet", "NatoDozerCommandSet")
        == block(spain_ov, "CommandSet", "NatoDozerCommandSet"),
        "SpainMissiles NATO dozer edited",
    )

    cb = new[K_CB].decode("latin1")
    sarab_btn = block(cb, "CommandButton", BTN_SARAB)
    lam_btn = block(cb, "CommandButton", BTN_LAMINA)
    spain_btn = block(cb, "CommandButton", BTN_SPAIN_RADAR)
    require(f"Object        = {OBJ_SARAB}" in sarab_btn, "Sarab3 button object")
    require(f"Object        = {OBJ_LAMINA}" in lam_btn, "Lamina button object")
    require(f"Object        = {OBJ_SPAIN_RADAR}" in spain_btn, "Spain Radar button object")
    require("Command       = DOZER_CONSTRUCT" in spain_btn, "Spain Radar command")
    require("Command       = UNIT_BUILD" in sarab_btn, "Sarab3 command")
    require("Command       = UNIT_BUILD" in lam_btn, "Lamina command")

    uav = new[K_UAV].decode("latin1")
    s_obj = block(uav, "Object", OBJ_SARAB)
    l_obj = block(uav, "Object", OBJ_LAMINA)
    require(last_buildcost(s_obj) == "500", f"Sarab3 cost {last_buildcost(s_obj)}")
    require(last_buildcost(l_obj) == "5000", f"Lamina cost {last_buildcost(l_obj)}")
    require("Sarab3Locomotor" in s_obj, "Sarab3 loco")
    require("Sarab3Deathweapon" in s_obj, "Sarab3 wpn")
    require("Zil-375V8" in l_obj, "Lamina loco")
    require("Quds5Launching" in l_obj, "Lamina wpn")

    radar_obj = new[K_SPAIN_RADAR].decode("latin1")
    body = block(radar_obj, "Object", OBJ_SPAIN_RADAR)
    require(f"CommandSet          = {CS_SPAIN_RADAR}" in body, "Spain Radar object CS")
    require("Side             = Nato" in body, "Spain Radar Side")
    require("ProductionUpdate" in body, "Spain Radar ProductionUpdate")
    require("DefaultProductionExitUpdate" in body, "Spain Radar exit")
    require("RadarUpgrade" in body, "Spain Radar RadarUpgrade")
    require("SpecialPowerSpySatellite" not in body, "Spain Radar has spy sat")
    require("Model                   = Nat_RadarSt" in body, "Spain Radar model")

    pt = new[K_PT].decode("latin1")
    require("PlayerTemplate FactionSpain" not in pt, "unexpected FactionSpain")
    require("SPECTER_PATCH AA_COMBO_HIDE" in pt, "AA combo hide")

    nk_obj = new[K_NK_RADAR].decode("latin1")
    require(
        "CommandSet          = NorthKorea_RadarStationCommandSet" in nk_obj,
        "NK radar object CS",
    )


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def write_installer(out_dir: Path, hashes: dict[str, str]) -> None:
    bat = f"""@echo off
setlocal EnableExtensions
title SPECTER — Radar Sarab_3 + Lamina (19 countries)

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

set "NEED=_SPEC_DATA_ONE.big CommandSet.ini CommandButton.ini PlayerTemplate.ini"
for %%F in (%NEED%) do (
  if not exist "%~dp0%%F" (
    echo ERROR: %%F is not next to this script.
    pause
    exit /b 1
  )
)

findstr /C:"SPECTER_PATCH RADAR_SARAB_LAMINA_19" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is not the 19-country Sarab3/Lamina radar build.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH ISRAEL_GS" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Israel Global Store patch missing from CommandSet.ini.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH INDIA_NO_DRONES" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: India drone-removal patch missing from CommandSet.ini.
  pause
  exit /b 1
)

set "GAME_ROOT="
set "PARENT="
for %%I in ("%~dp0..") do set "PARENT=%%~fI"
if exist "%~dp0generals.exe" set "GAME_ROOT=%~dp0"
if not defined GAME_ROOT if exist "%~dp0Generals.exe" set "GAME_ROOT=%~dp0"
if not defined GAME_ROOT if exist "%PARENT%\\generals.exe" set "GAME_ROOT=%PARENT%\\"
if not defined GAME_ROOT if exist "%PARENT%\\Generals.exe" set "GAME_ROOT=%PARENT%\\"
if not defined GAME_ROOT (
  echo ERROR: generals.exe not found.
  echo Unzip into the folder that has generals.exe, then run this again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\\" set "GAME_ROOT=%GAME_ROOT%\\"

echo.
echo Copies ONLY DATA + CommandSet.ini + CommandButton.ini + PlayerTemplate.ini
echo Does NOT copy ART or 0_ overlays.
echo.

if not exist "%GAME_ROOT%Data\\INI" mkdir "%GAME_ROOT%Data\\INI"
copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandButton.ini" "%GAME_ROOT%Data\\INI\\CommandButton.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0PlayerTemplate.ini" "%GAME_ROOT%Data\\INI\\PlayerTemplate.ini" >nul
if errorlevel 1 goto :copyfail

findstr /C:"SPECTER_PATCH RADAR_SARAB_LAMINA_19" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Data\\INI\\CommandSet.ini was not replaced.
  pause
  exit /b 1
)

echo Installed:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\\INI\\CommandSet.ini
echo   %GAME_ROOT%Data\\INI\\CommandButton.ini
echo   %GAME_ROOT%Data\\INI\\PlayerTemplate.ini
echo.
echo SHA-256:
echo   DATA  {hashes['_SPEC_DATA_ONE.big']}
echo   CS    {hashes['CommandSet.ini']}
echo   CB    {hashes['CommandButton.ini']}
echo   PT    {hashes['PlayerTemplate.ini']}
echo.
echo Keep original ART and 0_ overlays. Zero Hour was not run.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed.
pause
exit /b 1
"""
    write_text(out_dir / "Install_RadarSarabLamina19.bat", bat)


def write_readme(out_dir: Path, hashes: dict[str, str]) -> None:
    text = f"""SPECTER — Radar Sarab_3 ($500) + Lamina ($5000) — 19 countries
==============================================================

Supersedes incomplete tag radar-sarab-lamina (Spain skipped). That release
is kept. This pack adds SpainRadarGM406 + Spain_RadarCommandSet.

Zero Hour was not run. Static INI/BIG validation only.

Install: unzip next to generals.exe, run Install_RadarSarabLamina19.bat.
Does not copy ART or 0_ overlays.

SHA-256
  DATA  {hashes['_SPEC_DATA_ONE.big']}
  CS    {hashes['CommandSet.ini']}
  CB    {hashes['CommandButton.ini']}
  PT    {hashes['PlayerTemplate.ini']}
  ZIP   {hashes.get(ZIP_NAME, '')}
"""
    write_text(out_dir / "README_INSTALL.txt", text)


def write_report(out_dir: Path, hashes: dict[str, str]) -> None:
    rows = []
    for label, cs_name, note in COUNTRY_ROWS:
        rows.append(
            f"| {label} | `{cs_name}` | "
            f"slot 7 `{BTN_SARAB}` yes; Object `{OBJ_SARAB}` BuildCost **500** | "
            f"slot 8 `{BTN_LAMINA}` yes; Object `{OBJ_LAMINA}` BuildCost **5000** | "
            f"yes | {note} |"
        )
    table = "\n".join(rows)
    text = f"""# Radar Sarab_3 ($500) + Lamina ($5000) — 19 countries

**Zero Hour was not run.** Static INI/BIG validation only.

Supersedes incomplete GitHub Release `radar-sarab-lamina` (Spain skipped).
That tag is kept. This pack is tag `radar-sarab-lamina-19`.

SAGE construct cost is Object `BuildCost` (CommandButton.ini has no Cost field).
`SpecterRadar_Sarab3` last-win BuildCost = 500.
`SpecterRadar_Lamina` last-win BuildCost = 5000.

## Spain (this pack's structural change)

Live DATA has no `FactionSpain`, no Spain dozer, no Spain Radar. Spain content
is `Spain_MissileFactory` with `Side = Nato`, constructed from
`NatoDozerCommandSet` slot 14. That dozer uses slots 1–18; adding Radar there
would replace an existing NATO button.

Spain-only Radar added:

- Object `SpainRadarGM406` — clone of `NatoRadarGM406` (model `Nat_RadarSt`,
  ProductionUpdate, DefaultProductionExitUpdate, RadarUpgrade).
- CommandSet `Spain_RadarCommandSet` — empty slots 7/8 get Sarab_3 / Lamina.
- Construct button `Command_ConstructSpainRadarGM406` on
  `Spain_MissileFactoryCommandSet` **empty slot 15** (CommandSet.ini and
  last-win `CommandSet_SpainMissiles.ini`).
- Spy Satellite special power omitted on the Spain clone.
- NATO Radar CS, NATO dozer, and other countries unchanged.
- No `FactionSpain` / combo entry created (would be a new playable country).

Access path: play NATO → build Spain Missile Factory (already on NATO dozer)
→ construct Spain Radar from factory slot 15 → produce Sarab_3 / Lamina.

SPECTER already puts `DOZER_CONSTRUCT` on non-dozer CommandSets (VT72B).
Zero Hour was not run, so factory-to-Radar placement is not in-game proven.

## North Korea

Previous pack already put both drones on `NorthKorea_RadarStationCommandSet`
slots 7/8. Kept. Shared Heron/MQ-4/Orlan/Shahed were never on NK radar and
were not added.

## 19-country static table

| Country | Radar CommandSet identified | Sarab_3 $500 | Lamina $5000 | Objects/deps valid | Notes |
| --- | --- | --- | --- | --- | --- |
{table}

## SHA-256

| File | SHA-256 |
| --- | --- |
| `_SPEC_DATA_ONE.big` | `{hashes.get('_SPEC_DATA_ONE.big', '')}` |
| `CommandSet.ini` | `{hashes.get('CommandSet.ini', '')}` |
| `CommandButton.ini` | `{hashes.get('CommandButton.ini', '')}` |
| `PlayerTemplate.ini` | `{hashes.get('PlayerTemplate.ini', '')}` |
| `{ZIP_NAME}` | `{hashes.get(ZIP_NAME, '')}` |
"""
    write_text(out_dir / "RADAR_SARAB_LAMINA_19_REPORT.md", text)


def main() -> None:
    require(SRC_BIG.is_file(), f"missing {SRC_BIG}")
    require(sha256(SRC_BIG.read_bytes()) == SRC_SHA, "source DATA sha mismatch")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    spain_obj = clone_spain_radar(orig[K_NATO_RADAR])
    new[K_SPAIN_RADAR] = spain_obj

    cs = orig[K_CS].decode("latin1")
    require(CS_SPAIN_RADAR not in cs, "Spain_RadarCommandSet already in CS.ini")
    nl = nl_of(cs)
    extra_cs = SPAIN_RADAR_CS.replace("\n", nl)
    cs = cs.rstrip() + nl + extra_cs
    cs_bytes = cs.encode("latin1")
    cs_bytes = patch_named_factory(cs_bytes)
    new[K_CS] = cs_bytes

    spy = orig[K_SPY].decode("latin1")
    require(CS_SPAIN_RADAR not in spy, "Spain_RadarCommandSet already in spy overlay")
    spy_nl = nl_of(spy)
    spy = spy.rstrip() + spy_nl + SPAIN_RADAR_CS.replace("\n", spy_nl)
    new[K_SPY] = spy.encode("latin1")

    new[K_SPAIN_CS] = patch_named_factory(orig[K_SPAIN_CS])

    cb = orig[K_CB].decode("latin1")
    require(BTN_SPAIN_RADAR not in cb, "Spain Radar button exists")
    cb_nl = nl_of(cb)
    extra_btn = SPAIN_RADAR_BTN.replace("\n", cb_nl)
    new[K_CB] = (cb.rstrip() + cb_nl + extra_btn).encode("latin1")

    validate(orig, new)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_blob = build_big(new)
    digest = sha256(out_blob)
    OUT_BIG.write_bytes(out_blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")

    hashes = {"_SPEC_DATA_ONE.big": digest}
    lines = [f"{digest}  _SPEC_DATA_ONE.big"]
    for name, key in (
        ("CommandSet.ini", K_CS),
        ("CommandButton.ini", K_CB),
        ("PlayerTemplate.ini", K_PT),
    ):
        (OUT_DIR / name).write_bytes(new[key])
        h = sha256(new[key])
        hashes[name] = h
        (OUT_DIR / f"{name}.sha256").write_text(h + "\n", encoding="ascii")
        lines.append(f"{h}  {name}")

    write_installer(OUT_DIR, hashes)
    write_readme(OUT_DIR, hashes)
    write_report(OUT_DIR, hashes)
    (OUT_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")

    zip_path = OUT_DIR / ZIP_NAME
    zip_names = (
        "_SPEC_DATA_ONE.big",
        "CommandSet.ini",
        "CommandButton.ini",
        "PlayerTemplate.ini",
        "Install_RadarSarabLamina19.bat",
        "README_INSTALL.txt",
        "RADAR_SARAB_LAMINA_19_REPORT.md",
        "SHA256SUMS.txt",
    )
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in zip_names:
            zf.write(OUT_DIR / name, arcname=name)
    zip_hash = sha256(zip_path.read_bytes())
    hashes[ZIP_NAME] = zip_hash
    write_readme(OUT_DIR, hashes)
    write_report(OUT_DIR, hashes)
    lines.append(f"{zip_hash}  {ZIP_NAME}")
    (OUT_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")
    (OUT_DIR / f"{ZIP_NAME}.sha256").write_text(zip_hash + "\n", encoding="ascii")

    print("DATA", digest)
    print("CS  ", hashes["CommandSet.ini"])
    print("CB  ", hashes["CommandButton.ini"])
    print("PT  ", hashes["PlayerTemplate.ini"])
    print("ZIP ", zip_hash)


if __name__ == "__main__":
    main()
