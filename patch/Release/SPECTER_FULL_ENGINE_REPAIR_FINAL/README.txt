SPECTER FULL ENGINE REPAIR FINAL
================================

Repairs ALL Data\INI\Object\Specter\*.ini parse defects that cause:
  ReleaseCrashInfo.txt
  Error parsing INI file

HOW TO USE
----------
1. Close the game.
2. Extract SPECTER_FULL_ENGINE_REPAIR_FINAL.zip
3. Copy the extracted folder into your game folder
   (the folder with Data\ and Generals.exe).
4. Run:
     RUN_SPECTER_FULL_ENGINE_REPAIR.bat
5. Wait for:
     INSTALL SUCCESSFUL
     Specter FULL ENGINE INI REPAIR complete.
6. Optional:
     TEST_SPECTER_LOAD.bat

WHAT IT DOES
------------
[1] Detects GameRoot (Data\INI\Object\Specter\)
[2] Scans EVERY faction folder INI (Britain, Turkey, UAE, Ukraine, ...)
[3] Backs up originals to Specter_EngineRepair_Backup\
[4] Auto-repairs:
      - End; trailing comments
      - uppercase END
      - bare Scale
      - invalid BuildCompletion PLACE_ON_GROUND
      - BOM / newline hygiene
[5] Safe fallback (_FIXED) only if an aircraft file remains unrepairable
[6] Re-scans and writes reports

REPORTS
-------
FULL_INI_SCAN_REPORT.txt
FULL_INI_SCAN_REPORT_AFTER.txt
FINAL_REPAIR_REPORT.txt
TEST_SPECTER_LOAD_REPORT.txt (from TEST_SPECTER_LOAD.bat)

NOTES
-----
- Does not modify maps, models, textures, or .big archives
- Keeps Object names / faction names / weapons / units
- Multiplayer-safe unique IDs preserved
- Goal: GAME START (boot), not rebalance
