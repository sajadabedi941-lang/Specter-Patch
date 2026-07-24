SPECTER_CLEAN_PATCH_FINAL_FIXED
================================

Clean Patch overlay for Command & Conquer Generals Zero Hour + Specter.
Original Specter stock files are NOT included and stay untouched.

This package contains ONLY:
  Patch\Data\
  Patch\Art\
  Patch\SYNC_MANIFEST.sha256

No installer. No BAT/PS1. No old manifests. No caches.

------------------------------------------------------------
INSTALL (manual merge)
------------------------------------------------------------

1. Close Generals Zero Hour / Specter completely.

2. Copy / merge:
     Patch\Data   →   <GameRoot>\Data
     Patch\Art    →   <GameRoot>\Art

   Example GameRoot:
     C:\Program Files\EA Games\Command & Conquer Generals Zero Hour\

3. Do NOT replace Data.zip, *.big, Specter_Data*, or _SPEC_* archives.

4. Optional verify (PowerShell), from the extracted folder:
     Get-FileHash Patch\SYNC_MANIFEST.sha256
   Or re-hash Patch\Data and Patch\Art and compare to SYNC_MANIFEST.sha256.

5. Launch Specter / Zero Hour.

------------------------------------------------------------
UNINSTALL
------------------------------------------------------------
Remove the overlay files you copied, or restore from your own backup.
This package does not modify original Specter archives.

------------------------------------------------------------
CONTENTS
------------------------------------------------------------
  Patch\Data\INI\Object\Specter\
  Patch\Data\INI\Weapon\
  Patch\Data\INI\CommandButton\
  Patch\Data\INI\CommandSet\
  Patch\Data\INI\*.ini   (Upgrade / Science / SpecialPower / OCL / FX support)
  Patch\Art\
  Patch\SYNC_MANIFEST.sha256

See VALIDATION_REPORT.txt for scan / hash / INI validation results.
