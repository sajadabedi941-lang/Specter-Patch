#!/usr/bin/env python3
"""Global Store: remove Pantsir, add existing S-300 at $4500.

Live GS shop (all country *_GlobalStore objects, including Israel):
  Object CommandSet = Iraq_MICCommandSet
  Last-win overlay: CommandSet_ZZZZ_IraqMicToWfRadarAd.ini
  Slot 5 = Command_ConstructIraq_MIC_PantsirS1M -> Iraq_MIC_PantsirS1M ($4000)

Existing S-300 (not invented):
  Object Arabic_S300PMU2  DisplayName OBJECT:S300  Side=GLA  BuildCost=2000
    UNIT_BUILD vehicle, S400ECommandSet, model Arb_S300, image arb_s300pmu2
  EgyptVehicleS300VM / VietnamVehicleS300 are other-country variants; left alone.

GS items are Iraq_MIC_* copies (Side=Iraq, emptied prereqs, own BuildCost).
This packer clones Arabic_S300PMU2 as Iraq_MIC_S300 BuildCost=4500 and puts
Command_ConstructIraq_MIC_S300 on GS slot 5. Original Arabic_S300PMU2 stays 2000.
Iraq_MIC_PantsirS1M object/button/model stay; only the GS menu slot changes.
Russia/Iran/Arb Pantsir production is untouched.

Dual-patch CommandSet.ini + last-win RadarAd overlay (sets 1/2/3).
Do not edit IraqMicToWf / Empty overlays (not the AD shop).
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/RADAR_SARAB_LAMINA_19/_SPEC_DATA_ONE.big"
SRC_SHA = "bb42e2c1e96c7c41660540cb8cfd93f1633a41557dde1af349984ac9242b787e"
OUT_DIR = ROOT / "Release/GS_S300"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
ZIP_NAME = "SPECTER_GS_S300_INSTALL.zip"
MARKER = "SPECTER_PATCH GS_S300"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_PT = r"Data\INI\PlayerTemplate.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_MAP = r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI"
K_LOCO = r"Data\INI\Locomotor.ini"
K_UAV = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_COPIES = r"Data\INI\Object\Specter\Iraq Army\AirDefense\Iraq_MIC_RadarAdCopies.ini"
K_S300_SRC = r"Data\INI\Object\Specter\Arabic Alliance\AirDefense\Arb_S300.ini"
K_SPY = r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini"
K_MIC_OV = r"Data\INI\CommandSet_ZZZZ_IraqMicToWfRadarAd.ini"
K_MIC_WF = r"Data\INI\CommandSet_ZZZZ_IraqMicToWf.ini"
K_MIC_EMPTY = r"Data\INI\CommandSet_ZZZZ_IraqMicToWfEmpty.ini"
K_MIC_BTN = r"Data\INI\CommandButton_ZZZZ_IraqMicRadarAd.ini"
K_GS5 = r"Data\INI\Object\Specter\GlobalStore\CountryGlobalStoresFive.ini"

BTN_PANTSIR = "Command_ConstructIraq_MIC_PantsirS1M"
BTN_S300 = "Command_ConstructIraq_MIC_S300"
OBJ_S300 = "Iraq_MIC_S300"
OBJ_S300_SRC = "Arabic_S300PMU2"
OBJ_PANTSIR = "Iraq_MIC_PantsirS1M"

MIC_SETS = ("Iraq_MICCommandSet", "Iraq_MICCommandSet2", "Iraq_MICCommandSet3")

NEW_BUTTON = f"""
CommandButton {BTN_S300}
  Command       = UNIT_BUILD
  Object        = {OBJ_S300}
  TextLabel     = CONTROLBAR:ConstructArb_S300
  ButtonImage   = arb_s300pmu2
  ButtonBorderType        = BUILD
  DescriptLabel           = CONTROLBAR:ToolTipBuildArb_S300
