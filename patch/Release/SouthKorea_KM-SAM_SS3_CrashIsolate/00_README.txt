SPECTER SS3 — KM-SAM crash isolation (reversible)

This pack does NOT rewrite KM-SAM. It temporarily stops loading KM-SAM
so you can test whether the South Korea map-entry crash is caused by
the KM-SAM transfer.

HOW TO DISABLE (test)
1. Backup your SPECTER SS3 game folder first.
2. Unzip SouthKorea_KM-SAM_SS3_CrashIsolate_DISABLE.zip into the folder
   that contains generals.exe, so Data/INI/... overwrites the KM-SAM files.
3. Start SPECTER, pick South Korea, finish countdown, enter the map.
4. Report whether the crash is gone.

HOW TO RESTORE
Unzip SouthKorea_KM-SAM_SS3_CrashIsolate_RESTORE.zip into the same game
folder. Original KM-SAM files return. Nothing is permanently deleted.

Launch_Specter.bat does not copy these loose INI files. Unzip into the
game folder yourself.

Art (SKKMSAM.W3D / textures) is left in place. Unused art does not
define Objects.

Healthy baseline compared: git 41ffdc91 (immediately before the first
KM-SAM transfer commit 77e507d7).
