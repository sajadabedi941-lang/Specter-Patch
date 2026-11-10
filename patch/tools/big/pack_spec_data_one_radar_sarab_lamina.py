#!/usr/bin/env python3
"""Add Iraq Sarab3 / Lamiaa copies to 18 country Radar menus.

Live originals (israel-india-fixes DATA):
  Object Iraq_Sarab3   (user name Sarab_3)  BuildCost 1100
    Button Command_ConstructIraq_Sarab3  image irq_sarab3
    KindOf ballistic/suicide drone, Sarab3Locomotor
  Object Iraq_Lamiaa   (user name Lamina)   last-win BuildCost 1600
    Button Command_ConstructIraq_Lamiaa  image irq_lamiaa
    KindOf VEHICLE, Zil-375V8, Iraq_Bm21CommandSet
    Iraq radar already produces both; Iraq is not a destination.

This packer clones those objects as:
  SpecterRadar_Sarab3   BuildCost 500
  SpecterRadar_Lamina   BuildCost 5000
and new UNIT_BUILD buttons. SAGE shows Object BuildCost on the
construct button (CommandButton.ini has no Cost field).

Destination Radar CommandSets (from live objects, not guessed):
  SaudiArabia_RadarCommandSet, UAE_RadarCommandSet, Syria_RadarCommandSet,
  India_RadarCommandSet, Pakistan_RadarCommandSet,
  SouthAfrica_RadarCommandSet, Libya_RadarCommandSet,
  TurkeyGM406CommandSet, SwedenGM406CommandSet, UkraineGM406CommandSet,
  ItalyGM406CommandSet, BritainGM406CommandSet, GermanyGM406CommandSet,
  FranceGM406CommandSet, Vietnam_RadarStationCommandSet,
  SouthKorea_RadarStationCommandSet, Japan_RadarStationCommandSet,
  NorthKorea_RadarStationCommandSet

Empty slots 7 and 8 are free on every destination set. Existing buttons
are not replaced. Spain has no live Radar CommandSet / radar building /
PlayerTemplate — skipped, not invented.

Also patches CommandSet_ZZZZ_SpySatelliteRadar.ini and
CommandSet_Pakistan.ini so overlays cannot drop the new slots.

Does not restore India CombatDrone/LoiteringDrone, Spy Satellite,
Israel Strategy Center, ART, or 0_ overlays. Does not edit Iraq originals.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/ISRAEL_INDIA_FIXES/_SPEC_DATA_ONE.big"
SRC_SHA = "52b1186bc552b02237751f3faabd2b3c24c67f2a3ffe69d312db8dfd9a5bc58e"
OUT_DIR = ROOT / "Release/RADAR_SARAB_LAMINA"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
ZIP_NAME = "SPECTER_RADAR_SARAB_LAMINA_INSTALL.zip"
MARKER = "SPECTER_PATCH RADAR_SARAB_LAMINA"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_PT = r"Data\INI\PlayerTemplate.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_UAV = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_SPY = r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini"
K_PK = r"Data\INI\CommandSet_Pakistan.ini"
K_SARAB_SRC = r"Data\INI\Object\Specter\Iraq Army\Drones\Sarab3.ini"
K_LAM_SRC = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Lamiaa.ini"
K_MAP = r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI"
K_LOCO = r"Data\INI\Locomotor.ini"

BTN_SARAB = "Command_ConstructSpecterRadarSarab3"
BTN_LAMINA = "Command_ConstructSpecterRadarLamina"
OBJ_SARAB = "SpecterRadar_Sarab3"
OBJ_LAMINA = "SpecterRadar_Lamina"

RADAR_SETS = (
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

KEEP_SHARED = (
    "Command_ConstructSpecterRadarHeron",
    "Command_ConstructSpecterRadarMQ4",
    "Command_ConstructSpecterRadarOrlan10",
    "Command_ConstructSpecterRadarShahedLauncher",
)

NEW_BUTTONS = f"""
CommandButton {BTN_SARAB}
  Command       = UNIT_BUILD
  Object        = {OBJ_SARAB}
  TextLabel     = CONTROLBAR:ConstructSarab3
  ButtonImage   = irq_sarab3
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipUSABuildSarab3
End
; {MARKER} displayed $500 from Object {OBJ_SARAB} BuildCost (CommandButton has no Cost field)

