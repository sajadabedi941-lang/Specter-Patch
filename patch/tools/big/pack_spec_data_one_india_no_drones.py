#!/usr/bin/env python3
"""India only: remove India UAV production from live CommandSets.

Identified live (israel-gs-strategy DATA, SHA df81c16b...):

  Object India_CombatDrone     KindOf AIRCRAFT DRONE  Side=India
  Object India_LoiteringDrone  KindOf AIRCRAFT DRONE  Side=India
  Object India_HeavyUAV        KindOf AIRCRAFT DRONE  Side=India  (no construct button)

Production (ControlBar = Data\\INI\\CommandSet.ini):
  India_RadarCommandSet          slot 1 CombatDrone, slot 2 LoiteringDrone
  India_HeavyAirBaseCommandSet   slot 3 CombatDrone, slot 4 LoiteringDrone
  CommandSet_ZZZZ_SpySatelliteRadar.ini redefines India_RadarCommandSet
    with the same two slots (patched so last-win cannot restore them)

Not India player UAVs (left untouched):
  IndiaInfantryDroneOperatorFPV / IndiaInfantryLancetTeam (INFANTRY)
  India_AD_AntiDrone (air defense)
  India_Systems.ini dummy DRONE KindOf (powers bar / missile internals)
  SpecterRadar Heron / MQ4 / Orlan / Shahed on India radar (shared)
  manned aircraft on Heavy Air Base
  other countries' CombatDrone buttons / radar menus

This packer comments the four production slots, sets Buildable=No on the
three drone objects, and does not edit CommandButton.ini, ART, 0_ overlays,
Weapon.ini, or other countries.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/ISRAEL_GS/_SPEC_DATA_ONE.big"
SRC_SHA = "df81c16bfbfc4c1b666056e3e9c2ce0a8237fa68e3d90fa54f0f499c05d95b46"
OUT_DIR = ROOT / "Release/INDIA_NO_DRONES"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
ZIP_NAME = "INDIA_NO_DRONES_INSTALL.zip"
MARKER = "SPECTER_PATCH INDIA_NO_DRONES"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_PT = r"Data\INI\PlayerTemplate.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_UAV = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_VN = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_RadarStation.ini"
)
K_SPY = r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini"
K_COMBAT = r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_CombatDrone.ini"
K_LOITER = r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_LoiteringDrone.ini"
K_HEAVY = r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_HeavyUAV.ini"
K_RADAR_OBJ = r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_RadarStation.ini"
K_HAB_OBJ = r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_HeavyAirBase.ini"
K_AIRFIELD = r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_Airfield_T.ini"

DRONE_FILES = (K_COMBAT, K_LOITER, K_HEAVY)

UNTOUCHED_RADARS = (
    "Pakistan_RadarCommandSet",
    "UAE_RadarCommandSet",
    "Syria_RadarCommandSet",
    "SaudiArabia_RadarCommandSet",
    "Libya_RadarCommandSet",
    "SouthAfrica_RadarCommandSet",
    "Iraq_RadarStationCommandSet",
    "Vietnam_RadarStationCommandSet",
    "AmericaRadarStationCommandSet",
    "IsraelRadarStationCommandSet",
)

UNTOUCHED_INDIA = (
    "IndiaDozerCommandSet",
    "India_AirfieldCommandSet",
    "India_BarracksCommandSet",
    "India_WarFactoryCommandSet",
    "India_CommandCenterCommandSet",
    "India_MissileFactoryCommandSet",
    "India_WorkerCommandSet",
    "India_VT72BCommandSet",
)


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


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def active_slot_lines(cs_body: str) -> list[str]:
    lines = []
    for line in cs_body.splitlines():
        s = line.strip()
        if not s or s.startswith(";") or s.startswith("CommandSet") or s == "End":
            continue
        lines.append(s)
    return lines


def patch_commandsets(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    radar = block(text, "CommandSet", "India_RadarCommandSet")
    hab = block(text, "CommandSet", "India_HeavyAirBaseCommandSet")
    require("Command_ConstructIndia_CombatDrone" in radar, "radar missing CombatDrone")
    require("Command_ConstructIndia_LoiteringDrone" in radar, "radar missing LoiteringDrone")
    require("Command_ConstructSpecterRadarShahedLauncher" in radar, "radar missing Shahed")
    require("Command_ConstructIndia_CombatDrone" in hab, "HAB missing CombatDrone")
    require("Command_ConstructIndia_Mi-8T" in hab, "HAB missing Mi-8")

    new_radar = radar.replace(
        "  1 = Command_ConstructIndia_CombatDrone\r\n"
        "  2 = Command_ConstructIndia_LoiteringDrone\r\n",
        "  ;1 = Command_ConstructIndia_CombatDrone ; " + MARKER + "\r\n"
        "  ;2 = Command_ConstructIndia_LoiteringDrone\r\n",
        1,
    )
    new_hab = hab.replace(
        "  3 = Command_ConstructIndia_CombatDrone\r\n"
        "  4 = Command_ConstructIndia_LoiteringDrone\r\n",
        "  ;3 = Command_ConstructIndia_CombatDrone ; " + MARKER + "\r\n"
        "  ;4 = Command_ConstructIndia_LoiteringDrone\r\n",
        1,
    )
    require(new_radar != radar, "radar block unchanged")
    require(new_hab != hab, "HAB block unchanged")
    require(MARKER in new_radar, "radar marker")
    require(text.count(radar) == 1, "duplicate India_RadarCommandSet")
    require(text.count(hab) == 1, "duplicate India_HeavyAirBaseCommandSet")
    text = text.replace(radar, new_radar, 1).replace(hab, new_hab, 1)
    return text.encode("latin1")


def patch_spy_radar(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    radar = block(text, "CommandSet", "India_RadarCommandSet")
    require("Command_ConstructIndia_CombatDrone" in radar, "spy radar missing CombatDrone")
    new_radar = radar.replace(
        "  1 = Command_ConstructIndia_CombatDrone\r\n"
        "  2 = Command_ConstructIndia_LoiteringDrone\r\n",
        "  ;1 = Command_ConstructIndia_CombatDrone ; " + MARKER + "\r\n"
        "  ;2 = Command_ConstructIndia_LoiteringDrone\r\n",
        1,
    )
    require(new_radar != radar, "spy radar unchanged")
    require(text.count(radar) == 1, "duplicate spy India_RadarCommandSet")
    return text.replace(radar, new_radar, 1).encode("latin1")


def patch_drone_object(raw: bytes, object_name: str, kindof_line: str) -> bytes:
    text = raw.decode("latin1")
    body = block(text, "Object", object_name)
    require(kindof_line in body, f"{object_name} KindOf mismatch")
    require("Buildable" not in body, f"{object_name} already has Buildable")
    insert = kindof_line + "\r\n  Buildable              = No ; " + MARKER
    new_body = body.replace(kindof_line, insert, 1)
    require(text.count(body) == 1, f"duplicate {object_name}")
    return text.replace(body, new_body, 1).encode("latin1")


def construct_buttons_active(cs_text: str, button: str) -> list[str]:
    hits = []
    names = re.findall(r"^CommandSet (\S+)", cs_text, re.M)
    for name in names:
        body = block(cs_text, "CommandSet", name)
        for line in body.splitlines():
            s = line.strip()
            if s.startswith(";") or not s:
                continue
            if button in s:
                hits.append(name)
    return hits


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_CB] == new[K_CB], "CommandButton.ini changed")
    require(orig[K_PT] == new[K_PT], "PlayerTemplate.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    require(orig[K_UAV] == new[K_UAV], "Shahed UAV file changed")
    require(orig[K_VN] == new[K_VN], "Vietnam radar changed")
    require(orig[K_RADAR_OBJ] == new[K_RADAR_OBJ], "India radar object changed")
    require(orig[K_HAB_OBJ] == new[K_HAB_OBJ], "India Heavy Air Base object changed")
    require(orig[K_AIRFIELD] == new[K_AIRFIELD], "India airfield object changed")

    expected = {K_CS, K_SPY, *DRONE_FILES}
    changed = [k for k in orig if orig[k] != new[k]]
    require(set(changed) == expected, f"unexpected files changed: {changed}")
    require(set(orig) == set(new), "BIG entry set changed")

    orig_cs = orig[K_CS].decode("latin1")
    new_cs = new[K_CS].decode("latin1")
    radar = block(new_cs, "CommandSet", "India_RadarCommandSet")
    hab = block(new_cs, "CommandSet", "India_HeavyAirBaseCommandSet")
    require(MARKER in radar, "radar marker missing")
    require(MARKER in hab, "HAB marker missing")
    require(
        construct_buttons_active(new_cs, "Command_ConstructIndia_CombatDrone") == [],
        "CombatDrone still on an active CommandSet slot",
    )
    require(
        construct_buttons_active(new_cs, "Command_ConstructIndia_LoiteringDrone") == [],
        "LoiteringDrone still on an active CommandSet slot",
    )

    active_radar = " ".join(active_slot_lines(radar))
    require("Command_ConstructSpecterRadarHeron" in active_radar, "Heron removed")
    require("Command_ConstructSpecterRadarMQ4" in active_radar, "MQ4 removed")
    require("Command_ConstructSpecterRadarOrlan10" in active_radar, "Orlan removed")
    require("Command_ConstructSpecterRadarShahedLauncher" in active_radar, "Shahed removed")
    require("Command_SetRallyPoint" in active_radar, "radar rally")
    require("Command_Sell" in active_radar, "radar sell")
    require("Command_ConstructIndia_CombatDrone" not in active_radar, "radar CombatDrone live")
    require("Command_ConstructIndia_LoiteringDrone" not in active_radar, "radar Loitering live")

    active_hab = " ".join(active_slot_lines(hab))
    for keep in (
        "Command_ConstructIndia_Mi-8T",
        "Command_ConstructIndia_IL-76",
        "Command_ConstructIndiaJetTu22M3M",
        "Command_ConstructIndiaJetB2A",
        "Command_ConstructIndiaHelicopterKA52",
        "Command_SetRallyPoint",
        "Command_Sell",
    ):
        require(keep in active_hab, f"HAB lost {keep}")
    require("Command_ConstructIndia_CombatDrone" not in active_hab, "HAB CombatDrone live")
    require("Command_ConstructIndia_LoiteringDrone" not in active_hab, "HAB Loitering live")

    for name in UNTOUCHED_RADARS + UNTOUCHED_INDIA:
        require(
            block(orig_cs, "CommandSet", name) == block(new_cs, "CommandSet", name),
            f"{name} edited",
        )

    # Israel GS + AA combo hide lineage
    require(
        "Command_ConstructIsrael_GlobalStore ; SPECTER_PATCH ISRAEL_GS"
        in block(new_cs, "CommandSet", "AirF_AmericaDozerCommandSet"),
        "Israel GS slot lost",
    )
    pt = new[K_PT].decode("latin1")
    require("SPECTER_PATCH AA_COMBO_HIDE" in block(pt, "PlayerTemplate", "FactionGLA"), "AA hide")
    uav = block(new[K_UAV].decode("latin1"), "Object", "SpecterRadar_ShahedLauncher")
    require("BuildCost       = 8000" in uav, "Shahed cost")
    require("IranShahed136FireCommandSet" in uav, "Shahed Fire")
    require("TriggeredBy   = Upgrade_AmericaRadar" in new[K_VN].decode("latin1"), "VN radar")

    spy = new[K_SPY].decode("latin1")
    orig_spy = orig[K_SPY].decode("latin1")
    spy_radar = block(spy, "CommandSet", "India_RadarCommandSet")
    require(MARKER in spy_radar, "spy overlay marker")
    require(
        construct_buttons_active(spy, "Command_ConstructIndia_CombatDrone") == [],
        "spy overlay still produces CombatDrone",
    )
    for name in re.findall(r"^CommandSet (\S+)", orig_spy, re.M):
        if name == "India_RadarCommandSet":
            continue
        require(
            block(orig_spy, "CommandSet", name) == block(spy, "CommandSet", name),
            f"spy overlay edited {name}",
        )

    cb = new[K_CB].decode("latin1")
    require("CommandButton Command_ConstructIndia_CombatDrone" in cb, "CombatDrone button deleted")
    require("CommandButton Command_ConstructPakistan_CombatDrone" in cb, "Pakistan button")
    require(
        "CommandButton Command_ConstructIndiaInfantryDroneOperatorFPV" in cb,
        "FPV infantry button deleted",
    )

    for key, obj_name in (
        (K_COMBAT, "India_CombatDrone"),
        (K_LOITER, "India_LoiteringDrone"),
        (K_HEAVY, "India_HeavyUAV"),
    ):
        body = block(new[key].decode("latin1"), "Object", obj_name)
        require("Buildable              = No ; " + MARKER in body, f"{obj_name} not unbuildable")
        orig_body = block(orig[key].decode("latin1"), "Object", obj_name)
        stripped = body.replace("\r\n  Buildable              = No ; " + MARKER, "", 1)
        require(stripped == orig_body, f"{obj_name} extra object edits")

    # No other CommandSet file still actively produces the two construct buttons.
    for key, blob in new.items():
        if "commandset" not in key.lower():
            continue
        txt = blob.decode("latin1")
        if "CommandSet " not in txt:
            continue
        for btn in (
            "Command_ConstructIndia_CombatDrone",
            "Command_ConstructIndia_LoiteringDrone",
        ):
            hits = construct_buttons_active(txt, btn)
            require(hits == [], f"{btn} still active in {key}: {hits}")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def write_installer(out_dir: Path, hashes: dict[str, str]) -> None:
    bat = f"""@echo off
