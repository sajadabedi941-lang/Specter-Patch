#!/usr/bin/env python3
"""Israel only: replace Strategy Center with the existing Global Store.

Live first-win (aa-combo-startingbuilding DATA, SHA 00a9bbe5...):
  PlayerTemplate FactionAmericaAirForceGeneral
    StartingUnit0 = AirF_AmericaVehicleDozer
  Object AirF_AmericaVehicleDozer  Side=Israel
    CommandSet = AirF_AmericaDozerCommandSet
  CommandSet AirF_AmericaDozerCommandSet slot 2
    = AirF_Command_ConstructAmericaStrategyCenter
    -> Object AirF_AmericaStrategyCenter (Industry Planet)
    ButtonImage already Button_GlobalMarket  (GS art, wrong building)

Working country pattern (Germany / USA / IsraelDozerCommandSet):
  dozer slot 2 = Command_Construct*_GlobalStore
  CommandButton Object = *_GlobalStore
  ButtonImage = Button_GlobalMarket
  Object CommandSet = Iraq_MICCommandSet
  no Prerequisites, BuildCost 7000

Israel already has Command_ConstructIsrael_GlobalStore and
Israel_GlobalStore (same Iraq_MIC shop). IsraelDozerCommandSet slot 2
already uses it, but that set is NOT the starting dozer.

This packer swaps only AirF_AmericaDozerCommandSet slot 2 to
Command_ConstructIsrael_GlobalStore. Extra CommandSet_* copies of the
same AirF set are updated so a last-win overlay cannot restore
Strategy Center. ControlBar still loads only CommandSet.ini.

Does not:
  create a new building or CommandButton
  edit other countries' Global Store slots
  edit CommandButton.ini / PlayerTemplate.ini / Weapon.ini
  edit Shahed, Vietnam radar, ART, or 0_ overlays
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/AA_COMBO_HIDE/_SPEC_DATA_ONE.big"
SRC_SHA = "00a9bbe5b4ff9236df67d9835e6039aebab4d72650e5ff722facb56854006a46"
OUT_DIR = ROOT / "Release/ISRAEL_GS"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
ZIP_NAME = "ISRAEL_GS_INSTALL.zip"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_PT = r"Data\INI\PlayerTemplate.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_UAV = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_VN = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_RadarStation.ini"
)
K_DOZER = r"Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Dozer.ini"
K_GS5 = r"Data\INI\Object\Specter\GlobalStore\CountryGlobalStoresFive.ini"
K_MAP = r"Data\INI\MappedImages\HandCreated\IraqConstructFix_Images.INI"

EXTRA_CS = (
    r"Data\INI\CommandSet_IsraelMissileFactory.ini",
    r"Data\INI\CommandSet_IsraelMissiles.ini",
    r"Data\INI\CommandSet_ZZZZ_ZzIsraelMissileFactory.ini",
)

OLD_SLOT = "  2  = AirF_Command_ConstructAmericaStrategyCenter"
NEW_SLOT = "  2  = Command_ConstructIsrael_GlobalStore ; SPECTER_PATCH ISRAEL_GS"

UNTOUCHED_DOZERS = (
    "AmericaDozerCommandSet",
    "GermanyDozerCommandSet",
    "IsraelDozerCommandSet",
    "IranDozerCommandSet",
    "PLADozerCommandSet",
    "RussiaDozerCommandSet",
    "FranceDozerCommandSet",
    "BritainDozerCommandSet",
    "ItalyDozerCommandSet",
    "SwedenDozerCommandSet",
    "UkraineDozerCommandSet",
    "TurkeyDozerCommandSet",
    "NatoDozerCommandSet",
    "SupW_AmericaDozerCommandSet",
    "Lazr_AmericaDozerCommandSet",
    "Boss_AmericaDozerCommandSet",
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
    m = re.search(rf"^{kind} {re.escape(name)}\s*\r?\n", text, re.M)
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


def nl_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def slot_of(cs_body: str, slot: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(slot)}\s*=\s*(\S+)", cs_body, re.M)
    return None if m is None else m.group(1)


def field_of(body: str, field: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(field)}\s*=\s*(\S+)", body, re.M)
    return None if m is None else m.group(1)


def patch_cs_text(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    airf = block(text, "CommandSet", "AirF_AmericaDozerCommandSet")
    nl = nl_of(airf)
    old_line = OLD_SLOT + nl
    new_line = NEW_SLOT + nl
    require(old_line in airf, "AirF dozer slot 2 is not Strategy Center")
    require(airf.count(OLD_SLOT) == 1, "duplicate Strategy Center in AirF dozer")
    require("Command_ConstructIsrael_GlobalStore" not in airf, "AirF dozer already has GS")
    new_airf = airf.replace(old_line, new_line, 1)
    require(OLD_SLOT not in new_airf, "Strategy Center still on AirF dozer")
    require("SPECTER_PATCH ISRAEL_GS" in new_airf, "installer marker missing")
    require(slot_of(new_airf, "2") == "Command_ConstructIsrael_GlobalStore", "slot 2 not GS")
    require(text.count(airf) == 1, "duplicate AirF_AmericaDozerCommandSet")
    return text.replace(airf, new_airf, 1).encode("latin1")


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_CB] == new[K_CB], "CommandButton.ini changed")
    require(orig[K_PT] == new[K_PT], "PlayerTemplate.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    require(orig[K_UAV] == new[K_UAV], "Shahed UAV file changed")
    require(orig[K_VN] == new[K_VN], "Vietnam radar changed")
    require(orig[K_DOZER] == new[K_DOZER], "Israel dozer object changed")
    require(orig[K_GS5] == new[K_GS5], "Israel_GlobalStore object changed")
    require(orig[K_MAP] == new[K_MAP], "Button_GlobalMarket mapping changed")

    changed = [k for k in orig if orig[k] != new[k]]
    expected = [K_CS, *EXTRA_CS]
    require(changed == expected, f"unexpected files changed: {changed}")
    require(set(orig) == set(new), "BIG entry set changed")

    orig_cs = orig[K_CS].decode("latin1")
    new_cs = new[K_CS].decode("latin1")
    airf = block(new_cs, "CommandSet", "AirF_AmericaDozerCommandSet")
    orig_airf = block(orig_cs, "CommandSet", "AirF_AmericaDozerCommandSet")
    require(slot_of(orig_airf, "2") == "AirF_Command_ConstructAmericaStrategyCenter", "source slot")
    require(slot_of(airf, "2") == "Command_ConstructIsrael_GlobalStore", "live slot 2")
    require("SPECTER_PATCH ISRAEL_GS" in airf, "marker")
    require("AirF_Command_ConstructAmericaStrategyCenter" not in airf, "SC leftover in AirF dozer")
    require("Command_ConstructIsrael_GlobalStore" in airf, "GS button missing from AirF dozer")

    # Every other slot on the Israel starting dozer stays put.
    for slot in ("1", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"):
        require(
            slot_of(orig_airf, slot) == slot_of(airf, slot),
            f"AirF dozer slot {slot} changed",
        )

    for name in UNTOUCHED_DOZERS:
        require(
            block(orig_cs, "CommandSet", name) == block(new_cs, "CommandSet", name),
            f"{name} edited",
        )

    # Working-country pattern still present; IsraelDozer already had GS.
    require(
        slot_of(block(new_cs, "CommandSet", "GermanyDozerCommandSet"), "2")
        == "Command_ConstructGermany_GlobalStore",
        "Germany GS slot lost",
    )
    require(
        slot_of(block(new_cs, "CommandSet", "AmericaDozerCommandSet"), "2")
        == "Command_ConstructAmerica_GlobalStore",
        "USA GS slot lost",
    )
    require(
        slot_of(block(new_cs, "CommandSet", "IsraelDozerCommandSet"), "2")
        == "Command_ConstructIsrael_GlobalStore",
        "IsraelDozer GS slot lost",
    )
    require(
        slot_of(block(new_cs, "CommandSet", "AmericaDozerCommandSet"), "15")
        == "Command_ConstructAmericaStrategyCenter",
        "USA Strategy Center slot was edited",
    )

    # Button / object / shop chain (unchanged bytes, still required to exist).
    cb = new[K_CB].decode("latin1")
    gs_btn = block(cb, "CommandButton", "Command_ConstructIsrael_GlobalStore")
    require("Command       = DOZER_CONSTRUCT" in gs_btn, "GS button command")
    require("Object        = Israel_GlobalStore" in gs_btn, "GS button object")
    require("ButtonImage   = Button_GlobalMarket" in gs_btn, "GS button image")
    de_btn = block(cb, "CommandButton", "Command_ConstructGermany_GlobalStore")
    require("ButtonImage   = Button_GlobalMarket" in de_btn, "Germany GS image")
    require("Object        = Germany_GlobalStore" in de_btn, "Germany GS object")

    # The old Strategy Center button is unused by Israel's dozer but must
    # remain for any leftover object; we did not delete it.
    sc_btn = block(cb, "CommandButton", "AirF_Command_ConstructAmericaStrategyCenter")
    require("Object        = AirF_AmericaStrategyCenter" in sc_btn, "SC button object")

    gs_obj = block(new[K_GS5].decode("latin1"), "Object", "Israel_GlobalStore")
    require(field_of(gs_obj, "Side") == "Israel", "Israel_GlobalStore Side")
    require(field_of(gs_obj, "CommandSet") == "Iraq_MICCommandSet", "GS shop set")
    require(field_of(gs_obj, "BuildCost") == "7000", "GS cost")
    require(
        re.search(r"Prerequisites\s*\r?\n\s*End", gs_obj) is not None,
        "Israel_GlobalStore Prerequisites are missing or not empty",
    )

    mic = block(new_cs, "CommandSet", "Iraq_MICCommandSet")
    require("Command_ConstructIraq_MIC_Arrow" in mic, "MIC shop")
    require("Command_Sell" in mic, "MIC sell")

    dozer = block(new[K_DOZER].decode("latin1"), "Object", "AirF_AmericaVehicleDozer")
    require(field_of(dozer, "Side") == "Israel", "starting dozer Side")
    require(field_of(dozer, "CommandSet") == "AirF_AmericaDozerCommandSet", "starting dozer CS")

    mapped = new[K_MAP].decode("latin1")
    img = block(mapped, "MappedImage", "Button_GlobalMarket")
    require("Texture = Button_GlobalMarket.tga" in img, "GS TGA mapping")

    pt = new[K_PT].decode("latin1")
    airf_pt = block(pt, "PlayerTemplate", "FactionAmericaAirForceGeneral")
    require("StartingUnit0     = AirF_AmericaVehicleDozer" in airf_pt, "Israel starting dozer")
    gla = block(pt, "PlayerTemplate", "FactionGLA")
    require("SPECTER_PATCH AA_COMBO_HIDE" in gla, "AA combo hide lost")
    require(re.search(r"^\s*StartingBuilding\s*=", gla, re.M) is None, "GLA StartingBuilding restored")

    # Shahed / Vietnam from prior packs.
    require(
        "12 = Command_ConstructSpecterRadarShahedLauncher"
        in block(new_cs, "CommandSet", "Vietnam_RadarStationCommandSet"),
        "VN Shahed",
    )
    uav = block(new[K_UAV].decode("latin1"), "Object", "SpecterRadar_ShahedLauncher")
    require("BuildCost       = 8000" in uav, "Shahed cost")
    require("IranShahed136FireCommandSet" in uav, "Shahed Fire")
    vn = new[K_VN].decode("latin1")
    require("TriggeredBy   = Upgrade_AmericaRadar" in vn, "Vietnam radar TriggeredBy")

    # Extra CS copies: same AirF slot swap, no other country edits.
    for key in EXTRA_CS:
        extra = new[key].decode("latin1")
        extra_airf = block(extra, "CommandSet", "AirF_AmericaDozerCommandSet")
        require(slot_of(extra_airf, "2") == "Command_ConstructIsrael_GlobalStore", f"{key} slot 2")
        require("AirF_Command_ConstructAmericaStrategyCenter" not in extra_airf, f"{key} SC leftover")
        orig_extra = orig[key].decode("latin1")
        orig_extra_airf = block(orig_extra, "CommandSet", "AirF_AmericaDozerCommandSet")
        for slot in ("1", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"):
            require(
                slot_of(orig_extra_airf, slot) == slot_of(extra_airf, slot),
                f"{key} slot {slot} changed",
            )

    # No leftover Strategy Center construct on any AirF_AmericaDozerCommandSet.
    for key, blob in new.items():
        if b"CommandSet AirF_AmericaDozerCommandSet" not in blob:
            continue
        body = block(blob.decode("latin1"), "CommandSet", "AirF_AmericaDozerCommandSet")
        require(
            "AirF_Command_ConstructAmericaStrategyCenter" not in body,
            f"SC still on AirF dozer in {key}",
        )
        require(
            slot_of(body, "2") == "Command_ConstructIsrael_GlobalStore",
            f"slot 2 not GS in {key}",
        )

    # Only one object uses the live AirF dozer set.
    users = []
    for key, blob in new.items():
        if not key.lower().endswith(".ini"):
            continue
        txt = blob.decode("latin1")
        for m in re.finditer(r"^Object (\S+)", txt, re.M):
            try:
                body = block(txt, "Object", m.group(1))
            except SystemExit:
                continue
            if field_of(body, "CommandSet") == "AirF_AmericaDozerCommandSet":
                users.append((m.group(1), field_of(body, "Side"), key))
    require(users == [("AirF_AmericaVehicleDozer", "Israel", K_DOZER)], f"AirF dozer users {users}")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def write_installer(out_dir: Path, hashes: dict[str, str]) -> None:
    bat = f"""@echo off
