SPECTER FINAL PLAYABLE RELEASE
==============================
Britain_CombatDrone init crash fix + British Armed Forces BIG-only pack.

Crash fixed:
  Data\INI\Object\Specter\British Armed Forces\Drones\Britain_CombatDrone.ini
  Removed invalid SCIENCE_UAEStealthJet / UAE leftover from packed Object.
  All British Armed Forces content is inside _SPEC_DATA_ONE.big only.
  Do NOT install loose British Armed Forces INI files.

Contents (runtime only):
  _SPEC_DATA_ONE.big
  HASHES.txt
  README_INSTALL.txt

Install (clean Zero Hour / Specter):
1. Close Generals Zero Hour / GenLauncher.
2. Backup Data\_SPEC_DATA_ONE.big.
3. Replace Data\_SPEC_DATA_ONE.big with this file.
4. Keep Data\_SPEC_ART_ONE.big unchanged.
5. DELETE any loose British Armed Forces folder if present:
     Data\INI\Object\Specter\British Armed Forces\
   Also remove leftover experimental _SPECTER_PATCH_FINAL*.big.
6. If older overlays left tool/flat files, delete:
     Data\INI\CountryBalance.ini
     Data\INI\GlobalBuildLimits_SpecterPatch.ini
     Data\INI\Economy\
     flat dumps like Data\INI\AbbasLauncher.ini / Britain_CombatDrone.ini
7. Launch and play.

This package is BIG-only. Do not extract loose INI from it.