CommandButton {BTN_LAMINA}
  Command       = UNIT_BUILD
  Object        = {OBJ_LAMINA}
  TextLabel     = CONTROLBAR:ConstructIraq_Lamiaa
  ButtonImage   = irq_lamiaa
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipBuildIraq_Lamiaa
End
; {MARKER} displayed $5000 from Object {OBJ_LAMINA} BuildCost (CommandButton has no Cost field)
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


def add_slots(body: str) -> str:
    slots = used_slots(body)
    require(7 not in slots, f"slot 7 occupied: {slots.get(7)}")
    require(8 not in slots, f"slot 8 occupied: {slots.get(8)}")
    require(BTN_SARAB not in body, "Sarab3 already on this set")
    nl = nl_of(body)
    # Replace the CommandSet terminator only.
    m = re.search(r"^End\s*$", body, re.M)
    require(m is not None, "CommandSet End missing")
    insert = (
        f"  7 = {BTN_SARAB} ; {MARKER}{nl}"
        f"  8 = {BTN_LAMINA}{nl}"
    )
    return body[: m.start()] + insert + body[m.start() :]


def patch_named_sets(raw: bytes, names: tuple[str, ...]) -> bytes:
    text = raw.decode("latin1")
    for name in names:
        old = block(text, "CommandSet", name)
        new = add_slots(old)
        require(text.count(old) == 1, f"duplicate {name}")
        text = text.replace(old, new, 1)
    return text.encode("latin1")


def clone_sarab(src_file: bytes) -> str:
    text = src_file.decode("latin1")
    body = block(text, "Object", "Iraq_Sarab3")
    require("BuildCost               = 1100" in body, "Iraq_Sarab3 cost drifted")
    require("Locomotor = SET_NORMAL Sarab3Locomotor" in body, "Sarab3 locomotor")
    require("Weapon     = PRIMARY Sarab3Deathweapon" in body, "Sarab3 weapon")
    new = body.replace("Object Iraq_Sarab3", f"Object {OBJ_SARAB}", 1)
    new = new.replace(
        "  BuildCost               = 1100",
        "  BuildCost               = 500 ; " + MARKER,
        1,
    )
    require("Iraq_Sarab3" not in new.splitlines()[0], "name not changed")
    require("BuildCost               = 500" in new, "Sarab copy cost")
    return new.rstrip() + "\r\n\r\n"


def clone_lamina(src_file: bytes) -> str:
    text = src_file.decode("latin1")
    body = block(text, "Object", "Iraq_Lamiaa")
    require("BuildCost           = 500" in body, "Iraq_Lamiaa first cost")
    require("BuildCost       = 1600" in body, "Iraq_Lamiaa last-win cost")
    require("Locomotor = SET_NORMAL Zil-375V8" in body, "Lamiaa locomotor")
    require("Weapon = PRIMARY Quds5Launching" in body, "Lamiaa weapon")
    require("CommandSet            = Iraq_Bm21CommandSet" in body, "Lamiaa CS")
    new = body.replace("Object Iraq_Lamiaa", f"Object {OBJ_LAMINA}", 1)
    new = new.replace(
        "  BuildCost           = 500",
        "  BuildCost           = 5000 ; " + MARKER,
        1,
    )
    new = new.replace(
        "  BuildCost       = 1600",
        "  BuildCost       = 5000 ; " + MARKER,
        1,
    )
    require("BuildCost           = 5000" in new, "Lamina first cost")
    require("BuildCost       = 5000" in new, "Lamina last-win cost")
    require("BuildCost       = 1600" not in new, "Lamina still 1600")
    return new.rstrip() + "\r\n\r\n"


def patch_uav(raw: bytes, sarab_obj: str, lamina_obj: str) -> bytes:
    text = raw.decode("latin1")
    require("Object SpecterRadar_Heron" in text, "Heron missing")
    require("Object SpecterRadar_ShahedLauncher" in text, "Shahed missing")
    require(OBJ_SARAB not in text, "Sarab copy already in UAV file")
    header = (
        f"; {MARKER} copies of Iraq_Sarab3 / Iraq_Lamiaa for radar menus.\r\n"
        f"; Original Iraq objects and Iraq radar slots are unchanged.\r\n"
    )
    return (text.rstrip() + "\r\n\r\n" + header + sarab_obj + lamina_obj).encode("latin1")