setlocal EnableExtensions
title SPECTER — Israel Global Store (replace Strategy Center)

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
  echo ERROR: CommandSet.ini in this pack is not the Israel Global Store build.
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
  echo Unzip into the Zero Hour / SPECTER folder that has generals.exe,
  echo then run this script again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\\" set "GAME_ROOT=%GAME_ROOT%\\"

echo.
echo Copying ONLY _SPEC_DATA_ONE.big is not enough.
echo SPECTER already has Data\\INI\\CommandSet.ini as a loose file.
echo FileSystem::openFile reads that loose file before any BIG, so the
echo Israel dozer menu will not change unless this script overwrites it.
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

findstr /C:"SPECTER_PATCH ISRAEL_GS" "%GAME_ROOT%Data\\INI\\CommandSet.ini" >nul
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
echo Israel starting dozer slot 2 now builds Israel_GlobalStore.
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
    write_text(out_dir / "Install_IsraelGS.bat", bat)


def write_readme(out_dir: Path, hashes: dict[str, str]) -> None:
    text = f"""SPECTER — Israel: Strategy Center -> Global Store
=================================================

What this pack changes
----------------------
Israel's starting dozer (`AirF_AmericaVehicleDozer`, Side=Israel) uses
`AirF_AmericaDozerCommandSet`. Slot 2 was
`AirF_Command_ConstructAmericaStrategyCenter` (Strategy Center /
Industry Planet) with Global Store button art.

Slot 2 is now the already-working
`Command_ConstructIsrael_GlobalStore` button:

  CommandButton -> Object Israel_GlobalStore
  ButtonImage   -> Button_GlobalMarket
  Object        -> CommandSet Iraq_MICCommandSet
  Prerequisites empty, BuildCost 7000

Same pattern as Germany / USA Global Store. No new building, no new
CommandButton, no other-country Global Store edits.

CommandButton.ini and PlayerTemplate.ini are the aa-combo-hide bytes
(Arabic Alliance stays hidden). Shahed Fire 8000 and Vietnam radar
TriggeredBy are unchanged.

Install (required)
------------------
Copying only `_SPEC_DATA_ONE.big` will NOT change the Israel menu if
`Data\\INI\\CommandSet.ini` already exists. FileSystem::openFile opens
the loose file first, then BIGs.

1. Close Zero Hour.
2. Unzip {ZIP_NAME} into the game folder
   (the folder that has generals.exe) or next to it.
3. Run Install_IsraelGS.bat.
4. Confirm the script printed SPECTER_PATCH ISRAEL_GS hashes.
5. Keep 0_SPECTER_GlobalStoreCameos.big and
   0_SPECTER_MissileJLMNCameos.big.
6. Do not replace _SPEC_ART_ONE.big / _SPEC_ART_TWO.big.

Zero Hour was not run. Static validation is not an in-game screenshot.

SHA-256
-------
  DATA  {hashes['_SPEC_DATA_ONE.big']}
  CS    {hashes['CommandSet.ini']}
  CB    {hashes['CommandButton.ini']}
  PT    {hashes['PlayerTemplate.ini']}
  ZIP   {hashes[ZIP_NAME]}
"""
    write_text(out_dir / "README_INSTALL.txt", text)


