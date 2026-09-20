SPECTER ULTIMATE EXPANSION — FINAL INSTALLER (BAT)
==================================================

Simple Windows batch installer. No EXE required.

CONTENTS
--------
  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big
  Install_SpecterPatch.bat
  Launch_Specter.bat
  README_INSTALL.txt

INCLUDED IN THE BIG FILES
-------------------------
  Turkey aircraft
  UAE / Japan MQ-9
  MilitaryHQ fixes
  Multi-unit repairs
  Air Force Expansion aircraft
  Seven country drones
  (+ prior combined Ultimate Expansion content)

INSTALL — RECOMMENDED
---------------------
1. Close Generals / Specter.
2. Open your Specter game folder, for example:
     SPECTER FINAL (GeneralsMode.com)
3. Extract SPECTER_ULTIMATE_FINAL_INSTALLER.zip INTO that folder
   so you get a subfolder:
     SPECTER FINAL (GeneralsMode.com)\SPECTER_ULTIMATE_FINAL_INSTALLER\
4. Open that subfolder and double-click Install_SpecterPatch.bat
5. Wait for:
     INSTALLATION COMPLETED SUCCESSFULLY
6. Launch with Launch_Specter.bat or generals.exe

What the installer does
-----------------------
  - Detects its own folder automatically
  - Detects Specter GameRoot (this folder / parent / ask)
  - Creates BACKUP_SPECTER_DATE_TIME and copies old BIG files there
  - Copies the two new BIG files into GameRoot only
  - Does not modify any other original game folders

ALTERNATE: extract flat into GameRoot
-------------------------------------
If you extract the ZIP files directly into SPECTER FINAL
(so Install_SpecterPatch.bat sits next to generals.exe), run
Install_SpecterPatch.bat there. It will detect GameRoot and
verify the BIG files are in place.

NOTES
-----
  - Only _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big are replaced.
  - Old BIGs are saved under BACKUP_SPECTER_<DATE_TIME>\
  - Do not stack older playable ZIP installs on top of this.