def patch_cb(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    require("CommandButton Command_ConstructIraq_Sarab3" in text, "Iraq Sarab3 button")
    require("CommandButton Command_ConstructIraq_Lamiaa" in text, "Iraq Lamiaa button")
    require(BTN_SARAB not in text, "new Sarab3 button exists")
    nl = "\r\n" if "\r\n" in text else "\n"
    extra = NEW_BUTTONS.replace("\n", nl)
    return (text.rstrip() + nl + extra).encode("latin1")


def last_buildcost(body: str) -> str | None:
    costs = re.findall(r"^\s*BuildCost\s*=\s*(\d+)", body, re.M)
    return costs[-1] if costs else None


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_PT] == new[K_PT], "PlayerTemplate.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    require(orig[K_SARAB_SRC] == new[K_SARAB_SRC], "Iraq_Sarab3 source edited")
    require(orig[K_LAM_SRC] == new[K_LAM_SRC], "Iraq_Lamiaa source edited")
    require(orig[K_MAP] == new[K_MAP], "MappedImages changed")
    require(orig[K_LOCO] == new[K_LOCO], "Locomotor.ini changed")
    expected = {K_CS, K_CB, K_UAV, K_SPY, K_PK}
    changed = [k for k in orig if orig[k] != new[k]]
    require(set(changed) == expected, f"unexpected files changed: {changed}")

    orig_cs = orig[K_CS].decode("latin1")
    new_cs = new[K_CS].decode("latin1")
    require("SPECTER_PATCH ISRAEL_GS" in new_cs, "Israel GS lost")
    require("SPECTER_PATCH INDIA_NO_DRONES" in new_cs, "India drone hide lost")
    require(
        not active_has(
            block(new_cs, "CommandSet", "India_RadarCommandSet"),
            "Command_ConstructIndia_CombatDrone",
        ),
        "India CombatDrone restored",
    )
    require(
        not active_has(
            block(new_cs, "CommandSet", "India_RadarCommandSet"),
            "Command_SpySatelliteScan",
        ),
        "Spy Satellite on India radar",
    )
    iraq = block(new_cs, "CommandSet", "Iraq_RadarStationCommandSet")
    require(
        block(orig_cs, "CommandSet", "Iraq_RadarStationCommandSet") == iraq,
        "Iraq radar edited",
    )
    require("Command_ConstructIraq_Sarab3" in iraq, "Iraq lost Sarab3")
    require("Command_ConstructIraq_Lamiaa" in iraq, "Iraq lost Lamiaa")

    table = []
    for name in RADAR_SETS:
        body = block(new_cs, "CommandSet", name)
        slots = used_slots(body)
        require(slots.get(7) == BTN_SARAB, f"{name} slot 7")
        require(slots.get(8) == BTN_LAMINA, f"{name} slot 8")
        orig_slots = used_slots(block(orig_cs, "CommandSet", name))
        for n, btn in orig_slots.items():
            require(slots.get(n) == btn, f"{name} lost slot {n} {btn}")
        spy_sat = any("SpySatellite" in v for v in slots.values())
        require(not spy_sat, f"{name} gained Spy Satellite")
        shared_ok = True
        if name != "NorthKorea_RadarStationCommandSet":
            for keep in KEEP_SHARED:
                if keep in orig_slots.values():
                    require(keep in slots.values(), f"{name} lost {keep}")
        table.append(name)

    spy = new[K_SPY].decode("latin1")
    orig_spy = orig[K_SPY].decode("latin1")
    for name in RADAR_SETS:
        body = block(spy, "CommandSet", name)
        slots = used_slots(body)
        require(slots.get(7) == BTN_SARAB, f"spy {name} slot 7")
        require(slots.get(8) == BTN_LAMINA, f"spy {name} slot 8")
        orig_slots = used_slots(block(orig_spy, "CommandSet", name))
        for n, btn in orig_slots.items():
            require(slots.get(n) == btn, f"spy {name} lost slot {n}")

    pk = new[K_PK].decode("latin1")
    pk_radar = block(pk, "CommandSet", "Pakistan_RadarCommandSet")
    require(used_slots(pk_radar).get(7) == BTN_SARAB, "Pakistan.ini slot 7")
    require(used_slots(pk_radar).get(8) == BTN_LAMINA, "Pakistan.ini slot 8")

    cb = new[K_CB].decode("latin1")
    sarab_btn = block(cb, "CommandButton", BTN_SARAB)
    lam_btn = block(cb, "CommandButton", BTN_LAMINA)
    require(f"Object        = {OBJ_SARAB}" in sarab_btn, "Sarab3 button object")
    require("ButtonImage   = irq_sarab3" in sarab_btn, "Sarab3 image")
    require("Command       = UNIT_BUILD" in sarab_btn, "Sarab3 command")
    require(f"Object        = {OBJ_LAMINA}" in lam_btn, "Lamina button object")
    require("ButtonImage   = irq_lamiaa" in lam_btn, "Lamina image")
    require("CommandButton Command_ConstructIraq_Sarab3" in cb, "Iraq Sarab3 button deleted")
    require("CommandButton Command_ConstructIraq_Lamiaa" in cb, "Iraq Lamiaa button deleted")

    uav = new[K_UAV].decode("latin1")
    s_obj = block(uav, "Object", OBJ_SARAB)
    l_obj = block(uav, "Object", OBJ_LAMINA)
    require(last_buildcost(s_obj) == "500", f"Sarab3 cost {last_buildcost(s_obj)}")
    require(last_buildcost(l_obj) == "5000", f"Lamina cost {last_buildcost(l_obj)}")
    require("Sarab3Locomotor" in s_obj, "Sarab3 loco")
    require("Sarab3Deathweapon" in s_obj, "Sarab3 wpn")
    require("GenericSuicideDroneCommandSet" in s_obj, "Sarab3 unit CS")
    require("Zil-375V8" in l_obj, "Lamina loco")
    require("Quds5Launching" in l_obj, "Lamina wpn")
    require("Iraq_Bm21CommandSet" in l_obj, "Lamina unit CS")
    require("irq_sarab3" in s_obj, "Sarab3 portrait")
    require("irq_lamiaa" in l_obj, "Lamina portrait")

    orig_sarab = block(orig[K_SARAB_SRC].decode("latin1"), "Object", "Iraq_Sarab3")
    orig_lam = block(orig[K_LAM_SRC].decode("latin1"), "Object", "Iraq_Lamiaa")
    require(last_buildcost(orig_sarab) == "1100", "Iraq Sarab3 cost changed")
    require(last_buildcost(orig_lam) == "1600", "Iraq Lamiaa cost changed")

    wpn = new[K_WPN].decode("latin1")
    require("Weapon Sarab3Deathweapon" in wpn, "Sarab3Deathweapon missing")
    require("Weapon Quds5Launching" in wpn or True, "Quds5 check skip if named differently")
    require("Weapon Quds5Launching" in wpn, "Quds5Launching missing")
    loco = new[K_LOCO].decode("latin1")
    require("Locomotor Sarab3Locomotor" in loco, "Sarab3Locomotor missing")
    require("Locomotor Zil-375V8" in loco, "Zil-375V8 missing")
    mapped = new[K_MAP].decode("latin1")
    require("MappedImage irq_sarab3" in mapped, "irq_sarab3 mapping")
    require("MappedImage irq_lamiaa" in mapped, "irq_lamiaa mapping")

    pt = new[K_PT].decode("latin1")
    require("PlayerTemplate FactionSpain" not in pt, "unexpected FactionSpain")
    require("SPECTER_PATCH AA_COMBO_HIDE" in pt, "AA combo hide")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def write_installer(out_dir: Path, hashes: dict[str, str]) -> None:
    bat = f"""@echo off
setlocal EnableExtensions
title SPECTER — Radar Sarab_3 + Lamina

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

findstr /C:"SPECTER_PATCH RADAR_SARAB_LAMINA" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is not the Sarab3/Lamina radar build.
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

findstr /C:"SPECTER_PATCH RADAR_SARAB_LAMINA" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
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
    write_text(out_dir / "Install_RadarSarabLamina.bat", bat)


def write_readme(out_dir: Path, hashes: dict[str, str]) -> None:
    text = f"""SPECTER — Radar Sarab_3 ($500) + Lamina ($5000)
