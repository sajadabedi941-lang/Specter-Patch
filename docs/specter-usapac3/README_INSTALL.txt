USAPAC3 — America Command Center slot 6 (CommandSet crash fix)
==============================================================

CAUSE OF CRASH
--------------
CommandSet.ini line 2572 (AmericaCommandCenterCommandSet) referenced
Command_ConstructUSAPAC3, but that button was only in
CommandButton_USAPAC3.ini. Zero Hour parses CommandSet.ini / CommandButton.ini
before unique-path INI files, so load crashed on that CommandSet.

FIX
---
Command_ConstructUSAPAC3 / Object = USAPAC3 is now in CommandButton.ini.
CommandSet.ini slot 6 is unchanged. CommandButton_USAPAC3.ini was removed
from DATA so the button name is defined once.

INSTALL
-------
1. Close Generals / Specter.
2. Extract the ZIP. Keep every file next to Launch_Specter.bat.
3. Do not replace canonical _SPEC_ART_ONE.big
   (2,145,283,309 bytes, original Full Release).
4. Run Launch_Specter.bat. It copies DATA, ART TWO, CommandSet.ini, and
   CommandButton.ini into the game folder / Data\INI\.
5. Keep _SPECTER_PATCH_FINAL.big deleted.

ART ONE: https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-unified/_SPEC_ART_ONE.big
