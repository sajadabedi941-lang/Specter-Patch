#!/usr/bin/env python3
"""Unified SPECTER installer for Israel Global Store + India UAV removal.

Source DATA is the india-no-drones pack, which was built on the
israel-gs-strategy BIG. Static checks (not an in-game run):

  Israel: AirF_AmericaDozerCommandSet slot 2
          = Command_ConstructIsrael_GlobalStore
  India:  India_RadarCommandSet / India_HeavyAirBaseCommandSet
          no longer produce CombatDrone / LoiteringDrone
          India_HeavyUAV / CombatDrone / LoiteringDrone Buildable = No

This script does not rebuild _SPEC_DATA_ONE.big. It copies the already
validated DATA + CommandSet.ini + CommandButton.ini + PlayerTemplate.ini,
writes a combined installer that never copies ART or 0_ overlays, and
zips SPECTER_ISRAEL_INDIA_FIXES_INSTALL.zip.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "Release/INDIA_NO_DRONES"
SRC_BIG = SRC_DIR / "_SPEC_DATA_ONE.big"
SRC_SHA = "52b1186bc552b02237751f3faabd2b3c24c67f2a3ffe69d312db8dfd9a5bc58e"
OUT_DIR = ROOT / "Release/ISRAEL_INDIA_FIXES"
ZIP_NAME = "SPECTER_ISRAEL_INDIA_FIXES_INSTALL.zip"
K_CS = r"Data\INI\CommandSet.ini"


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


def slot_of(body: str, slot: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(slot)}\s*=\s*(\S+)", body, re.M)
    return None if m is None else m.group(1)


def active_has(body: str, needle: str) -> bool:
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith(";") or s.startswith("CommandSet") or s == "End":
            continue
        if needle in s:
            return True
    return False


def validate_source(src_dir: Path) -> dict[str, bytes]:
    require(sha256(SRC_BIG.read_bytes()) == SRC_SHA, "source DATA sha mismatch")
    entries = read_big(SRC_BIG)
    cs = entries[K_CS].decode("latin1")
    loose = (src_dir / "CommandSet.ini").read_bytes()
    require(loose == entries[K_CS], "loose CommandSet.ini != packed")

    airf = block(cs, "CommandSet", "AirF_AmericaDozerCommandSet")
    require(slot_of(airf, "2") == "Command_ConstructIsrael_GlobalStore", "Israel slot 2")
    require("SPECTER_PATCH ISRAEL_GS" in airf, "Israel marker")
    require(
        not active_has(airf, "AirF_Command_ConstructAmericaStrategyCenter"),
        "Strategy Center still on Israel dozer",
    )
    extra = (
        r"Data\INI\CommandSet_IsraelMissileFactory.ini",
        r"Data\INI\CommandSet_IsraelMissiles.ini",
        r"Data\INI\CommandSet_ZZZZ_ZzIsraelMissileFactory.ini",
    )
    for key in extra:
        body = block(entries[key].decode("latin1"), "CommandSet", "AirF_AmericaDozerCommandSet")
        require(
            slot_of(body, "2") == "Command_ConstructIsrael_GlobalStore",
            f"{key} Israel slot 2",
        )

    radar = block(cs, "CommandSet", "India_RadarCommandSet")
    hab = block(cs, "CommandSet", "India_HeavyAirBaseCommandSet")
    require("SPECTER_PATCH INDIA_NO_DRONES" in radar, "India radar marker")
    require("SPECTER_PATCH INDIA_NO_DRONES" in hab, "India HAB marker")
    require(not active_has(radar, "Command_ConstructIndia_CombatDrone"), "India radar CombatDrone")
    require(not active_has(radar, "Command_ConstructIndia_LoiteringDrone"), "India radar Loitering")
    require(active_has(radar, "Command_ConstructSpecterRadarShahedLauncher"), "Shahed stripped")
    require(active_has(radar, "Command_ConstructSpecterRadarHeron"), "Heron stripped")
    require(not active_has(hab, "Command_ConstructIndia_CombatDrone"), "HAB CombatDrone")
    require(active_has(hab, "Command_ConstructIndia_Mi-8T"), "HAB Mi-8")
    spy = block(
        entries[r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini"].decode("latin1"),
        "CommandSet",
        "India_RadarCommandSet",
    )
    require(not active_has(spy, "Command_ConstructIndia_CombatDrone"), "spy overlay CombatDrone")
    for key, obj in (
        (
            r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_CombatDrone.ini",
            "India_CombatDrone",
        ),
        (
            r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_LoiteringDrone.ini",
            "India_LoiteringDrone",
        ),
        (
            r"Data\INI\Object\Specter\Indian Armed Forces\Drones\India_HeavyUAV.ini",
            "India_HeavyUAV",
        ),
    ):
        body = block(entries[key].decode("latin1"), "Object", obj)
        require("Buildable              = No" in body, f"{obj} still buildable")

    require(
        slot_of(block(cs, "CommandSet", "AmericaDozerCommandSet"), "15")
        == "Command_ConstructAmericaStrategyCenter",
        "USA Strategy Center edited",
    )
    return entries


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def write_installer(out_dir: Path, hashes: dict[str, str]) -> None:
    bat = f"""@echo off
setlocal EnableExtensions
title SPECTER — Israel Global Store + India drone removal

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

