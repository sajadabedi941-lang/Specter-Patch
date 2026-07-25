SPECTER ULTIMATE EXPANSION - WORKING INSTALLER
==============================================

CONTENTS
--------
  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big
  Install_SpecterPatch.bat
  Launch_Specter.bat
  README.txt

HOW TO INSTALL
--------------
1. Close Command & Conquer Generals Zero Hour / Specter.
2. Open your game folder (the folder that contains generals.exe).
3. Extract this ZIP into that game folder so you get:

     <GameFolder>\SPECTER_ULTIMATE_WORKING_INSTALLER\
         Install_SpecterPatch.bat
         Launch_Specter.bat
         _SPEC_DATA_ONE.big
         _SPEC_ART_ONE.big
         README.txt

4. Open SPECTER_ULTIMATE_WORKING_INSTALLER
5. Right-click Install_SpecterPatch.bat -> Run as administrator
   (or double-click; it will ask for Administrator permission)
6. Wait for these messages:
     Backup completed
     Installing Specter Patch...
     Installation completed successfully

7. Start the game with Launch_Specter.bat or generals.exe

WHAT IT DOES
------------
  - Detects its own folder automatically
  - Uses the parent folder as the game root
  - Backs up existing BIG files to BACKUP_SPECTER_DATE_TIME
  - Copies only _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big
  - Does not modify other game folders

TROUBLESHOOTING
---------------
  ERROR: Wrong game folder
    -> Move this installer folder inside the directory that
       contains generals.exe, then run again.

  ERROR: BIG files missing
    -> Re-extract the ZIP. Both BIG files must sit next to
       Install_SpecterPatch.bat