setlocal EnableExtensions
title SPECTER — remove India drones

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

findstr /C:"SPECTER_PATCH INDIA_NO_DRONES" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini in this pack is not the India-drone removal build.
  pause
  exit /b 1
)

findstr /C:"SPECTER_PATCH ISRAEL_GS" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is not the Israel Global Store lineage this pack needs.
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
  echo Unzip into the Zero Hour / SPECTER folder that has generals.exe,
  echo then run this script again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\\" set "GAME_ROOT=%GAME_ROOT%\\"

echo.
echo Copying ONLY _SPEC_DATA_ONE.big is not enough.
echo SPECTER already has Data\\INI\\CommandSet.ini as a loose file.
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

findstr /C:"SPECTER_PATCH INDIA_NO_DRONES" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
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
echo India CombatDrone / LoiteringDrone / HeavyUAV cannot be built.
echo Keep 0_ overlays and original ART. Do not replace ART.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed.
pause
exit /b 1
"""
    write_text(out_dir / "Install_IndiaNoDrones.bat", bat)


def write_readme(out_dir: Path, hashes: dict[str, str]) -> None:
    text = f"""SPECTER — India: remove country drones
======================================

Removed from India's production menus
-------------------------------------
- India_CombatDrone          (Command_ConstructIndia_CombatDrone)
- India_LoiteringDrone       (Command_ConstructIndia_LoiteringDrone)
- India_HeavyUAV             (object only; was not on a menu)

