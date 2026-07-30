SPECTER FINAL PLAYABLE RELEASE
==============================
Britain_CombatDrone init crash fix (SCIENCE_UAEStealthJet removed).

Crash fixed:
  File   : Data\INI\Object\Specter\British Armed Forces\Drones\Britain_CombatDrone.ini
  Object : Britain_CombatDrone
  Cause  : Prerequisites Science = SCIENCE_UAEStealthJet (Science not defined)
  Fix    : Keep Britain_AdvancedAirBase + SCIENCE_Rank3 only; packed in BIG

Contents:
  _SPEC_DATA_ONE.big
  HASHES.txt
  README_INSTALL.txt
  VALIDATION_REPORT.txt
  CRASH_ROOT_CAUSE_REPORT.txt

Install:
1. Close Generals Zero Hour / GenLauncher.
2. Backup Data\_SPEC_DATA_ONE.big.
3. Replace Data\_SPEC_DATA_ONE.big with this file.
4. Keep Data\_SPEC_ART_ONE.big unchanged.
5. DELETE if present:
     Data\INI\Object\Specter\British Armed Forces\
     Data\INI\Britain_CombatDrone.ini
     _SPECTER_PATCH_FINAL*.big
6. Launch and play.

Do not extract loose INI from this package.
