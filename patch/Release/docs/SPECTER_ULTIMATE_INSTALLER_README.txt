SPECTER ULTIMATE EXPANSION — STANDALONE INSTALLER
=================================================

Automatic installer for the final combined playable BIG release.
No manual file copying required.

CONTENTS
--------
  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big
  Install_SpecterPatch.exe
  Launch_Specter.bat
  README.txt

INSTALL (recommended)
---------------------
1. Close Generals / Specter if it is running.
2. Unzip SPECTER_ULTIMATE_INSTALLER.zip to any folder
   (Desktop or Downloads is fine).
3. Double-click Install_SpecterPatch.exe
4. If GameRoot is not auto-detected, select the folder that contains
   generals.exe and your current Specter BIG files.
5. Wait for: INSTALLATION COMPLETED SUCCESSFULLY
6. Choose Yes to launch Specter, or use the desktop shortcut
   "Specter Ultimate Expansion", or Launch_Specter.bat

What the installer does
-----------------------
  1. Detects Specter GameRoot automatically (or asks for the folder)
  2. Backs up existing _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big
  3. Copies the new BIG files into GameRoot
  4. Confirms installation success
  5. Creates a desktop shortcut named "Specter Ultimate Expansion"
  6. Offers to launch generals.exe

REQUIREMENTS
------------
  - Windows with .NET Framework 4.x (included on modern Windows)
  - Specter / Generals Zero Hour GameRoot with generals.exe

NOTES
-----
  - Do not stack older SPECTER_*_PLAYABLE ZIP installs on top of this.
  - Backups are stored in GameRoot\SpecterBIG_Backup_<timestamp>\
  - Launch_Specter.bat uses the GameRoot saved by the installer.
