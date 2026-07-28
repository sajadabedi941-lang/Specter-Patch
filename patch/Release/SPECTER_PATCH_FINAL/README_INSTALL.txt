_SPECTER_PATCH_FINAL.big — STANDALONE SPECTER ULTIMATE PATCH
============================================================

Separate patch BIG. Does NOT replace original Specter BIG files.

INSTALL
-------
1. Close Generals / Specter.
2. Copy _SPECTER_PATCH_FINAL.big into your main Specter game folder
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
  _SPECTER_PATCH_FINAL.big     <--- patch loads after _SPEC_* (overrides)

Case-insensitive name order places _SPECTER_PATCH_FINAL after
_SPEC_ART_ONE / _SPEC_DATA_ONE so repaired Data/INI and Art entries win.

CONTENTS
--------
Inside the BIG:
  Data\
  Data\INI\
  Data\INI\Object\
  Art\

Includes all previous repairs for:
  Turkey, India, Israel, Libya, Pakistan, SaudiArabia, UAE,
  SouthAfrica, Syria, Ukraine, Vietnam, Egypt, Japan

- CommandCenter / MilitaryHQ USA-structure donors
- Building portrait identity remaps (irq_* -> USA)
- Aircraft / UAV / WeaponObjects / CommandButton overlays from prior fixes
- Patch Art textures

MULTIPLAYER
-----------
All players must use the same _SPECTER_PATCH_FINAL.big alongside the
same original Specter BIGs. Original multiplayer compatibility is preserved
because base _SPEC_* files are unchanged.
