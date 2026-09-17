#!/usr/bin/env python3
"""Package SPECTER1_RUS_TIGR_TIER2_RELEASE.zip from the current fixed DATA.

Verifies Upgrade.ini parse (zero errors), RUS_Tier1/2, Tigr1/Tigr2, and
DATA consistency before writing the Windows release ZIP. Does not ship
debug/test reports. Marks NOT WINDOWS GAMEPLAY VALIDATED.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf
from rus_tigr2_rebuild import CS_AFTER, CS_LIVE, def_exists
from rus_tigr_tier1_parse_fix import extract_named_upgrade, unique_upgrade_count
from rus_tigr_tier2_final_fix import (
    INI_UNIQUE_LIMIT,
    P_BTN,
    P_BTR,
    P_CS,
    P_DEF_UPG,
    P_IC,
    P_TIGR,
    P_UPG,
    simulate_upgrade_parse,
    upgrade_block_errors,
)

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_RUS_TIGR_TIER2_FINAL/_SPEC_DATA_ONE.big")
EXPECTED_DATA_SHA = "37419fb5a6e82eddaca83ff1679157cd189339826f74b0477781494f292a305e"
OUT_DIR = Path("/workspace/patch/Release/SPECTER1_RUS_TIGR_TIER2_RELEASE")
ZIP_PATH = Path("/workspace/patch/Release/SPECTER1_RUS_TIGR_TIER2_RELEASE.zip")
ARTIFACTS = Path("/opt/cursor/artifacts")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(packed) -> dict:
    pups = jf.text_of(packed, P_UPG)
    pdef = jf.text_of(packed, P_DEF_UPG)
    pbtn = jf.parse_buttons(jf.text_of(packed, P_BTN))
    pcs = jf.parse_commandsets(jf.text_of(packed, P_CS))
    pic = jf.text_of(packed, P_IC)
    ptigr = jf.text_of(packed, P_TIGR)
    pbtr = jf.text_of(packed, P_BTR)

    unique, order = unique_upgrade_count(pdef, pups)
    parsed = simulate_upgrade_parse(pdef, pups)
    syntax = upgrade_block_errors(pups) + upgrade_block_errors(pdef)

    def cs_buttons(name: str) -> list[str]:
        return re.findall(r"(?im)^\s*\d+\s*=\s*(\S+)", pcs.get(name, ""))

    live = cs_buttons(CS_LIVE)
    after = cs_buttons(CS_AFTER)
    cc = cs_buttons("RussiaCommandCenterCommandSet")
    t1 = jf.extract_object_block(ptigr, "RussiaVehicleTigr1")
    t2 = jf.extract_object_block(ptigr, "RussiaVehicleTigr2")
    btr = jf.extract_object_block(pbtr, "RussiaVehicleBTR82A")
    tier1 = extract_named_upgrade(pups, "Upgrade_RUS_Tier1")
    tier2 = extract_named_upgrade(pups, "Upgrade_RUS_Tier2")
    tigr2_upg = extract_named_upgrade(pups, "Upgrade_Rus_Tigr2")

    checks = {
        "Upgrade.ini parse ZERO errors": parsed["ok"] and not syntax and unique <= INI_UNIQUE_LIMIT,
        "Upgrade_RUS_Tier1 exists": "DisplayName        = UPGRADE:Tier1" in tier1 and "sys_tier1" in tier1,
        "Upgrade_RUS_Tier2 exists": "DisplayName        = UPGRADE:Tier2" in tier2 and "sys_tier2" in tier2,
        "Upgrade_Rus_Tigr2 exists": "ButtonImage        = rus_btr82" in tigr2_upg,
        "Tigr1 object present": "Side" in t1 and "Russia" in t1,
        "Tigr2 object present": "Side" in t2 and "Russia" in t2,
        "Tigr1 UNIT_BUILD live CS": "Command_ConstructRussiaVehicleTigr1" in live,
        "Tigr2 UNIT_BUILD after CS": "Command_ConstructRussiaVehicleTigr2" in after,
        "Tigr2 not on live CS": "Command_ConstructRussiaVehicleTigr2" not in live,
        "Tigr1 on Command Center": "Command_ConstructRussiaVehicleTigr1" in cc,
        "Tigr2 research button": "PLAYER_UPGRADE" in pbtn.get("Command_Upgrade_Rus_Tigr2", ""),
        "CommandSetUpgrade TriggeredBy Upgrade_Rus_Tigr2": "TriggeredBy = Upgrade_Rus_Tigr2" in pic,
        "Tigr.ini packed": def_exists(packed, "Object", "RussiaVehicleTigr1")
        and def_exists(packed, "Object", "RussiaVehicleTigr2"),
        "BTR82A clone weapons": "30mm_2A72_dualfeed" in t1 + t2,
        "DATA SHA256 match": True,  # filled by caller
    }
    if parsed["overflow_name"]:
        checks["Upgrade.ini parse ZERO errors"] = False
    return {
        "checks": checks,
        "unique": unique,
        "order": order,
        "parsed": parsed,
        "syntax": syntax,
        "tier1_idx": order.index("Upgrade_RUS_Tier1") + 1,
        "tier2_idx": order.index("Upgrade_RUS_Tier2") + 1,
        "tigr2_idx": order.index("Upgrade_Rus_Tigr2") + 1,
        "t1_ok": bool(t1),
        "t2_ok": bool(t2),
        "btr_ok": bool(btr),
    }


def write_text(path: Path, text: str) -> None:
    path.write_text(text.replace("\n", "\r\n") if False else text, encoding="utf-8")


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing packed DATA: {SRC_DATA}")
    data_sha = sha256_file(SRC_DATA)
    if data_sha != EXPECTED_DATA_SHA:
        raise SystemExit(f"DATA SHA mismatch: {data_sha} != {EXPECTED_DATA_SHA}")

    packed = jf.read_big_list(SRC_DATA)
    result = verify(packed)
    result["checks"]["DATA SHA256 match"] = data_sha == EXPECTED_DATA_SHA
    failed = [k for k, v in result["checks"].items() if not v]
    if failed:
        raise SystemExit(f"release verification failed: {failed}")
    if result["syntax"]:
        raise SystemExit(f"Upgrade.ini syntax errors: {result['syntax']}")
    if not result["parsed"]["ok"]:
        raise SystemExit(f"Upgrade.ini parse overflow at {result['parsed']['overflow_name']}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_dst = OUT_DIR / "_SPEC_DATA_ONE.big"
    if not data_dst.is_file() or sha256_file(data_dst) != data_sha:
        data_dst.write_bytes(SRC_DATA.read_bytes())

    # Original Specter release ZIPs ship BIG + notes at zip root.
    # Never extract loose Data/Art folders.
    data_tree = OUT_DIR / "Data"
    if data_tree.exists():
        shutil.rmtree(data_tree)
    art_tree = OUT_DIR / "Art"
    if art_tree.exists():
        shutil.rmtree(art_tree)

    install = f"""SPECTER1_RUS_TIGR_TIER2_RELEASE