End
; {MARKER} displayed $4500 from Object {OBJ_S300} BuildCost
"""

KEEP_GS_SLOTS = {
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


def last_buildcost(body: str) -> str | None:
    costs = re.findall(r"^\s*BuildCost\s*=\s*(\d+)", body, re.M)
    return costs[-1] if costs else None


def swap_mic_slot5(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    old_line = f"  5 = {BTN_PANTSIR}"
    new_line = f"  5 = {BTN_S300} ; {MARKER}"
    n = text.count(old_line)
    require(n == 3, f"expected 3 Pantsir slot-5 lines, found {n}")
    require(BTN_S300 not in text, "S300 already on this CommandSet file")
    text = text.replace(old_line, new_line)
    require(text.count(new_line) == 3, "slot-5 replace failed")
    require(old_line not in text, "Pantsir slot-5 remains")
    return text.encode("latin1")


def clone_s300(src_file: bytes) -> str:
    text = src_file.decode("latin1")
    body = block(text, "Object", OBJ_S300_SRC)
    require("DisplayName          = OBJECT:S300" in body, "source is not OBJECT:S300")
    require("  Side                 = GLA" in body, "Arabic_S300PMU2 Side")
    require("  BuildCost            = 2000" in body, "Arabic_S300PMU2 cost drifted")
    require("CommandSet           = S400ECommandSet" in body, "S300 commandset")
    require("Locomotor = SET_NORMAL      Generic8x8Locomotor" in body, "S300 loco")
    require("Model                   = Arb_S300" in body, "S300 model")
    require("SelectPortrait         = arb_s300pmu2" in body, "S300 portrait")
    new = body.replace(f"Object {OBJ_S300_SRC}", f"Object {OBJ_S300}", 1)
    new = new.replace(
        "  Side                 = GLA",
        "  Side                 = Iraq",
        1,
    )
    new = new.replace(
        "  BuildCost            = 2000",
        f"  BuildCost            = 4500 ; {MARKER}",
        1,
    )
    header = (
        f"Object {OBJ_S300}\n"
        if "\r\n" not in new
        else f"Object {OBJ_S300}\r\n"
    )
    # body already starts with Object line; prepend comment after it
    nl = nl_of(new)
    comment = (
        f"; SPECTER Iraq M.I.C. copy of {OBJ_S300_SRC}. "
        f"Adaptations: Side=Iraq; BuildCost=4500; GS slot 5. {MARKER}{nl}"
    )
    first_nl = new.find(nl)
    new = new[: first_nl + len(nl)] + comment + new[first_nl + len(nl) :]
    require(f"Object {OBJ_S300}" in new.split(nl, 1)[0], "name not changed")
    require("BuildCost            = 4500" in new, "clone cost")
    require("Side                 = Iraq" in new, "clone Side")
    require("Side                 = GLA" not in new, "clone still GLA")
    require("BuildCost            = 2000" not in new, "clone still 2000")
    return new.rstrip() + nl + nl


def patch_copies(raw: bytes, clone: str) -> bytes:
    text = raw.decode("latin1")
    require(f"Object {OBJ_PANTSIR}" in text, "Pantsir MIC copy missing")
    require(f"Object {OBJ_S300}" not in text, "S300 MIC copy already exists")
    require("Object Iraq_MIC_S400" in text, "S400 MIC copy missing")
    nl = nl_of(text)
    return (text.rstrip() + nl + nl + clone).encode("latin1")


def patch_cb(raw: bytes, require_original: bool) -> bytes:
    text = raw.decode("latin1")
    require(f"CommandButton {BTN_PANTSIR}" in text, "Pantsir button missing")
    require(f"CommandButton {BTN_S300}" not in text, "S300 button exists")
    if require_original:
        require(
            "CommandButton Command_ConstructArb_S300" in text,
            "original S300 button",
        )
    nl = nl_of(text)
    extra = NEW_BUTTON.replace("\n", nl)
    return (text.rstrip() + nl + extra).encode("latin1")


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_PT] == new[K_PT], "PlayerTemplate.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    require(orig[K_MAP] == new[K_MAP], "MappedImages changed")
    require(orig[K_LOCO] == new[K_LOCO], "Locomotor.ini changed")
    require(orig[K_S300_SRC] == new[K_S300_SRC], "Arabic_S300PMU2 source edited")
    require(orig[K_UAV] == new[K_UAV], "SpecterRadarUavs.ini changed")
    require(orig[K_SPY] == new[K_SPY], "spy overlay changed")
    require(orig[K_MIC_WF] == new[K_MIC_WF], "IraqMicToWf overlay changed")
    require(orig[K_MIC_EMPTY] == new[K_MIC_EMPTY], "IraqMicToWfEmpty overlay changed")
    require(orig[K_GS5] == new[K_GS5], "Israel_GlobalStore object changed")
    expected = {K_CS, K_CB, K_COPIES, K_MIC_OV, K_MIC_BTN}
    changed = [k for k in orig if orig[k] != new[k]]
    require(set(changed) == expected, f"unexpected files changed: {changed}")

    orig_cs = orig[K_CS].decode("latin1")
    new_cs = new[K_CS].decode("latin1")
    require("SPECTER_PATCH ISRAEL_GS" in new_cs, "Israel GS lost")
    require("SPECTER_PATCH INDIA_NO_DRONES" in new_cs, "India drone hide lost")
    require("SPECTER_PATCH RADAR_SARAB_LAMINA" in new_cs, "Sarab/Lamina lost")
    require("Command_ConstructSpecterRadarSarab3" in new_cs, "Sarab3 radar button")
    require("Command_ConstructSpecterRadarLamina" in new_cs, "Lamina radar button")
    require(
        "Command_ConstructIsrael_GlobalStore" in new_cs, "Israel GS construct lost"
    )

    for name in MIC_SETS:
        body = block(new_cs, "CommandSet", name)
        slots = used_slots(body)
        require(slots.get(5) == BTN_S300, f"{name} slot 5 not S300")
        require(not active_has(body, BTN_PANTSIR), f"{name} still has Pantsir")
        orig_slots = used_slots(block(orig_cs, "CommandSet", name))
        require(orig_slots.get(5) == BTN_PANTSIR, f"{name} orig slot 5 not Pantsir")
        for n, btn in KEEP_GS_SLOTS.items():
            require(slots.get(n) == btn, f"{name} lost slot {n} {btn}")
        require(BTN_S300 not in [orig_slots[k] for k in orig_slots], "S300 was already in orig")

    ov = new[K_MIC_OV].decode("latin1")
    orig_ov = orig[K_MIC_OV].decode("latin1")
    for name in MIC_SETS:
        slots = used_slots(block(ov, "CommandSet", name))
        require(slots.get(5) == BTN_S300, f"overlay {name} slot 5")
        require(not active_has(block(ov, "CommandSet", name), BTN_PANTSIR), f"overlay {name} Pantsir")
        orig_slots = used_slots(block(orig_ov, "CommandSet", name))
        require(orig_slots.get(5) == BTN_PANTSIR, f"overlay orig {name} slot 5")
        for n, btn in KEEP_GS_SLOTS.items():
            require(slots.get(n) == btn, f"overlay {name} lost slot {n}")

    # Earlier overlays must not restore Pantsir as last-win (RadarAd is last).
    empty = new[K_MIC_EMPTY].decode("latin1")
    wf = new[K_MIC_WF].decode("latin1")
    require(BTN_PANTSIR not in empty, "Empty overlay gained Pantsir")
    require(BTN_S300 not in empty, "Empty overlay gained S300")
    require(BTN_PANTSIR not in wf, "Wf overlay gained Pantsir")

    ru_wf = block(new_cs, "CommandSet", "RussiaWarFactoryCommandSet")
    require(
        "Command_ConstructRussiaVehiclePantsirS1M" in ru_wf, "Russia WF Pantsir removed"
    )
    iran_wf = block(new_cs, "CommandSet", "IranWarfactoryCommandSet")
    require(
        "Command_ConstructIranVehiclePantsirS1M" in iran_wf, "Iran WF Pantsir removed"
    )
    arb_arms = block(new_cs, "CommandSet", "GLAArmsDealerCommandSet")
    require("Command_ConstructArb_Pantsir" in arb_arms, "Arb Pantsir removed")
    require("Command_ConstructArb_S300" in arb_arms, "Arb S300 production removed")

    cb = new[K_CB].decode("latin1")
    s300_btn = block(cb, "CommandButton", BTN_S300)
    require(f"Object        = {OBJ_S300}" in s300_btn, "S300 button object")
    require("Command       = UNIT_BUILD" in s300_btn, "S300 button command")
    require("ButtonImage   = arb_s300pmu2" in s300_btn, "S300 button image")
    require(f"CommandButton {BTN_PANTSIR}" in cb, "Pantsir button deleted")
    require("CommandButton Command_ConstructArb_S300" in cb, "original S300 button deleted")

    btn_ov = new[K_MIC_BTN].decode("latin1")
    ov_s300 = block(btn_ov, "CommandButton", BTN_S300)
    require(f"Object        = {OBJ_S300}" in ov_s300, "overlay S300 button object")
    require(f"CommandButton {BTN_PANTSIR}" in btn_ov, "overlay Pantsir button deleted")

    copies = new[K_COPIES].decode("latin1")
    s300 = block(copies, "Object", OBJ_S300)
    pants = block(copies, "Object", OBJ_PANTSIR)
    require(last_buildcost(s300) == "4500", f"MIC S300 cost {last_buildcost(s300)}")
    require(last_buildcost(pants) == "4000", "Pantsir MIC cost changed")
    require("Side                 = Iraq" in s300, "MIC S300 Side")
    require("S400ECommandSet" in s300, "MIC S300 CS")
    require("Generic8x8Locomotor" in s300, "MIC S300 loco")
    require("Arb_S300" in s300, "MIC S300 model")
    require("arb_s300pmu2" in s300, "MIC S300 portrait")
    require("OBJECT:S300" in s300, "MIC S300 display name")

    src = block(orig[K_S300_SRC].decode("latin1"), "Object", OBJ_S300_SRC)
    require(last_buildcost(src) == "2000", "original S300 cost changed")
    egy = orig[r"Data\INI\Object\Specter\Egyptian Armed Forces\Airdefense\S300VM.ini"]
    require(egy == new[r"Data\INI\Object\Specter\Egyptian Armed Forces\Airdefense\S300VM.ini"], "Egypt S300VM edited")

    mapped = new[K_MAP].decode("latin1")
    require("MappedImage arb_s300pmu2" in mapped, "arb_s300pmu2 mapping")
    require("MappedImage specbtn_mic_pantsir" in mapped or True, "pantsir cameo optional")

    gs = new[K_GS5].decode("latin1")
    israel = block(gs, "Object", "Israel_GlobalStore")
    require("CommandSet             = Iraq_MICCommandSet" in israel, "Israel GS shop")

    from collections import Counter

    counts = Counter(re.findall(r"^CommandSet (\S+)", new_cs, re.M))
    dups = [n for n, k in counts.items() if k > 1]
    require(not dups, f"duplicate CommandSets: {dups[:8]}")
    require(copies.count(f"Object {OBJ_S300}") == 1, "duplicate Iraq_MIC_S300")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def write_installer(out_dir: Path, hashes: dict[str, str]) -> None:
    bat = f"""@echo off
