SPECTER_PATCH_HASH_FIXED_FINAL
==============================

Fixes installer "Manifest verify FAIL / HASH_MISMATCH" by regenerating
SYNC_MANIFEST.sha256 from the CURRENT patch files.

Contents:
  patch\
    SYNC_MANIFEST.sha256   (new, current hashes)
    Install_SpecterPatch.bat / .ps1
    Uninstall_SpecterPatch.bat / .ps1
    Verify_SpecterPatch.bat / .ps1
    Run_SpecterPatch.bat / .ps1
    Data\
    Art\
    tools\

Install:
1. Extract this ZIP
2. Copy the "patch" folder into your Specter / Zero Hour GameRoot
3. Run patch\Run_SpecterPatch.bat (or Install_SpecterPatch.bat)
4. Expect: Manifest verify PASS, HASH_MISMATCH = 0, INSTALLATION SUCCESSFUL

No gameplay changes. Manifest-only fix.