==============================

NOT WINDOWS GAMEPLAY VALIDATED

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG
   next to generals.exe (backup the original first).
3. Do not replace ART. ART is unchanged.
4. Launch Specter.
5. Play Russia. Build Weapon Industry Plant (Industrial Complex).
6. Build Tigr1 (slot 6). Tigr1 is always available.
7. Purchase Tigr2 research (slot 5). Wait for completion.
8. Build Tigr2 (slot 10 on the switched CommandSet).
9. Command Center slot 11 also builds Tigr1.

DATA SHA256 {data_sha}
ART_CHANGED = NO
"""

    notes = f"""SPECTER1_RUS_TIGR_TIER2_RELEASE
==============================

NOT WINDOWS GAMEPLAY VALIDATED

What this release fixes
-----------------------
Zero Hour crashed while parsing Data\\\\INI\\\\Upgrade.ini at:

  Upgrade Upgrade_RUS_Tier2

The Tier2 block itself was valid. Capture Default+Upgrade.ini already
used 128 unique upgrade names. Three hardcoded veterancy templates take
bits 0-2 of the 128-bit UpgradeMaskType, so only 125 INI names fit.
Unique 125 (Upgrade_RUS_Tier1) was the last valid bit. Unique 126
(Upgrade_RUS_Tier2) overflowed the mask.

This pack frees five unused unique upgrade templates, rebuilds the
Russian Tigr2 research upgrade from the working SU39 vehicle template,
and keeps Tigr1, Tigr2, Upgrade_RUS_Tier1, and Upgrade_RUS_Tier2.

Kept
----
  Upgrade_RUS_Tier1
  Upgrade_RUS_Tier2
  Object RussiaVehicleTigr1
  Object RussiaVehicleTigr2

Tigr path
---------
  Upgrade_Rus_Tigr2          SU39-style PLAYER_UPGRADE (rus_btr82)
  Command_Upgrade_Rus_Tigr2  plant slot 5
  RussiaVehicleTigr1         always buildable (plant slot 6, CC slot 11)
  RussiaVehicleTigr2         plant slot 10 after Upgrade_Rus_Tigr2

Parse verification (this packager)
----------------------------------
  Upgrade.ini parse errors:     ZERO
  Unique Default+Upgrade.ini:   {result['unique']}  (limit {INI_UNIQUE_LIMIT})
  Upgrade_RUS_Tier1 index:      {result['tier1_idx']}
  Upgrade_RUS_Tier2 index:      {result['tier2_idx']}
  Upgrade_Rus_Tigr2 index:      {result['tigr2_idx']}
  Simulated next mask bit:      {result['parsed']['next_bit']}  (must be <= 128)
  Tigr1 / Tigr2 objects:        PRESENT
  DATA SHA256:                  {data_sha}
  DATA consistency:             PASS

Patched inside _SPEC_DATA_ONE.big (not shipped as loose files):
  Upgrade.ini, CommandButton.ini, CommandSet.ini,
  WeaponIndustryPlant.ini, Tigr.ini