================================================

Adds copies of Iraq_Sarab3 and Iraq_Lamiaa to 18 country Radar menus
on empty slots 7 and 8. Spain has no live Radar in this DATA (no
PlayerTemplate, no radar building, no Radar CommandSet) and was not
invented.

Zero Hour was not run. Static INI/BIG validation only.

Install: unzip next to generals.exe, run Install_RadarSarabLamina.bat.
Does not copy ART or 0_ overlays.

SHA-256
  DATA  {hashes['_SPEC_DATA_ONE.big']}
  CS    {hashes['CommandSet.ini']}
  CB    {hashes['CommandButton.ini']}
  PT    {hashes['PlayerTemplate.ini']}
  ZIP   {hashes.get(ZIP_NAME, '')}
"""
    write_text(out_dir / "README_INSTALL.txt", text)


COUNTRY_ROWS = (
    ("عربستان", "SaudiArabia_RadarCommandSet", True),
    ("امارات", "UAE_RadarCommandSet", True),
    ("سوریه", "Syria_RadarCommandSet", True),
    ("هند", "India_RadarCommandSet", True),
    ("پاکستان", "Pakistan_RadarCommandSet", True),
    ("آفریقای جنوبی", "SouthAfrica_RadarCommandSet", True),
    ("لیبی", "Libya_RadarCommandSet", True),
    ("ترکیه", "TurkeyGM406CommandSet", True),
    ("سوئد", "SwedenGM406CommandSet", True),
    ("اوکراین", "UkraineGM406CommandSet", True),
    ("ایتالیا", "ItalyGM406CommandSet", True),
    ("بریتانیا", "BritainGM406CommandSet", True),
    ("آلمان", "GermanyGM406CommandSet", True),
    ("فرانسه", "FranceGM406CommandSet", True),
    ("اسپانیا", None, False),
    ("ویتنام", "Vietnam_RadarStationCommandSet", True),
    ("کره جنوبی", "SouthKorea_RadarStationCommandSet", True),
    ("ژاپن", "Japan_RadarStationCommandSet", True),
    ("کره شمالی", "NorthKorea_RadarStationCommandSet", True),
)


def write_report(out_dir: Path, hashes: dict[str, str]) -> None:
    rows = []
    for label, cs_name, patched in COUNTRY_ROWS:
        if not patched:
            rows.append(
                f"| {label} | **no live Radar CommandSet / radar building / PlayerTemplate** "
                f"(only `Spain_MissileFactoryCommandSet`) | — | — | — | "
                f"skipped; no CS invented |"
            )
            continue
        rows.append(
            f"| {label} | `{cs_name}` yes (from radar Object) | "
            f"slot 7 `{BTN_SARAB}` yes; Object `{OBJ_SARAB}` BuildCost **500** | "
            f"slot 8 `{BTN_LAMINA}` yes; Object `{OBJ_LAMINA}` BuildCost **5000** | "
            f"yes (cloned from Iraq originals; weapon/loco/mapped image present) | "
            f"no duplicate in CommandSet.ini; spy overlay + Pakistan.ini dual-patched |"
        )
    table = "\n".join(rows)
    text = f"""# Radar Sarab_3 ($500) + Lamina ($5000)

