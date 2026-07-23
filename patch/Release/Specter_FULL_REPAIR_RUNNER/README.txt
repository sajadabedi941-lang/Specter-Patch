Specter FULL REPAIR RUNNER
==========================

Simple installer — no GameRoot typing, no folder picker.

HOW TO INSTALL
--------------
1. Close Generals Zero Hour / Specter.

2. Extract Specter_FULL_REPAIR_RUNNER.zip

3. Copy EVERYTHING from the extracted folder into your main game folder
   (the folder that already contains Data\ and Generals.exe).

   Example game folder:
     SPECTER FINAL (GeneralsMode.com)

   After copy, your game folder should contain:
     Data\                          (your existing game data)
     Specter_FULL_REPAIR_Data\      (repaired patch files — payload)
     RUN_SPECTER_FULL_REPAIR.bat
     UNINSTALL_SPECTER_FULL_REPAIR.bat
     ...

4. Inside that game folder, double-click:
     RUN_SPECTER_FULL_REPAIR.bat

5. Wait for:
     INSTALL SUCCESSFUL
     Specter FULL INI Repair activated.

The BAT uses its own location (%~dp0) as the game folder.
It does NOT ask for GameRoot.

WHAT IT DOES
------------
- Shows the detected game path
- Checks that Data\ exists
- Creates a backup under SpecterPatch_Backup\FULL_REPAIR_*
- Copies repaired files from Specter_FULL_REPAIR_Data\ into Data\
- Removes dangerous flat Data\INI\*.ini duplicates from the New folder dump

NOTE ABOUT "Data"
-----------------
The repaired files are shipped as Specter_FULL_REPAIR_Data\ so they do NOT
collide with your live game Data\ folder before the installer runs.
The installer copies them into Data\ after creating a backup.

HOW TO UNINSTALL / ROLLBACK
---------------------------
1. Double-click UNINSTALL_SPECTER_FULL_REPAIR.bat in the same game folder
2. Wait for UNINSTALL SUCCESSFUL

CONTENTS
--------
- RUN_SPECTER_FULL_REPAIR.bat
- UNINSTALL_SPECTER_FULL_REPAIR.bat
- Install_Specter_Full_Repair.ps1
- Uninstall_Specter_Full_Repair.ps1
- Specter_FULL_REPAIR_Data\   (repaired Data files)
- RepairManifest.txt
- FlatIniBlacklist.txt
- README.txt

NOTES
-----
- Paths with spaces, parentheses, and Persian characters are supported.
- Every path operation uses quoted -LiteralPath handling.
- Do NOT drop New folder files as flat Data\INI\*.ini
- Keep a copy of this ZIP if you want to re-install later
