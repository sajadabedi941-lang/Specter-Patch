USAPAC3 — America Command Center slot 6 (Rank 3 lock)
=====================================================

Object USAPAC3 already had Prerequisites Science = SCIENCE_Rank3
(same placement as overlay America_AD_THAAD). That Object gate is not
what ControlBar uses for UNIT_BUILD on the Command Center.

Command_ConstructUSAPAC3 had no Science line, so the button stayed
enabled. Live Specter rank-gates UNIT_BUILD with:

  Science = SCIENCE_Rank3

on the CommandButton (same field Command_US_Tier3 / overlay China
UNIT_BUILD buttons use). That line is now on Command_ConstructUSAPAC3.
Object cost, time, weapons, models, and CC slot 6 are unchanged.

INSTALL
-------
1. Close Generals / Specter.
2. Extract the ZIP. Keep every file next to Launch_Specter.bat.
3. Do not replace canonical _SPEC_ART_ONE.big (2,145,283,309 bytes).
4. Run Launch_Specter.bat.

ART ONE: https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/specter-unified/_SPEC_ART_ONE.big
