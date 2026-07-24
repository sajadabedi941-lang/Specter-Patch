SPECTER ENGINE REPAIR — FINAL
=============================

Fixes "Error parsing INI file" crashes caused by broken Specter Object INIs.

HOW TO USE (non-technical)
--------------------------
1. Close Generals Zero Hour / Specter.
2. Unzip Specter_ENGINE_REPAIR_FINAL.zip
3. Copy the extracted files into your game folder
   (the folder that contains Data\ and Generals.exe).
4. Double-click:
     RUN_SPECTER_ENGINE_REPAIR.bat
5. Wait until you see SUCCESS.
6. Press any key to close.
7. Start the game.

That is all. No PowerShell commands. No manual editing.

WHAT IT DOES
------------
- Finds Data\INI\Object\Specter automatically
- Scans ALL *.ini files in every Specter subfolder
- Detects parse errors (missing End, End; comments, invalid Object,
  ModuleTag issues, quotes, braces, bad parameters, command sets, etc.)
- Creates backup:
    Specter_ENGINE_REPAIR_BACKUP\date_time\
- Repairs only REAL files that fail verification
- Never creates fake / placeholder unit files
- Re-scans every file after repair
- Writes REPAIR_REPORT.txt next to this README

KNOWN CRASH TARGETS
-------------------
Also checked specifically:
  British Armed Forces\Airforce\Britain_F35B.ini
  British Armed Forces\Drones\Britain_CombatDrone.ini
(Entire Specter tree is scanned — more errors may exist elsewhere.)

FILES IN THIS PACKAGE
---------------------
  RUN_SPECTER_ENGINE_REPAIR.bat   ← run this
  AUTO_REPAIR_ENGINE.ps1          ← used automatically by the BAT
  REPAIR_REPORT.txt               ← overwritten when you run
  README.txt                      ← this file

IF SOMETHING GOES WRONG
-----------------------
- The window will NOT close by itself (press a key after reading).
- Open REPAIR_REPORT.txt
- Originals are in Specter_ENGINE_REPAIR_BACKUP\
