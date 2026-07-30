SPECTER FINAL PLAYABLE RELEASE
==============================
PR #206 final playable Data BIG for clean Zero Hour / Specter installs.

Contents (runtime only):
  _SPEC_DATA_ONE.big
  HASHES.txt
  README_INSTALL.txt

Install (clean Zero Hour / Specter game folder):
1. Close Generals Zero Hour / GenLauncher completely.
2. Backup your current Data\_SPEC_DATA_ONE.big.
3. Copy this _SPEC_DATA_ONE.big into the game Data\ folder
   (replace the existing file).
4. Keep Data\_SPEC_ART_ONE.big unchanged.
5. Remove leftover experimental patch BIGs if present next to the game
   (examples: _SPECTER_PATCH_FINAL*.big). Do not keep old test BIGs.
6. For a clean install after older Specter patch overlays, also delete
   stale loose tool/flat files under Data\INI\ if present:
     CountryBalance.ini
     GlobalBuildLimits_SpecterPatch.ini
     CommandButton_RuntimeFix_RussiaRS24.ini
     Economy\  (folder)
     any flat New-folder dumps such as AbbasLauncher.ini in Data\INI\
7. Launch generals.exe / Specter from the game folder and play.

Do NOT extract loose INI from this package — this release is BIG-only.
