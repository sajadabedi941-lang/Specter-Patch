#!/usr/bin/env python3
"""Unified SPECTER installer: Global Store S-300 + 19-country Radar drones.

Lineage (already applied in order, not nested ZIPs):

  radar-sarab-lamina-19  BIG  bb42e2c1...
       └─ gs-s300        BIG  aa40e6d1...   (this pack's DATA)

gs-s300 patched only MIC shop files on top of the 19-country Radar DATA.
Diff vs radar-sarab-lamina-19 is exactly:

  CommandSet.ini
  CommandButton.ini
  CommandSet_ZZZZ_IraqMicToWfRadarAd.ini
  CommandButton_ZZZZ_IraqMicRadarAd.ini
  Iraq_MIC_RadarAdCopies.ini

SpainRadarGM406 / Spain_RadarCommandSet from radar-sarab-lamina-19 stay.

This script does not rebuild _SPEC_DATA_ONE.big. It copies the already
merged gs-s300 DATA, re-validates both feature sets, writes a combined
BAT that never copies ART or 0_ overlays, and zips
SPECTER_S300_RADAR_DRONES_INSTALL.zip.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "Release/GS_S300"
SRC_BIG = SRC_DIR / "_SPEC_DATA_ONE.big"
SRC_SHA = "aa40e6d1e68058becbe8d197a94c9ba05a5ef1af6bda25a14f5e82e9ea4ece53"
R19_BIG = ROOT / "Release/RADAR_SARAB_LAMINA_19/_SPEC_DATA_ONE.big"
R19_SHA = "bb42e2c1e96c7c41660540cb8cfd93f1633a41557dde1af349984ac9242b787e"
OUT_DIR = ROOT / "Release/S300_RADAR_DRONES"
ZIP_NAME = "SPECTER_S300_RADAR_DRONES_INSTALL.zip"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_PT = r"Data\INI\PlayerTemplate.ini"
K_UAV = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_COPIES = r"Data\INI\Object\Specter\Iraq Army\AirDefense\Iraq_MIC_RadarAdCopies.ini"
K_S300_SRC = r"Data\INI\Object\Specter\Arabic Alliance\AirDefense\Arb_S300.ini"
K_MIC_OV = r"Data\INI\CommandSet_ZZZZ_IraqMicToWfRadarAd.ini"
K_MIC_BTN = r"Data\INI\CommandButton_ZZZZ_IraqMicRadarAd.ini"
K_MIC_WF = r"Data\INI\CommandSet_ZZZZ_IraqMicToWf.ini"
K_MIC_EMPTY = r"Data\INI\CommandSet_ZZZZ_IraqMicToWfEmpty.ini"
K_SPY = r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini"
K_SPAIN_CS = r"Data\INI\CommandSet_SpainMissiles.ini"
K_SPAIN_RADAR = (
    r"Data\INI\Object\Specter\Spanish Armed Forces\Buildings\Spain_RadarGM406.ini"
)
K_GS5 = r"Data\INI\Object\Specter\GlobalStore\CountryGlobalStoresFive.ini"

BTN_SARAB = "Command_ConstructSpecterRadarSarab3"
BTN_LAMINA = "Command_ConstructSpecterRadarLamina"
BTN_S300 = "Command_ConstructIraq_MIC_S300"
BTN_PANTSIR = "Command_ConstructIraq_MIC_PantsirS1M"
OBJ_S300 = "Iraq_MIC_S300"
OBJ_SARAB = "SpecterRadar_Sarab3"
OBJ_LAMINA = "SpecterRadar_Lamina"
CS_SPAIN_RADAR = "Spain_RadarCommandSet"
BTN_SPAIN_RADAR = "Command_ConstructSpainRadarGM406"

MIC_SETS = ("Iraq_MICCommandSet", "Iraq_MICCommandSet2", "Iraq_MICCommandSet3")
RADAR_19 = (
    ("عربستان", "SaudiArabia_RadarCommandSet"),
    ("امارات", "UAE_RadarCommandSet"),
    ("سوریه", "Syria_RadarCommandSet"),
    ("هند", "India_RadarCommandSet"),
    ("پاکستان", "Pakistan_RadarCommandSet"),
    ("آفریقای جنوبی", "SouthAfrica_RadarCommandSet"),
    ("لیبی", "Libya_RadarCommandSet"),
    ("ترکیه", "TurkeyGM406CommandSet"),
    ("سوئد", "SwedenGM406CommandSet"),
    ("اوکراین", "UkraineGM406CommandSet"),
    ("ایتالیا", "ItalyGM406CommandSet"),
    ("بریتانیا", "BritainGM406CommandSet"),
    ("آلمان", "GermanyGM406CommandSet"),
    ("فرانسه", "FranceGM406CommandSet"),
    ("اسپانیا", CS_SPAIN_RADAR),
    ("ویتنام", "Vietnam_RadarStationCommandSet"),
    ("کره جنوبی", "SouthKorea_RadarStationCommandSet"),
    ("ژاپن", "Japan_RadarStationCommandSet"),
    ("کره شمالی", "NorthKorea_RadarStationCommandSet"),
)
GS_KEEP = {
    1: "Command_ConstructIraq_MIC_Arrow",
    2: "Command_ConstructIraq_MIC_AN_TPY2",
    3: "Command_ConstructIraq_MIC_92N6R",
    4: "Command_ConstructIraq_MIC_S400",
    6: "Command_ConstructIraq_MIC_Krasukha4",
    7: "Command_ConstructIraq_MIC_96L6TSP",
    8: "Command_ConstructIraq_MIC_S500",
    9: "Command_ConstructIraq_MIC_HQ9",
    10: "Command_ConstructIraq_MIC_HT233",
    11: "Command_ConstructIraq_MIC_TRML4D",
    12: "Command_ConstructIraq_MIC_IRIST",
    13: "Command_ConstructIraq_MIC_US_AN_TPY2",
    14: "Command_ConstructIraq_MIC_THAAD",
    15: "Command_Sell",
}
EXPECTED_DIFF = {
    K_CS,
    K_CB,
    K_MIC_OV,
    K_MIC_BTN,
    K_COPIES,
}


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


def last_buildcost(body: str) -> str | None:
    costs = re.findall(r"^\s*BuildCost\s*=\s*(\d+)", body, re.M)
    return costs[-1] if costs else None


def validate_merged(entries: dict[str, bytes], r19: dict[str, bytes]) -> None:
    require(sha256(SRC_BIG.read_bytes()) == SRC_SHA, "gs-s300 DATA sha mismatch")
    require(sha256(R19_BIG.read_bytes()) == R19_SHA, "radar-19 DATA sha mismatch")
    changed = [k for k in r19 if k in entries and r19[k] != entries[k]]
    added = [k for k in entries if k not in r19]
    removed = [k for k in r19 if k not in entries]
    require(not added, f"unexpected added files: {added}")
    require(not removed, f"unexpected removed files: {removed}")
    require(set(changed) == EXPECTED_DIFF, f"merge diff drifted: {changed}")

    cs = entries[K_CS].decode("latin1")
    loose_cs = (SRC_DIR / "CommandSet.ini").read_bytes()
    require(loose_cs == entries[K_CS], "loose CommandSet.ini != packed")
    require((SRC_DIR / "CommandButton.ini").read_bytes() == entries[K_CB], "loose CB")
    require((SRC_DIR / "PlayerTemplate.ini").read_bytes() == entries[K_PT], "loose PT")

    require("SPECTER_PATCH GS_S300" in cs, "GS_S300 marker")
    require("SPECTER_PATCH RADAR_SARAB_LAMINA_19" in cs, "Spain radar marker")
    require("SPECTER_PATCH RADAR_SARAB_LAMINA" in cs, "Sarab/Lamina marker")
    require("SPECTER_PATCH ISRAEL_GS" in cs, "Israel GS marker")
    require("SPECTER_PATCH INDIA_NO_DRONES" in cs, "India hide marker")
    require("SPECTER_PATCH AA_COMBO_HIDE" in entries[K_PT].decode("latin1"), "AA combo")

    ov = entries[K_MIC_OV].decode("latin1")
    copies = entries[K_COPIES].decode("latin1")
    for name in MIC_SETS:
        for label, txt in (("CS", cs), ("overlay", ov)):
            slots = used_slots(block(txt, "CommandSet", name))
            require(slots.get(5) == BTN_S300, f"{label} {name} slot 5")
            require(not active_has(block(txt, "CommandSet", name), BTN_PANTSIR), f"{label} {name} Pantsir")
            for n, btn in GS_KEEP.items():
                require(slots.get(n) == btn, f"{label} {name} lost {n}")

    s300 = block(copies, "Object", OBJ_S300)
    require(last_buildcost(s300) == "4500", f"Iraq_MIC_S300 cost {last_buildcost(s300)}")
    require("Side                 = Iraq" in s300, "Iraq_MIC_S300 Side")
    src = block(entries[K_S300_SRC].decode("latin1"), "Object", "Arabic_S300PMU2")
    require(last_buildcost(src) == "2000", "original S300 cost")
    pants = block(copies, "Object", "Iraq_MIC_PantsirS1M")
    require(last_buildcost(pants) == "4000", "Pantsir MIC cost")
    require(
        "Command_ConstructRussiaVehiclePantsirS1M"
        in block(cs, "CommandSet", "RussiaWarFactoryCommandSet"),
        "Russia WF Pantsir removed",
    )
    empty = entries[K_MIC_EMPTY].decode("latin1")
    wf = entries[K_MIC_WF].decode("latin1")
    require(BTN_PANTSIR not in empty and BTN_S300 not in empty, "Empty overlay polluted")
    require(BTN_PANTSIR not in wf, "Wf overlay gained Pantsir")

    israel = block(entries[K_GS5].decode("latin1"), "Object", "Israel_GlobalStore")
    require("CommandSet             = Iraq_MICCommandSet" in israel, "Israel GS shop")

    uav = entries[K_UAV].decode("latin1")
    require(last_buildcost(block(uav, "Object", OBJ_SARAB)) == "500", "Sarab_3 cost")
    require(last_buildcost(block(uav, "Object", OBJ_LAMINA)) == "5000", "Lamina cost")
    cb = entries[K_CB].decode("latin1")
    require(f"Object        = {OBJ_S300}" in block(cb, "CommandButton", BTN_S300), "S300 btn")
    require(f"Object        = {OBJ_SARAB}" in block(cb, "CommandButton", BTN_SARAB), "Sarab btn")
    require(f"Object        = {OBJ_LAMINA}" in block(cb, "CommandButton", BTN_LAMINA), "Lamina btn")

    spy = entries[K_SPY].decode("latin1")
    spain_ov = entries[K_SPAIN_CS].decode("latin1")
    require(K_SPAIN_RADAR in entries, "SpainRadarGM406 missing")
    require("Object SpainRadarGM406" in entries[K_SPAIN_RADAR].decode("latin1"), "Spain radar obj")
    require(
        used_slots(block(cs, "CommandSet", "Spain_MissileFactoryCommandSet")).get(15)
        == BTN_SPAIN_RADAR,
        "Spain factory slot 15",
    )
    require(
        used_slots(block(spain_ov, "CommandSet", "Spain_MissileFactoryCommandSet")).get(15)
        == BTN_SPAIN_RADAR,
        "Spain overlay factory slot 15",
    )
    india = block(cs, "CommandSet", "India_RadarCommandSet")
    require(not active_has(india, "Command_ConstructIndia_CombatDrone"), "India CombatDrone")
    require(active_has(india, "Command_ConstructSpecterRadarHeron"), "India Heron")
    require(active_has(india, "Command_ConstructSpecterRadarShahedLauncher"), "India Shahed")

    dups = [n for n, k in Counter(re.findall(r"^CommandSet (\S+)", cs, re.M)).items() if k > 1]
    require(not dups, f"duplicate CommandSets: {dups[:8]}")

    for label, name in RADAR_19:
        body = block(cs, "CommandSet", name)
        slots = used_slots(body)
        require(slots.get(7) == BTN_SARAB, f"{label} missing Sarab_3")
        require(slots.get(8) == BTN_LAMINA, f"{label} missing Lamina")
        require(
            not any("SpySatellite" in v for v in slots.values()),
            f"{label} Spy Satellite",
        )
        spy_body = block(spy, "CommandSet", name)
        spy_slots = used_slots(spy_body)
        require(spy_slots.get(7) == BTN_SARAB, f"spy {label} Sarab_3")
        require(spy_slots.get(8) == BTN_LAMINA, f"spy {label} Lamina")

    require(len(RADAR_19) == 19, "country table is not 19")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def write_installer(out_dir: Path, hashes: dict[str, str]) -> None:
    bat = f"""@echo off
