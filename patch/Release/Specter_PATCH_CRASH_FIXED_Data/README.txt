Specter_PATCH_CRASH_FIXED
=========================

Repaired files from New folder.zip, placed in the CORRECT Specter patch paths.

ROOT CAUSE (why these files crashed ZH init):
  Installing them as a FLAT dump into Data\INI\ (e.g. Data\INI\AbbasLauncher.ini)
  created DUPLICATE Object definitions alongside the faction-tree copies under
  Data\INI\Object\Specter\... — Generals Zero Hour then throws
  "Uncaught Exception during initialization".

  AbbasLauncher.ini / SpecialForces.ini in the ZIP are TURKEY objects and must
  live under Turkey Armed Forces\ — not UAE (same filename exists for UAE).

This package:
  - Merges 56 corrected files into the proper Object\Specter\... paths
  - DELETES flat Data\INI\<filename> copies that cause duplicate Objects
  - Also removes leftover tool schemas (CountryBalance / Economy / GlobalBuildLimits)

Install:
  1. Close Generals Zero Hour
  2. Run Install_Fix.bat and enter your GameRoot
  3. Launch ZH — Main Menu + Skirmish

Do NOT drop these INIs as loose files into Data\INI\ root.
