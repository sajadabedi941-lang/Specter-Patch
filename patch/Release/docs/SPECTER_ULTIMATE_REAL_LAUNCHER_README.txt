SPECTER ULTIMATE EXPANSION - REAL LAUNCHER PACKAGE
==================================================

CONTENTS
--------
  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big
  Install_SpecterPatch.bat
  Launch_Specter.bat
  README.txt

HOW THE LAUNCHER LOADS THE PATCH
--------------------------------
Zero Hour auto-loads .big files from the game folder (next to generals.exe).

Specter uses TWO archives that must both be active:
  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

The ZH command "generals.exe -mod Something.big" only supports ONE archive,
so it cannot enable both Specter BIGs. Launch_Specter.bat uses the correct
multi-BIG method:

  1. Copy/load both _SPEC_*.big files into the game folder
  2. Start generals.exe from that game folder

INSTALL
-------
1. Close Specter / Generals Zero Hour.
2. Extract this ZIP into your game folder (contains generals.exe).
3. Optional once: run Install_SpecterPatch.bat (creates Backup_SpecterPatch).
4. Every time you play: double-click Launch_Specter.bat

Launch_Specter.bat will:
  - verify BIG files and generals.exe
  - load both patch BIGs into the game folder
  - start the game with those BIGs active
