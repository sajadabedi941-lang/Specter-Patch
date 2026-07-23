Specter_RUNTIME_CRASH_FIX_V2
============================

Purpose: stop ZH "Uncaught Exception during initialization" caused by
FLAT duplicate Object INIs sitting in Data\INI\*.ini while the same
Objects already exist under Data\INI\Object\Specter\...

What Install_Runtime_Fix.bat does:
  1. Creates automatic backup under GameRoot\SpecterPatch_Backup\RuntimeCrashFixV2_<timestamp>\
  2. Scans Data\INI\ (root only) and REMOVES any .ini that:
       - shares a filename with Object\Specter\... files
       - is on the FlatIniBlacklist (1127 names)
       - defines an Object name already present under Object\Specter
       - is a tool schema (CountryBalance / GlobalBuildLimits / Economy)
  3. Removes Data\INI\New folder\ if present
  4. Merges corrected faction-path files from this ZIP into Object\Specter\...
  5. Re-checks specific files (AbbasLauncher, SpecialForces, Turkey_*, AAB, MilitaryHQ)
  6. Does NOT run SHA256 verification

Keep: all faction folders under Object\Specter\ (Britain, Egypt, Turkey, ...)

Install:
  1. Close Generals Zero Hour completely
  2. Extract this ZIP anywhere
  3. Run Install_Runtime_Fix.bat
  4. Enter your GameRoot when prompted
  5. Launch Zero Hour

Packaged corrected files: 56