Taken off:
  India_RadarCommandSet          slots 1 and 2
  India_HeavyAirBaseCommandSet   slots 3 and 4

Left on India radar: Heron / MQ-4 / Orlan-10 / Shahed launcher,
Sell, Rally. Manned aircraft on Heavy Air Base stay. Infantry FPV
operator, Lancet team, Anti-Drone AD, other countries, ART, and
0_ overlays are unchanged.

Install (required)
------------------
1. Close Zero Hour.
2. Unzip {ZIP_NAME} into the game folder (generals.exe) or next to it.
3. Run Install_IndiaNoDrones.bat.
4. Keep 0_SPECTER_GlobalStoreCameos.big and original ART.

Zero Hour was not run. Static validation is not an in-game screenshot.

SHA-256
-------
  DATA  {hashes['_SPEC_DATA_ONE.big']}
  CS    {hashes['CommandSet.ini']}
  CB    {hashes['CommandButton.ini']}
  PT    {hashes['PlayerTemplate.ini']}
  ZIP   {hashes.get(ZIP_NAME, '(see SHA256SUMS.txt)')}
"""
    write_text(out_dir / "README_INSTALL.txt", text)


def write_report(out_dir: Path, hashes: dict[str, str]) -> None:
    text = f"""# India: remove country UAVs from production