setlocal EnableExtensions
title SPECTER — Global Store S-300 + Radar Sarab_3/Lamina

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

set "NEED=_SPEC_DATA_ONE.big CommandSet.ini CommandButton.ini PlayerTemplate.ini"
for %%F in (%NEED%) do (
  if not exist "%~dp0%%F" (
    echo ERROR: %%F is not next to this script. Unzip the full pack.
    pause
    exit /b 1
  )
)

findstr /C:"SPECTER_PATCH GS_S300" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is missing the Global Store S-300 patch.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH RADAR_SARAB_LAMINA_19" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is missing the 19-country Radar drone patch.
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
findstr /C:"5 = Command_ConstructIraq_MIC_S300" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Global Store slot 5 is not S-300.
  pause
  exit /b 1
)
findstr /C:"5 = Command_ConstructIraq_MIC_PantsirS1M" "%~dp0CommandSet.ini" >nul
if not errorlevel 1 (
  echo ERROR: Pantsir is still on Global Store slot 5. Incomplete pack.
  pause
  exit /b 1
)
findstr /C:"CommandSet Spain_RadarCommandSet" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Spain Radar CommandSet missing.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH AA_COMBO_HIDE" "%~dp0PlayerTemplate.ini" >nul
if errorlevel 1 (
  echo ERROR: PlayerTemplate.ini is not the expected lineage.
  pause
  exit /b 1
)