Unchanged: ART, War Factory CommandSet, identity / PlayerTemplate,
BTR82A.ini, Default\\Upgrade.ini.

Copy _SPEC_DATA_ONE.big next to generals.exe. Do not replace ART.
"""

    bat = r"""@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SPECTER1 RUS TIGR TIER2 RELEASE installer
cd /d "%~dp0"

echo.
echo ============================================================
echo  SPECTER1_RUS_TIGR_TIER2_RELEASE
echo ============================================================
echo  Copies _SPEC_DATA_ONE.big into the Zero Hour GameRoot.
echo  Does NOT replace ART.
echo  NOT WINDOWS GAMEPLAY VALIDATED
echo.

set "SRC=%~dp0"
set "GAMEROOT=%~1"
if not defined GAMEROOT (
  echo Enter Specter / Zero Hour GameRoot (folder with generals.exe).
  set /p "GAMEROOT=GameRoot: "
)
if not defined GAMEROOT (
  echo ERROR: GameRoot required.
  echo Usage: Install_SpecterPatch.bat "D:\Games\Generals Zero Hour"
  pause
  exit /b 1
)
set "GAMEROOT=%GAMEROOT:"=%"

if not exist "!GAMEROOT!\generals.exe" if not exist "!GAMEROOT!\_SPEC_DATA_ONE.big" (
  echo ERROR: "!GAMEROOT!" is not a Specter / Zero Hour GameRoot.
  pause
  exit /b 1
)
if not exist "!SRC!_SPEC_DATA_ONE.big" (
  echo ERROR: _SPEC_DATA_ONE.big missing next to installer.
  pause
  exit /b 1
)

set "BAK=!GAMEROOT!\SpecterPatch_Backup_RUS_TIGR_TIER2"
mkdir "!BAK!" 2>nul
if exist "!GAMEROOT!\_SPEC_DATA_ONE.big" copy /Y "!GAMEROOT!\_SPEC_DATA_ONE.big" "!BAK!\" >nul

echo Copying _SPEC_DATA_ONE.big ...
copy /Y "!SRC!_SPEC_DATA_ONE.big" "!GAMEROOT!\_SPEC_DATA_ONE.big" >nul || goto :fail

echo.
echo INSTALLATION COMPLETED SUCCESSFULLY
echo Backup saved to: !BAK!
echo ART was not changed.
echo NOT WINDOWS GAMEPLAY VALIDATED
pause
exit /b 0
:fail
echo ERROR: copy failed. Check permissions / disk space.
pause
exit /b 1
"""

    write_text(OUT_DIR / "INSTALL.txt", install)
    write_text(OUT_DIR / "RELEASE_NOTES.txt", notes)
    write_text(OUT_DIR / "Install_SpecterPatch.bat", bat.replace("\n", "\r\n") if "\n" in bat else bat)

    top_files = [
        "_SPEC_DATA_ONE.big",
        "INSTALL.txt",
        "RELEASE_NOTES.txt",
        "Install_SpecterPatch.bat",
    ]
    sha_lines = [
        "SPECTER1_RUS_TIGR_TIER2_RELEASE",
        "NOT WINDOWS GAMEPLAY VALIDATED",
        "",
    ]
    for name in top_files:
        sha_lines.append(f"{sha256_file(OUT_DIR / name)}  {name}")
    write_text(OUT_DIR / "SHA256.txt", "\n".join(sha_lines) + "\n")

    zip_names = top_files + ["SHA256.txt"]
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for name in zip_names:
            zf.write(OUT_DIR / name, arcname=name)
    zip_sha = sha256_file(ZIP_PATH)
    Path(str(ZIP_PATH) + ".sha256").write_text(f"{zip_sha}  {ZIP_PATH.name}\n", encoding="utf-8")

    # Cursor artifacts store rejects ~300MB ZIP copies (Errno 5). Ship
    # notes/hashes there; the downloadable ZIP stays under patch/Release.
    if ARTIFACTS.is_dir():
        (ARTIFACTS / (ZIP_PATH.name + ".sha256")).write_text(
            f"{zip_sha}  {ZIP_PATH.name}\n", encoding="utf-8"
        )
        (ARTIFACTS / "RELEASE_NOTES.txt").write_text(notes, encoding="utf-8")
        (ARTIFACTS / "INSTALL.txt").write_text(install, encoding="utf-8")
        (ARTIFACTS / "SHA256.txt").write_text("\n".join(sha_lines) + "\n", encoding="utf-8")

    print("VERIFY PASS")
    for k, v in result["checks"].items():
        print(f"  {k} = PASS" if v else f"  {k} = FAIL")
    print(f"Upgrade.ini unique={result['unique']} overflow={result['parsed']['overflow_name']}")
    print(f"DATA SHA256 {data_sha}")
    print(f"ZIP {ZIP_PATH} SHA256 {zip_sha} size={ZIP_PATH.stat().st_size}")
    print("NOT WINDOWS GAMEPLAY VALIDATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