**Zero Hour was not run.** Static INI / BIG validation is not an in-game
screenshot.

## Identified India drones (Side=India, KindOf includes AIRCRAFT DRONE)

| Object | File | Construct button | Produced from |
| --- | --- | --- | --- |
| `India_CombatDrone` | `Drones\\India_CombatDrone.ini` | `Command_ConstructIndia_CombatDrone` | Radar slot 1, Heavy Air Base slot 3 |
| `India_LoiteringDrone` | `Drones\\India_LoiteringDrone.ini` | `Command_ConstructIndia_LoiteringDrone` | Radar slot 2, Heavy Air Base slot 4 |
| `India_HeavyUAV` | `Drones\\India_HeavyUAV.ini` | none | not on any live CommandSet |

Overlay: `CommandSet_ZZZZ_SpySatelliteRadar.ini` redefined
`India_RadarCommandSet` with the same Combat/Loitering slots.

## Not removed

- `IndiaInfantryDroneOperatorFPV`, `IndiaInfantryLancetTeam` (INFANTRY)
- `India_AD_AntiDrone` (air defense)
- `India_Systems.ini` dummy DRONE KindOf objects
- Specter radar UAVs on India radar (Heron, MQ-4, Orlan-10, Shahed)
- Heavy Air Base manned aircraft (Mi-8T, IL-76, Tu-22M3M, B-2A, Ka-52)
- Other countries' drone buttons and radar menus
- ART / `0_` overlays / weapons / stats of unrelated units

