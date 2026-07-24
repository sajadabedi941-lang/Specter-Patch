SPECTER ULTIMATE WARFARE — FINAL PLAYABLE GAME BUILD
====================================================

This package contains the REAL playable BIG archives rebuilt from
current main patch sources (MilitaryHQ, CommandCenter USA,
Britain F35B, Saudi MQ-9 drone, seven-country drones, prior INI repairs).

CONTENTS
--------
  _SPEC_DATA_ONE.big          Gameplay / INI archive (REQUIRED)
  _SPEC_ART_ONE.big           Art archive (REQUIRED)
  Install_SpecterPatch.bat    One-click installer for GameRoot
  README_INSTALL.txt          This file
  VERIFY_REPORT.txt           Content verification inside the BIGs
  *.sha256                    Checksums

WHAT THIS FIXES IN THE RUNNING GAME
-----------------------------------
The game loads BIG archives, not loose patch/Data INI files.
These BIGs include the latest main-branch changes:
  - MilitaryHQ_StockFactions USA Command Center assets
  - 12-country CommandCenter USA replacements
  - Britain F35B based on working USA F-35 donor (US_F35A / F35C weapons)
  - Saudi CombatDrone based on working USA MQ-9 (US_MQ9)
  - Seven-country CombatDrones on USA MQ-9
  - Prior INI repairs already on main

INSTALL (recommended)
---------------------
1. Close Generals / Specter completely.
2. Unzip this package anywhere.
3. Double-click Install_SpecterPatch.bat
4. When asked, enter your Specter GameRoot path
   (folder that contains generals.exe / existing _SPEC_*.big).
5. Wait for: INSTALLATION COMPLETED SUCCESSFULLY
6. Launch Specter.

Manual install (optional)
-------------------------
1. Backup GameRoot _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big
2. Copy the two BIG files from this ZIP into GameRoot (replace)
3. Launch Specter

SHA256
------
See _SPEC_DATA_ONE.big.sha256, _SPEC_ART_ONE.big.sha256, and the
release file SPECTER_FINAL_PLAYABLE_BUILD.sha256 for the Combined ZIP.