findstr /C:"SPECTER_PATCH ISRAEL_GS" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is missing the Israel Global Store patch.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH INDIA_NO_DRONES" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is missing the India drone-removal patch.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH AA_COMBO_HIDE" "%~dp0PlayerTemplate.ini" >nul
if errorlevel 1 (
  echo ERROR: PlayerTemplate.ini is not the combo-hide lineage this pack needs.
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
  echo Unzip SPECTER_ISRAEL_INDIA_FIXES_INSTALL.zip into the Zero Hour
  echo / SPECTER folder that has generals.exe, then run this script again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\\" set "GAME_ROOT=%GAME_ROOT%\\"

echo.
echo This installer copies ONLY:
echo   _SPEC_DATA_ONE.big
echo   Data\\INI\\CommandSet.ini
echo   Data\\INI\\CommandButton.ini
echo   Data\\INI\\PlayerTemplate.ini
echo It does NOT copy or replace _SPEC_ART_ONE.big, _SPEC_ART_TWO.big,
echo or any 0_*.big overlay.
echo.

if exist "%~dp0_SPEC_ART_ONE.big" (
  echo ERROR: ART file found next to this script. This pack must not ship ART.
  pause
  exit /b 1
)
if exist "%~dp00_SPECTER_GlobalStoreCameos.big" (
  echo NOTE: A 0_ overlay is next to this script and will NOT be copied.
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

findstr /C:"SPECTER_PATCH ISRAEL_GS" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Data\\INI\\CommandSet.ini was not replaced (Israel marker missing).
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH INDIA_NO_DRONES" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Data\\INI\\CommandSet.ini was not replaced (India marker missing).
  pause
  exit /b 1
)

echo Installed both fixes:
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
echo Zero Hour was not run on this pack. Static INI/BIG checks only.
echo Keep original ART and 0_SPECTER_GlobalStoreCameos.big.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed.
pause
exit /b 1
"""
    write_text(out_dir / "Install_IsraelIndiaFixes.bat", bat)


def write_readme(out_dir: Path, hashes: dict[str, str]) -> None:
    text = f"""SPECTER — Israel Global Store + India drone removal
===================================================

One installer. Two static INI/BIG patches. Zero Hour was not run;
neither fix is in-game confirmed.

Israel (PR #728)
----------------
Starting dozer CommandSet AirF_AmericaDozerCommandSet slot 2 =
Command_ConstructIsrael_GlobalStore (not Strategy Center).
Object Israel_GlobalStore, ButtonImage Button_GlobalMarket.

India (PR #729)
---------------
India_CombatDrone, India_LoiteringDrone, India_HeavyUAV are not
producible. Shared radar UAVs (Heron / MQ-4 / Orlan-10 / Shahed),
infantry, and other countries' drones are unchanged.

Install
-------
1. Close Zero Hour.
2. Unzip {ZIP_NAME} into the folder that has generals.exe
   (or into a folder next to it).
3. Run Install_IsraelIndiaFixes.bat once.
4. Do not replace _SPEC_ART_ONE.big / _SPEC_ART_TWO.big.
5. Keep 0_SPECTER_GlobalStoreCameos.big and other 0_ overlays.

The BAT copies only DATA + three INI files. It never copies ART or 0_.

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
    text = f"""# Unified SPECTER pack: Israel Global Store + India UAV removal

**Zero Hour was not run.** Neither PR #728 nor PR #729 has been
confirmed inside the game. This pack only concatenates the already
statically-checked DATA lineage:

`aa-combo-hide` → `israel-gs-strategy` → `india-no-drones`

## Israel

`AirF_AmericaDozerCommandSet` slot 2 = `Command_ConstructIsrael_GlobalStore`.
Extra `CommandSet_*` copies of the same AirF set match. USA Strategy Center
on `AmericaDozerCommandSet` slot 15 is unchanged.

## India

`India_RadarCommandSet` and `India_HeavyAirBaseCommandSet` no longer have
active CombatDrone / LoiteringDrone slots. The three UAV objects have
`Buildable = No`. Heron / MQ-4 / Orlan-10 / Shahed stay on India radar.

## Installer

`Install_IsraelIndiaFixes.bat` copies only:

- `_SPEC_DATA_ONE.big`
- `Data\\INI\\CommandSet.ini`
- `Data\\INI\\CommandButton.ini`
- `Data\\INI\\PlayerTemplate.ini`

It does not copy `_SPEC_ART_ONE.big`, `_SPEC_ART_TWO.big`, or `0_*.big`.

## SHA-256

| File | SHA-256 |
| --- | --- |
| `_SPEC_DATA_ONE.big` | `{hashes['_SPEC_DATA_ONE.big']}` |
| `CommandSet.ini` | `{hashes['CommandSet.ini']}` |
| `CommandButton.ini` | `{hashes['CommandButton.ini']}` |
| `PlayerTemplate.ini` | `{hashes['PlayerTemplate.ini']}` |
| `{ZIP_NAME}` | `{hashes.get(ZIP_NAME, '')}` |
"""
    write_text(out_dir / "ISRAEL_INDIA_FIXES_REPORT.md", text)


def main() -> None:
    entries = validate_source(SRC_DIR)
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
        "Install_IsraelIndiaFixes.bat",
        "README_INSTALL.txt",
        "ISRAEL_INDIA_FIXES_REPORT.md",
        "SHA256SUMS.txt",
    )
    artish = [p.name for p in OUT_DIR.iterdir() if p.name.startswith("0_") or "ART" in p.name.upper()]
    require(not artish, f"ART/0_ files leaked into pack dir: {artish}")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in zip_names:
            require("ART" not in name.upper() and not name.startswith("0_"), f"zip would include {name}")
            zf.write(OUT_DIR / name, arcname=name)
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