## Fix

Comment out the four production slots. Set `Buildable = No` on the three
drone objects. CommandButton.ini is unchanged (buttons unused).

## SHA-256

| File | SHA-256 |
| --- | --- |
| `_SPEC_DATA_ONE.big` | `{hashes['_SPEC_DATA_ONE.big']}` |
| `CommandSet.ini` | `{hashes['CommandSet.ini']}` |
| `CommandButton.ini` | `{hashes['CommandButton.ini']}` |
| `PlayerTemplate.ini` | `{hashes['PlayerTemplate.ini']}` |
| `{ZIP_NAME}` | `{hashes.get(ZIP_NAME, '')}` |
"""
    write_text(out_dir / "INDIA_NO_DRONES_REPORT.md", text)


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    blob = SRC_BIG.read_bytes()
    require(sha256(blob) == SRC_SHA, "source BIG sha mismatch")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    new[K_CS] = patch_commandsets(orig[K_CS])
    new[K_SPY] = patch_spy_radar(orig[K_SPY])
    new[K_COMBAT] = patch_drone_object(
        orig[K_COMBAT],
        "India_CombatDrone",
        "  KindOf                 = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT DRONE",
    )
    new[K_LOITER] = patch_drone_object(
        orig[K_LOITER],
        "India_LoiteringDrone",
        "  KindOf                 = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT DRONE",
    )
    new[K_HEAVY] = patch_drone_object(
        orig[K_HEAVY],
        "India_HeavyUAV",
        "  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT CAN_ATTACK DRONE",
    )
    validate(orig, new)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_blob = build_big(new)
    digest = sha256(out_blob)
    OUT_BIG.write_bytes(out_blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")

    hashes: dict[str, str] = {"_SPEC_DATA_ONE.big": digest}
    copies = (
        ("CommandSet.ini", K_CS),
        ("CommandButton.ini", K_CB),
        ("PlayerTemplate.ini", K_PT),
    )
    lines = [f"{digest}  _SPEC_DATA_ONE.big"]
    for name, key in copies:
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
        "Install_IndiaNoDrones.bat",
        "README_INSTALL.txt",
        "INDIA_NO_DRONES_REPORT.md",
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

    print("wrote", OUT_BIG, "bytes", len(out_blob), "sha256", digest)
    print("CS", hashes["CommandSet.ini"])
    print("CB", hashes["CommandButton.ini"])
    print("PT", hashes["PlayerTemplate.ini"])
    print("ZIP", zip_hash)
    print("--- India_RadarCommandSet ---")
    print(block(new[K_CS].decode("latin1"), "CommandSet", "India_RadarCommandSet"))
    print("--- India_HeavyAirBaseCommandSet ---")
    print(block(new[K_CS].decode("latin1"), "CommandSet", "India_HeavyAirBaseCommandSet"))


if __name__ == "__main__":
    main()
