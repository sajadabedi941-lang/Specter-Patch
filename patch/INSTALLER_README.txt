Specter Ultimate Warfare Expansion — Safe Patch Installer
=========================================================

Phases activated: A → I (land / air / missile / drone / air defense)
Compatible with: Command & Conquer Generals Zero Hour + Specter mod
Multiplayer: every lobby client must install THIS same package

Exact installer files (must exist in this folder)
-------------------------------------------------
  patch/Install_SpecterPatch.bat
  patch/Uninstall_SpecterPatch.bat
  patch/Verify_SpecterPatch.bat
  patch/INSTALLER_README.txt

Companion engines (also required for full verify/rollback)
---------------------------------------------------------
  patch/Install_SpecterPatch.ps1
  patch/Uninstall_SpecterPatch.ps1
  patch/Verify_SpecterPatch.ps1
  patch/SYNC_MANIFEST.sha256

---------------------------------------------------------
QUICK START (Windows)
---------------------------------------------------------

1. Copy the entire "patch" folder into your Specter / Zero Hour game root
   so you have:

     <GameRoot>\
       generals.exe / GeneralsZH.exe / Data.zip / Art\ / Data\ ...
       patch\
         Install_SpecterPatch.bat
         Uninstall_SpecterPatch.bat
         Verify_SpecterPatch.bat
         INSTALLER_README.txt
         Install_SpecterPatch.ps1
         Data\
         Art\
         SYNC_MANIFEST.sha256

2. Right-click Install_SpecterPatch.bat → Run as administrator
   (recommended if the game is under Program Files)

3. Wait for progress + SYNC_MANIFEST verification

4. Read PATCH_INSTALLED.txt in the game root

5. To roll back: run Uninstall_SpecterPatch.bat

Optional: Verify_SpecterPatch.bat — re-check hashes anytime

---------------------------------------------------------
WHAT THE INSTALLER DOES
---------------------------------------------------------

SAFE:
- Detects game root automatically (parent of patch\, common paths, registry)
- Backs up any ORIGINAL file it will overwrite into:
    <GameRoot>\SpecterPatch_Backup\<timestamp>\
- Merges patch\Data  →  <GameRoot>\Data
- Merges patch\Art   →  <GameRoot>\Art
- Verifies installed Data/Art files with SYNC_MANIFEST.sha256
- Writes PATCH_INSTALLED.txt (game root + patch folder)
- Tracks state in <GameRoot>\SpecterPatch_InstallState\

NEVER TOUCHES:
- *.big
- Data.zip
- _SPEC_*
- Specter_Data*
- payload.rar

This preserves Specter archives and keeps the install multiplayer-safe
(identical loose overlay for all clients).

---------------------------------------------------------
ROLLBACK / UNINSTALL
---------------------------------------------------------

Uninstall_SpecterPatch.bat will:
1. Restore files from the active backup snapshot
2. Delete overlay files that the patch newly added
3. Remove PATCH_INSTALLED.txt markers
4. KEEP the backup folder on disk (manual delete later if desired)

---------------------------------------------------------
COMMAND LINE (PowerShell)
---------------------------------------------------------

  powershell -ExecutionPolicy Bypass -File .\Install_SpecterPatch.ps1
  powershell -ExecutionPolicy Bypass -File .\Install_SpecterPatch.ps1 -GameRoot "D:\Games\Specter"
  powershell -ExecutionPolicy Bypass -File .\Install_SpecterPatch.ps1 -Force
  powershell -ExecutionPolicy Bypass -File .\Uninstall_SpecterPatch.ps1 -GameRoot "D:\Games\Specter"
  powershell -ExecutionPolicy Bypass -File .\Verify_SpecterPatch.ps1

Exit codes (installer):
  0 = success + verify pass
  2 = merged OK but verify warnings
  1 = errors

---------------------------------------------------------
MULTIPLAYER SYNC
---------------------------------------------------------

Host and all clients must install the same patch package
(same SYNC_MANIFEST.sha256 PackageSHA256).

Do not mix partial copies. Do not edit files after install
unless everyone updates together.
