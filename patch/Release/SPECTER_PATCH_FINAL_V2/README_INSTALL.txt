_SPECTER_PATCH_FINAL_V2.big — STANDALONE SPECTER PATCH
======================================================

Separate patch BIG. Does NOT replace original Specter BIG files.

INSTALL
-------
1. Close Generals / Specter.
2. Copy _SPECTER_PATCH_FINAL_V2.big into your main Specter game folder
   (same folder as):
     _SPEC_ART_ONE.big
     _SPEC_DATA_ONE.big
     EnglishZH.big
     AudioZH.big
3. Launch Specter.

Do NOT overwrite or delete the original BIG files.

LOAD PRIORITY
-------------
Keep original BIGs in place. Add this file beside them:

  AudioZH.big
  EnglishZH.big
  _SPEC_ART_ONE.big
  _SPEC_DATA_ONE.big
  _SPECTER_PATCH_FINAL_V2.big     <--- patch loads after _SPEC_* (overrides)

Case-insensitive name order places _SPECTER_PATCH_FINAL_V2 after
_SPEC_ART_ONE / _SPEC_DATA_ONE so repaired Data/INI and Art entries win.

CONTENTS
--------
Inside the BIG:
  Data\...
  Data\INI\...
  Data\INI\Object\...
  Art\...

Includes CommandCenter final fixes for:
  Ukraine, Vietnam, UAE, Turkey, SouthAfrica, Syria,
  SaudiArabia, Libya, Israel, Pakistan
plus India/Egypt USA-structure CommandCenters, Turkey unit fixes,
India/Libya/Israel MilitaryHQ repairs, and related patch DATA/ART overlays.

USA CommandCenter is the structural/ART donor (us_commandcenter / US_Command / US_COM_Strb).

MULTIPLAYER
-----------
All players must use the same _SPECTER_PATCH_FINAL_V2.big alongside the
same original Specter BIGs. Original multiplayer compatibility is preserved
because base _SPEC_* files are unchanged.