if exist "%~dp0_SPEC_ART_ONE.big" (
  echo ERROR: ART file found next to this script. This pack must not ship ART.
  pause
  exit /b 1
)
if exist "%~dp0_SPEC_ART_TWO.big" (
  echo ERROR: ART file found next to this script. This pack must not ship ART.
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
  echo Unzip SPECTER_S300_RADAR_DRONES_INSTALL.zip into the folder that
  echo has generals.exe, then run this script again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\\" set "GAME_ROOT=%GAME_ROOT%\\"

echo.
echo Copies ONLY DATA + CommandSet.ini + CommandButton.ini + PlayerTemplate.ini
echo Does NOT copy _SPEC_ART_ONE.big, _SPEC_ART_TWO.big, or 0_ overlays.
echo.

if exist "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big" (
  echo NOTE: existing 0_SPECTER_GlobalStoreCameos.big will NOT be replaced.
)
if exist "%GAME_ROOT%_SPEC_ART_ONE.big" (
  echo NOTE: existing _SPEC_ART_ONE.big will NOT be replaced.
)

if not exist "%GAME_ROOT%Data\\INI" mkdir "%GAME_ROOT%Data\\INI"
copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandButton.ini" "%GAME_ROOT%Data\\INI\\CommandButton.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0PlayerTemplate.ini" "%GAME_ROOT%Data\\INI\\PlayerTemplate.ini" >nul
if errorlevel 1 goto :copyfail

findstr /C:"SPECTER_PATCH GS_S300" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: installed CommandSet.ini missing GS S-300. Incomplete install.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH RADAR_SARAB_LAMINA_19" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: installed CommandSet.ini missing Radar drones. Incomplete install.
  pause
  exit /b 1
)
findstr /C:"5 = Command_ConstructIraq_MIC_S300" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: installed Global Store slot 5 is not S-300.
  pause
  exit /b 1
)
findstr /C:"5 = Command_ConstructIraq_MIC_PantsirS1M" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
if not errorlevel 1 (
  echo ERROR: installed CommandSet.ini still has Pantsir on GS slot 5.
  pause
  exit /b 1
)
findstr /C:"CommandSet Spain_RadarCommandSet" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: installed CommandSet.ini missing Spain Radar.
  pause
  exit /b 1
)