def write_report(out_dir: Path, hashes: dict[str, str]) -> None:
    text = f"""# Israel: replace Strategy Center with existing Global Store

**Zero Hour was not run.** Static INI / BIG validation is not an in-game
screenshot.

## Live Israel construction menu

| Step | Value |
| --- | --- |
| PlayerTemplate | `FactionAmericaAirForceGeneral` |
| StartingUnit0 | `AirF_AmericaVehicleDozer` |
| Object Side | Israel |
| CommandSet | `AirF_AmericaDozerCommandSet` |
| ControlBar file | `Data\\INI\\CommandSet.ini` only |

`IsraelDozerCommandSet` already had slot 2 =
`Command_ConstructIsrael_GlobalStore`, but the starting dozer does not
use that set. The button art on the Strategy Center construct command
was already `Button_GlobalMarket`, so the menu looked like Global Store
and built Industry Planet.

## Fix (Israel only)

`AirF_AmericaDozerCommandSet` slot 2:

| Before | After |
| --- | --- |
| `AirF_Command_ConstructAmericaStrategyCenter` | `Command_ConstructIsrael_GlobalStore` |

Existing chain (unchanged bytes):

- `Command_ConstructIsrael_GlobalStore` → `Israel_GlobalStore`
- `ButtonImage = Button_GlobalMarket` (same TGA as Germany)
- `Israel_GlobalStore` → `Iraq_MICCommandSet`, `Side = Israel`,
  `BuildCost = 7000`, empty `Prerequisites`
- MappedImage `Button_GlobalMarket` → `Button_GlobalMarket.tga`
  (keep `0_SPECTER_GlobalStoreCameos.big`)

Three extra `CommandSet_*` copies that redefined the same AirF dozer
set still had Strategy Center. They are updated so a last-win overlay
cannot restore it. ControlBar still loads only `CommandSet.ini`.

## Unchanged on purpose

- Other countries' Global Store construct slots (USA slot 2, Germany
  slot 2, and the rest)
- `IsraelDozerCommandSet` (already GS)
- `CommandButton.ini`, `PlayerTemplate.ini` (AA combo hide kept)
- `Weapon.ini`, Shahed Fire, Shahed cost 8000, Vietnam radar
  `TriggeredBy = Upgrade_AmericaRadar`
- ART originals and `0_` overlays
- Units, economy, radar menus, prices

USA still has Strategy Center on `AmericaDozerCommandSet` slot 15.

## SHA-256

| File | SHA-256 |
| --- | --- |
| `_SPEC_DATA_ONE.big` | `{hashes['_SPEC_DATA_ONE.big']}` |
| `CommandSet.ini` | `{hashes['CommandSet.ini']}` |
| `CommandButton.ini` | `{hashes['CommandButton.ini']}` |
| `PlayerTemplate.ini` | `{hashes['PlayerTemplate.ini']}` |
| `{ZIP_NAME}` | `{hashes[ZIP_NAME]}` |
"""
    write_text(out_dir / "ISRAEL_GS_REPORT.md", text)


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    blob = SRC_BIG.read_bytes()
    require(sha256(blob) == SRC_SHA, "source BIG sha mismatch")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    new[K_CS] = patch_cs_text(orig[K_CS])
    for key in EXTRA_CS:
        new[key] = patch_cs_text(orig[key])
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
    hashes[ZIP_NAME] = "(see SHA256SUMS.txt next to this zip)"
    write_readme(OUT_DIR, hashes)
    write_report(OUT_DIR, hashes)
    (OUT_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")

    zip_path = OUT_DIR / ZIP_NAME
    zip_names = (
        "_SPEC_DATA_ONE.big",
        "CommandSet.ini",
        "CommandButton.ini",
        "PlayerTemplate.ini",
        "Install_IsraelGS.bat",
        "README_INSTALL.txt",
        "ISRAEL_GS_REPORT.md",
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
    print("CS", hashes["CommandSet.ini"], "bytes", len(new[K_CS]))
    print("CB", hashes["CommandButton.ini"])
    print("PT", hashes["PlayerTemplate.ini"])
    print("ZIP", zip_hash)
    print("--- AirF_AmericaDozerCommandSet ---")
    print(block(new[K_CS].decode("latin1"), "CommandSet", "AirF_AmericaDozerCommandSet"))


if __name__ == "__main__":
    main()
