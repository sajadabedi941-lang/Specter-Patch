SPECTER CRASH REFERENCE DIAGNOSIS
=================================

Read-only tool. Does NOT modify or delete any files.

HOW TO USE
----------
1. After a crash, leave ReleaseCrashInfo.txt in the game folder
   (same place as Generals.exe / Data\), OR copy it next to this tool.
2. Copy this SPECTER_CRASH_DIAGNOSE folder next to your game Data\ folder.
3. Double-click RUN_CRASH_DIAGNOSE.bat
4. Open CRASH_REFERENCE_REPORT.txt

WHAT IT DOES
------------
1. Reads ReleaseCrashInfo.txt
2. Finds the failing Specter INI / Object name
3. Checks references inside that INI:
     WeaponSet / Weapon
     Armor
     Draw
     Model
     CommandSet
     CommandButton (including buttons listed by the CommandSet)
     Locomotor
     Prerequisite Object =
4. Searches Object\Specter and Data\INI for definitions
5. Writes CRASH_REFERENCE_REPORT.txt with:
     Broken file
     Missing reference
     Fix suggestion

WHAT IT DOES NOT DO
-------------------
- No repairs
- No deletes
- No overwrites of game INIs

FILES
-----
  RUN_CRASH_DIAGNOSE.bat            ← double-click
  DIAGNOSE_CRASH_REFERENCES.ps1     ← used automatically
  CRASH_REFERENCE_REPORT.txt        ← created/updated on run
  README.txt                        ← this file

NOTE
----
Stock Generals definitions inside .big archives are not indexed.
"MISSING" means not found in loose Data\INI / Object\Specter files.