echo Installed both packs:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\\INI\\CommandSet.ini
echo   %GAME_ROOT%Data\\INI\\CommandButton.ini
echo   %GAME_ROOT%Data\\INI\\PlayerTemplate.ini
echo.
echo ART and 0_ overlays were not copied.
echo.
echo SHA-256:
echo   DATA  {hashes['_SPEC_DATA_ONE.big']}
echo   CS    {hashes['CommandSet.ini']}
echo   CB    {hashes['CommandButton.ini']}
echo   PT    {hashes['PlayerTemplate.ini']}
echo.
echo Zero Hour was not run. Static INI/BIG checks only.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed. Previous files were not fully replaced.
pause
exit /b 1
"""
    write_text(out_dir / "Install_S300RadarDrones.bat", bat)


def write_readme(out_dir: Path, hashes: dict[str, str]) -> None:
    text = f"""SPECTER — Global Store S-300 + Radar Sarab_3/Lamina
===================================================

One installer. Two already-merged patches. Not two ZIPs inside a ZIP.

Lineage: radar-sarab-lamina-19 then gs-s300 (MIC shop files only).

Zero Hour was not run. Static INI/BIG validation only.

Install
-------
1. Close Zero Hour.
2. Unzip {ZIP_NAME} next to generals.exe.
3. Run Install_S300RadarDrones.bat once.
4. Do not replace ART or 0_ overlays.

