SPECTER FULL ENGINE REPAIR FINAL
================================

Fixes Generals Zero Hour Specter crashes:
  ReleaseCrashInfo.txt → "Error parsing INI file"

HOW TO USE (only steps needed)
------------------------------
1. Close the game.
2. Extract SPECTER_ENGINE_REPAIR_FINAL.zip
3. Copy the SPECTER_ENGINE_REPAIR_FINAL folder next to your game
   (same place as Data\ and Generals.exe), OR inside the game folder.
4. Right-click INSTALL_SPECTER_REPAIR.bat → Run as administrator
5. Wait for SUCCESS.
6. Start the game.

To undo:
  Run UNINSTALL_SPECTER_REPAIR.bat (restores newest backup).

WHAT THIS PACKAGE CONTAINS
--------------------------
  INSTALL_SPECTER_REPAIR.bat     ← run this
  UNINSTALL_SPECTER_REPAIR.bat   ← undo / restore backup
  AUTO_REPAIR_ENGINE.ps1         ← repairs + REPLACES broken INIs
  SCAN_ALL_SPECTER_INI.ps1       ← full tree scan / verify
  Repair_Report.txt              ← results (updated by INSTALL)
  README.txt                     ← this file
  Fixed\                         ← pre-repaired INI files (deployed by INSTALL)

WHAT INSTALL DOES
-----------------
[1] Auto-detects game folder (Data\INI\Object\Specter)
[2] Pre-scans ALL Specter *.ini (every faction subfolder)
[3] Backs up originals to:
      Specter_ENGINE_REPAIR_BACKUP\date_time\
[4] Copies Fixed\ repaired INIs into the game (actual REPLACE)
[5] Auto-repairs any other broken INIs still found
[6] Writes repaired copies into Fixed\
[7] Re-scans and writes Repair_Report.txt
[8] Pauses with SUCCESS or FAILURE (window never auto-closes)

KNOWN TARGETS (always checked)
------------------------------
  British Armed Forces\Airforce\Britain_F35B.ini
  Turkey Armed Forces\Turkey_WeaponObjects.ini
  Israel Defense Forces\Buildings\Israel_CommandCenter.ini
  Israel Defense Forces\Buildings\Israel_MilitaryHQ.ini

Plus every other Specter INI automatically.

NOTES
-----
- No manual file moving after extract + copy folder
- No manual PowerShell commands
- Relative paths only (works from any drive / folder name)
- Does not modify maps, models, textures, or .big archives
- Keeps Object / faction / weapon names (multiplayer-safe IDs)
