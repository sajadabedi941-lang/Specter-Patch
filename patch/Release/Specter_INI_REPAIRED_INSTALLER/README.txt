Specter INI REPAIRED INSTALLER
==============================

Install repaired INI files into the correct Specter Object paths.

HOW TO USE
----------
1. Close Generals Zero Hour / Specter.

2. Extract Specter_INI_REPAIRED_INSTALLER.zip

3. Copy the extracted folder (or its contents) into your game folder
   (the folder that contains Data\ and Generals.exe).

4. Double-click:
     RUN_SPECTER_INI_REPAIR.bat

5. Progress:
     [1/4] Detecting game folder
     [2/4] Creating backup
     [3/4] Installing repaired INI files
     [4/4] Verifying installation

6. Success message:
     INSTALL SUCCESSFUL
     Repaired INI files installed.

WHAT IT DOES
------------
- Auto-detects the game root (looks for Data\INI\Object\Specter\)
- If not found, opens a folder picker
- Asks before overwriting existing files (Yes / No skip / Cancel)
- Backs up replaced files to:
    Specter_INI_Backup\INI_REPAIR_<timestamp>\
- Copies each repaired INI to the correct faction path under:
    Data\INI\Object\Specter\<Faction>\...
- Does NOT install as flat Data\INI\*.ini
- Does NOT modify maps, models, textures, or archives

UNINSTALL / ROLLBACK
--------------------
Run UNINSTALL_SPECTER_INI_REPAIR.bat in the same folder.
It restores files from Specter_INI_Backup.

CONTENTS
--------
- RUN_SPECTER_INI_REPAIR.bat
- UNINSTALL_SPECTER_INI_REPAIR.bat
- Install_Specter_INI_Repair.ps1
- Uninstall_Specter_INI_Repair.ps1
- PlacementMap.txt
- Specter_INI_REPAIRED\   (repaired INI files)
- README.txt

NOTES
-----
- Supports paths with spaces and parentheses
- Multiplayer-safe (same unique Object IDs; path placement only)
- Keep this ZIP if you want to reinstall later