**Zero Hour was not run.** Static INI/BIG validation only.

SAGE construct cost is Object `BuildCost` (CommandButton.ini has no Cost field).
`SpecterRadar_Sarab3` last-win BuildCost = 500.
`SpecterRadar_Lamina` last-win BuildCost = 5000.
Iraq originals (`Iraq_Sarab3` 1100, `Iraq_Lamiaa` 1600) unchanged.

Empty slots 7 and 8 only. No existing Radar buttons replaced.
India CombatDrone / LoiteringDrone stay commented. Spy Satellite stays gone.
Israel GS marker kept. Shared Heron / MQ-4 / Orlan-10 / Shahed kept where they
already existed (North Korea radar never had them; they were not added).

Spain: no live Radar in this DATA. Not invented.

## 19-country static table

| Country | Radar CommandSet identified | Sarab_3 $500 | Lamina $5000 | Objects/deps valid | Duplicate CS / unwanted override |
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
    write_text(out_dir / "RADAR_SARAB_LAMINA_REPORT.md", text)


def main() -> None:
    require(SRC_BIG.is_file(), f"missing {SRC_BIG}")
    require(sha256(SRC_BIG.read_bytes()) == SRC_SHA, "source DATA sha mismatch")
    orig = read_big(SRC_BIG)
    sarab_obj = clone_sarab(orig[K_SARAB_SRC])
    lamina_obj = clone_lamina(orig[K_LAM_SRC])
    new = dict(orig)
    new[K_UAV] = patch_uav(orig[K_UAV], sarab_obj, lamina_obj)
    new[K_CB] = patch_cb(orig[K_CB])
    new[K_CS] = patch_named_sets(orig[K_CS], RADAR_SETS)
    new[K_SPY] = patch_named_sets(orig[K_SPY], RADAR_SETS)
    new[K_PK] = patch_named_sets(orig[K_PK], ("Pakistan_RadarCommandSet",))
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
        "Install_RadarSarabLamina.bat",
        "README_INSTALL.txt",
        "RADAR_SARAB_LAMINA_REPORT.md",
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
