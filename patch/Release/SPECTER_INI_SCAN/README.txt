SPECTER INI SCAN
================

Double-click RUN_SCAN.bat

WHAT IT DOES
------------
- Finds Data\INI\Object\Specter automatically
- Scans EVERY .ini file (all subfolders)
- Checks for:
    missing End blocks
    malformed Object headers
    duplicate Object names
    empty files
    invalid syntax characters ({ } / bad quotes)
    End; trailing comments, uppercase END, etc.
- Writes INI_ERROR_REPORT.txt next to this folder
- Copies broken files into:
    Specter_INI_SCAN_BACKUP\date_time\
  (safety copies only — before any future repair)

WHAT IT DOES NOT DO
-------------------
- Does NOT delete anything
- Does NOT modify / overwrite game INI files
- Does NOT repair (scan + report + backup only)

HOW TO USE
----------
1. Close the game (optional but recommended)
2. Copy this folder next to your game Data\ folder
3. Double-click RUN_SCAN.bat
4. Open INI_ERROR_REPORT.txt

FILES
-----
  RUN_SCAN.bat           ← double-click this
  SCAN_SPECTER_INI.ps1   ← used automatically
  INI_ERROR_REPORT.txt   ← created/updated when you run
  README.txt             ← this file