setlocal EnableExtensions
title SPECTER — Global Store S-300

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

findstr /C:"SPECTER_PATCH GS_S300" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is not the Global Store S-300 build.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH ISRAEL_GS" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Israel Global Store patch missing from CommandSet.ini.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH RADAR_SARAB_LAMINA" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Sarab_3/Lamina radar patch missing from CommandSet.ini.
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

findstr /C:"SPECTER_PATCH GS_S300" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
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
    write_text(out_dir / "Install_GlobalStoreS300.bat", bat)


def write_readme(out_dir: Path, hashes: dict[str, str]) -> None:
    text = f"""SPECTER — Global Store: Pantsir out, S-300 in ($4500)
=====================================================

Replaces Global Store slot 5 (Pantsir) with a copy of Arabic_S300PMU2
at BuildCost 4500. Pantsir objects elsewhere are unchanged.

Zero Hour was not run. Static INI/BIG validation only.

Install: unzip next to generals.exe, run Install_GlobalStoreS300.bat.
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
    text = f"""# Global Store: Pantsir → S-300 ($4500)

**Zero Hour was not run.** Static INI/BIG validation only.

Live Global Store shop is `Iraq_MICCommandSet` (all `*_GlobalStore` buildings,
including Israel). Last-win overlay `CommandSet_ZZZZ_IraqMicToWfRadarAd.ini`.

