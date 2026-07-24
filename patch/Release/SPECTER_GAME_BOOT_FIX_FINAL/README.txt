SPECTER GAME BOOT FIX FINAL
===========================

Fixes chained startup crashes:
  Technical Difficulties / ReleaseCrashInfo.txt
  Error parsing INI file

HOW TO USE
----------
1. Close the game.
2. Extract SPECTER_GAME_BOOT_FIX_FINAL.zip
3. Copy the SPECTER_GAME_BOOT_FIX_FINAL folder into your game root
   (same place as Data\ and Generals.exe).
4. Double-click ONLY:
     INSTALL_SPECTER_GAME_BOOT_FIX.bat
5. Wait for: INSTALL SUCCESSFUL
6. Launch Specter and confirm main menu / Skirmish.

Undo:
  UNINSTALL_SPECTER_GAME_BOOT_FIX.bat

Re-check without reinstalling:
  VERIFY_SPECTER_GAME_BOOT_FIX.bat

WHAT IT DEPLOYS
---------------
Fixed\*.ini  ->  Data\INI\Object\Specter\... (correct faction paths)
Includes all New folder.zip Object INIs (Britain_F35B, CombatDrone, Turkey weapons,
Israel buildings, etc.) plus additional previously repaired Specter INIs.

SAFETY
------
- Backs up overwritten files to Specter_GAME_BOOT_FIX_BACKUP\date_time\
- Does NOT modify *.big / *.zh.big / original Specter archives
- Preserves Object names, factions, weapons, command sets

IMPORTANT — RUNTIME PROOF
-------------------------
The packaging agent could not launch generals.exe (Linux environment, no Wine).
After INSTALL, YOU must launch the game on Windows to confirm boot.
If it still crashes, keep ReleaseCrashInfo.txt and re-run VERIFY.

FILES IN THIS PACKAGE
---------------------
INSTALL_SPECTER_GAME_BOOT_FIX.bat
UNINSTALL_SPECTER_GAME_BOOT_FIX.bat
VERIFY_SPECTER_GAME_BOOT_FIX.bat
INSTALL_SPECTER_GAME_BOOT_FIX.ps1
UNINSTALL_SPECTER_GAME_BOOT_FIX.ps1
VERIFY_SPECTER_GAME_BOOT_FIX.ps1
Fixed\
README.txt
FINAL_CRASH_FIX_REPORT.txt
RUNTIME_CRASH_ITERATIONS.txt
GAME_ROOT_AND_LOAD_ORDER_REPORT.txt
CRASH_CHAIN_REPORT.txt
GLOBAL_REFERENCE_AUDIT.txt
NEW_FOLDER_FILE_VALIDATION.txt
FINAL_MANIFEST.sha256
