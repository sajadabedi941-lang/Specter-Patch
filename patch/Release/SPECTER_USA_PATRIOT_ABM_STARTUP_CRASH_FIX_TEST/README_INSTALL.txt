SPECTER USA Patriot PAC-3 — ABM startup crash fix
=================================================

Baseline: specter-usa-patriot-new-donor-thaad-test (healthy).
Broken pack: specter-usa-patriot-abm-fix-test (immediate startup crash).
PAC-3 v1–v8 is not used.

Install
-------
1. Extract this ZIP into SPECTER FINAL (the folder with generals.exe).
2. Replace only:
     _SPEC_DATA_ONE.big
3. Do not replace _SPEC_ART_TWO.big or _SPEC_ART_ONE.big.
   Loose Data\INI is not in this ZIP.

What crashed
------------
USAPAC3_THAAD_ABM_OBJECT had ClientUpdate immediately followed by Geometry
with no End. ClientUpdate is a module (parseModuleName -> initFromINI until
End). That End closed ClientUpdate, so Object USAPAC3 was parsed into the
projectile (duplicate ModuleTag_01). ZH throws Uncaught Exception during
initialization.

Fix
---
Same ClientUpdate End as THAAD_AA_OBJECT1 / THAAD_ABM_OBJECT:
  ClientUpdate = AnimatedParticleSysBoneClientUpdate ModuleTag_08
End
  Geometry ...
End

ABM CRUSH weapon/projectile kept. PRIMARY AA, Donor Guard/Draw/FIREPOINT,
US_THAAD, Weapon.ini, other AD unchanged.

In-game test
------------
Not run on this machine. Archive/hash/INI checks only.