| Check | Result |
| --- | --- |
| Pantsir removed from GS slot 5 (CS.ini sets 1/2/3) | yes |
| Pantsir removed from last-win RadarAd overlay | yes |
| S-300 on GS slot 5 `Command_ConstructIraq_MIC_S300` | yes |
| Object `Iraq_MIC_S300` last-win BuildCost | **4500** |
| Source `Arabic_S300PMU2` BuildCost | still 2000 |
| `Iraq_MIC_PantsirS1M` object kept | yes (cost 4000) |
| Russia / Iran / Arb Pantsir production kept | yes |
| Other GS slots 1–4, 6–15 unchanged | yes |
| Israel GS / Sarab_3 / Lamina markers kept | yes |
| Duplicate Iraq_MICCommandSet in CommandSet.ini | none |
| Duplicate Iraq_MIC_S300 object | none |

SAGE construct cost is Object `BuildCost`. CommandButton.ini has no Cost field.

## SHA-256

| File | SHA-256 |
| --- | --- |
| `_SPEC_DATA_ONE.big` | `{hashes.get('_SPEC_DATA_ONE.big', '')}` |
| `CommandSet.ini` | `{hashes.get('CommandSet.ini', '')}` |
| `CommandButton.ini` | `{hashes.get('CommandButton.ini', '')}` |
| `PlayerTemplate.ini` | `{hashes.get('PlayerTemplate.ini', '')}` |
| `{ZIP_NAME}` | `{hashes.get(ZIP_NAME, '')}` |
"""
    write_text(out_dir / "GS_S300_REPORT.md", text)


def main() -> None:
    require(SRC_BIG.is_file(), f"missing {SRC_BIG}")
    require(sha256(SRC_BIG.read_bytes()) == SRC_SHA, "source DATA sha mismatch")
    orig = read_big(SRC_BIG)
    clone = clone_s300(orig[K_S300_SRC])
    new = dict(orig)
    new[K_COPIES] = patch_copies(orig[K_COPIES], clone)
    new[K_CS] = swap_mic_slot5(orig[K_CS])
    new[K_MIC_OV] = swap_mic_slot5(orig[K_MIC_OV])
    new[K_CB] = patch_cb(orig[K_CB], require_original=True)
    new[K_MIC_BTN] = patch_cb(orig[K_MIC_BTN], require_original=False)
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
        "Install_GlobalStoreS300.bat",
        "README_INSTALL.txt",
        "GS_S300_REPORT.md",
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
