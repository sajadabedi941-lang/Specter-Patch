SPECTER FINAL PLAYABLE — CLEAN BASE REBUILD (tool INIs excluded)
================================================================

BIG SHA256: f69c8dd4fc804c9537f4961be5dd36647e2567a718a611f91fab5b3abf6e7d4b
BIG SIZE:   384158503

This _SPEC_DATA_ONE.big was rebuilt from the original working Specter DATA BIG
plus patch/Data with non-game tool INIs excluded:
  - Data/INI/CountryBalance.ini
  - Data/INI/Economy/*.ini
  - Data/INI/GlobalBuildLimits_SpecterPatch.ini

Those configs live only at:
  patch/tools/economy/config/

Install:
  1. Replace Data\_SPEC_DATA_ONE.big with this file
  2. Keep Data\_SPEC_ART_ONE.big
  3. Do NOT copy CountryBalance.ini / Economy/*.ini / GlobalBuildLimits_*.ini
     into GameRoot Data\INI
  4. Delete leftover _SPECTER_PATCH_FINAL*.big if present

Goal: reach main menu (no tool-schema init crash).
No new gameplay content in this rebuild step.
