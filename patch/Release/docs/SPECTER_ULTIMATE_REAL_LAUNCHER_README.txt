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

  1. Ensure both _SPEC_*.big files are in the game folder
  2. Start generals.exe from that game folder

INSTALL
-------
1. Close Specter / Generals Zero Hour.
2. Extract this ZIP into your game folder (contains generals.exe).
3. Optional once: run Install_SpecterPatch.bat (creates Backup_SpecterPatch).
4. Every time you play: double-click Launch_Specter.bat

Launch_Specter.bat will:
  - find its own folder
  - verify BIG files and generals.exe (pause on error)
  - load both patch BIGs into the game folder
  - start the game with those BIGs active

FINAL TEST
----------
Wine/Windows CMD final tests PASSED before publish.
ZIP SHA256: a937c58f95f2977314ad114cbbaf070a5d990dab43a3fd99a3c33c43a4e65ba2