The BAT copies only DATA + CommandSet.ini + CommandButton.ini +
PlayerTemplate.ini. It refuses to run if ART is sitting next to it,
and it checks both GS S-300 and 19-country Radar markers before and
after copy.

SHA-256
-------
  DATA  {hashes['_SPEC_DATA_ONE.big']}
  CS    {hashes['CommandSet.ini']}
  CB    {hashes['CommandButton.ini']}
  PT    {hashes['PlayerTemplate.ini']}
  ZIP   {hashes.get(ZIP_NAME, '')}
"""
    write_text(out_dir / "README_INSTALL.txt", text)


def write_report(out_dir: Path, hashes: dict[str, str]) -> None:
    rows = []
    for label, cs_name in RADAR_19:
        rows.append(
            f"| {label} | `{cs_name}` | slot 7 `{BTN_SARAB}` **$500** | "
            f"slot 8 `{BTN_LAMINA}` **$5000** |"
        )
    table = "\n".join(rows)
    text = f"""# Unified pack: GS S-300 + 19-country Radar drones

**Zero Hour was not run.**

Merged lineage (not nested ZIPs):

`radar-sarab-lamina-19` (`{R19_SHA}`) → `gs-s300` (`{SRC_SHA}`)

gs-s300 changed only five MIC shop files. Spain Radar from
radar-sarab-lamina-19 is unchanged.

## Global Store

