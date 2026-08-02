SPECTER — ADVANCED AIR BASE FIVE-AIRCRAFT FULL RELEASE
======================================================

Full replacement Specter BIG archives (not a small overlay patch).

CONTENTS
--------
  _SPEC_DATA_ONE.big       Gameplay / INI archive (REQUIRED)
  _SPEC_ART_ONE.big        Art archive (REQUIRED)
  Install_SpecterPatch.bat One-click installer
  README_INSTALL.txt       This file
  VERIFY_REPORT.txt        Load-order / content verification
  HASHES.txt               SHA256 checksums
  ANALYSIS_AND_MERGE_REPORT.txt

ADVANCED AIR BASE PRODUCES ONLY
-------------------------------
  1. B-2 Spirit
  2. B-21 Raider
  3. B-52 Stratofortress
  4. E-3 AWACS
  5. AN-225 Mriya

All other aircraft were removed from Advanced Air Base CommandSets.
Normal faction airfields are unchanged (fighters/helos remain there).

INSTALL (recommended)
---------------------
1. Close Generals / Specter completely.
2. Unzip this package.
3. Double-click Install_SpecterPatch.bat
4. Enter your Specter GameRoot path
   (folder containing generals.exe and existing _SPEC_*.big).
5. Wait for: INSTALLATION COMPLETED SUCCESSFULLY
6. Launch Specter.

MANUAL INSTALL
--------------
1. Backup GameRoot\_SPEC_DATA_ONE.big and GameRoot\_SPEC_ART_ONE.big
2. Copy both BIG files from this ZIP into GameRoot (replace)
3. Launch Specter

NOTES
-----
- This is a FULL merge into _SPEC_DATA_ONE / _SPEC_ART_ONE (previous Specter
  entries preserved; Cursor patch Data/Art merged in).
- Do not install a separate loose patch/Data tree for this release.
- Multiplayer: every client must use the same BIG pair.

SPLIT ZIP (repository distribution)
-----------------------------------
If you received SPECTER_AAB_FIVE_AIRCRAFT_FULL.z01 … .z25 + .zip:
1. Keep ALL parts in the same folder
2. Extract with 7-Zip / WinRAR starting from SPECTER_AAB_FIVE_AIRCRAFT_FULL.zip
   or: 7z x SPECTER_AAB_FIVE_AIRCRAFT_FULL.zip
3. Open the extracted SPECTER_AAB_FIVE_AIRCRAFT_FULL folder
4. Run Install_SpecterPatch.bat