| Check | Result |
| --- | --- |
| Slot 5 | `Command_ConstructIraq_MIC_S300` |
| Object | `Iraq_MIC_S300` BuildCost **4500** |
| Pantsir on GS slot 5 | gone (CS.ini + last-win overlay) |
| `Iraq_MIC_PantsirS1M` / other-country Pantsir | kept |
| `Arabic_S300PMU2` cost | still 2000 |
| Other GS slots 1–4, 6–15 | unchanged |
| Israel GS shop | still `Iraq_MICCommandSet` |

## 19-country Radar

| Country | CommandSet | Sarab_3 | Lamina |
| --- | --- | --- | --- |
{table}

Spain uses `SpainRadarGM406` + `Spain_RadarCommandSet` from
radar-sarab-lamina-19. India CombatDrone stays commented. Shared
Heron/MQ-4/Orlan-10/Shahed and Spy Satellite removal stay.

## SHA-256

| File | SHA-256 |
| --- | --- |
| `_SPEC_DATA_ONE.big` | `{hashes.get('_SPEC_DATA_ONE.big', '')}` |
| `CommandSet.ini` | `{hashes.get('CommandSet.ini', '')}` |
| `CommandButton.ini` | `{hashes.get('CommandButton.ini', '')}` |
| `PlayerTemplate.ini` | `{hashes.get('PlayerTemplate.ini', '')}` |
| `{ZIP_NAME}` | `{hashes.get(ZIP_NAME, '')}` |
"""
    write_text(out_dir / "S300_RADAR_DRONES_REPORT.md", text)


def main() -> None:
    r19 = read_big(R19_BIG)
    entries = read_big(SRC_BIG)
    validate_merged(entries, r19)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    copies = (
        "_SPEC_DATA_ONE.big",
        "CommandSet.ini",
        "CommandButton.ini",
        "PlayerTemplate.ini",
    )
    hashes: dict[str, str] = {}
    lines: list[str] = []
    for name in copies:
        src = SRC_DIR / name
        dst = OUT_DIR / name
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        digest = sha256(dst.read_bytes())
        hashes[name] = digest
        (OUT_DIR / f"{name}.sha256").write_text(digest + "\n", encoding="ascii")
        lines.append(f"{digest}  {name}")
        if name == "_SPEC_DATA_ONE.big":
            require(digest == SRC_SHA, "copied DATA sha drifted")
        if name == "CommandSet.ini":
            require(dst.read_bytes() == entries[K_CS], "copied CS != packed")

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
        "Install_S300RadarDrones.bat",
        "README_INSTALL.txt",
        "S300_RADAR_DRONES_REPORT.md",
        "SHA256SUMS.txt",
    )
    artish = [
        p.name
        for p in OUT_DIR.iterdir()
        if p.name.startswith("0_") or "ART" in p.name.upper()
    ]
    require(not artish, f"ART/0_ files leaked into pack dir: {artish}")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in zip_names:
            require(
                "ART" not in name.upper() and not name.startswith("0_"),
                f"zip would include {name}",
            )
            zf.write(OUT_DIR / name, arcname=name)
        inner = [n for n in zf.namelist() if n.lower().endswith(".zip")]
        require(not inner, f"nested ZIP: {inner}")
    zip_hash = sha256(zip_path.read_bytes())
    hashes[ZIP_NAME] = zip_hash
    write_readme(OUT_DIR, hashes)
    write_report(OUT_DIR, hashes)
    lines.append(f"{zip_hash}  {ZIP_NAME}")
    (OUT_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")
    (OUT_DIR / f"{ZIP_NAME}.sha256").write_text(zip_hash + "\n", encoding="ascii")

    print("DATA", hashes["_SPEC_DATA_ONE.big"])
    print("CS  ", hashes["CommandSet.ini"])
    print("CB  ", hashes["CommandButton.ini"])
    print("PT  ", hashes["PlayerTemplate.ini"])
    print("ZIP ", zip_hash)
    print("wrote", zip_path, "bytes", zip_path.stat().st_size)


if __name__ == "__main__":
    main()
