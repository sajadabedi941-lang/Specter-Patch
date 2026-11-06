Israel Iron Dome Mobile  (BIG install)
======================================

This pack patches SPECTER FINAL archives. It does not copy extra INI
files into Data\INI for the game to run.

Install
-------
1. Extract this folder into SPECTER FINAL (the folder with generals.exe).
2. Run Install_Israel_IronDomeMobile.bat
3. The installer copies the current BIGs into SpecterBackup_IronDomeMobile
   then replaces:
     _SPEC_DATA_ONE.big
     _SPEC_ART_TWO.big
   _SPEC_ART_ONE.big is backed up and not replaced.
4. It removes leftover files from the previous loose v2 installer.
5. If Data\INI\CommandSet.ini is the ss1 duplicate (450860 bytes) or the
   v2 file (450912 bytes), it is removed so the patched BIG is used.
   SAGE loose files beat BIG files of the same path.

Restore
-------
Run Restore_Israel_IronDomeMobile.bat to put the backed-up BIGs back.

What is inside the patched DATA BIG
-----------------------------------
Updated:
  Data\INI\CommandSet.ini
    AirF_AmericaCommandCenterCommandSet slot 11
  Data\INI\CommandSet_SpecterPatch.ini
    Israel_CommandCenterCommandSet slot 1 (kept)
  Data\English\generals.csf
    ss1 strings plus three Iron Dome Mobile labels

Added:
  Data\INI\CommandButton_Israel_VehicleIronDomeMobile.ini
  Data\INI\CommandSet_Israel_VehicleIronDomeMobile.ini
  Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Israel_VehicleIronDomeMobile.ini

What is inside the patched ART TWO BIG
--------------------------------------
Added:
  Art\W3D\BONDKS.W3D
  Art\Textures\T_M978_D01.tga
  Art\Textures\T_M978_D02.tga
  Art\Textures\T_M978_D03.tga
  Art\Textures\concrete_wall_02_D.tga
  Art\Textures\texture_0006.tga
  Art\Textures\texture_0007.tga
  Art\Textures\texture_0008.tga

Unchanged
---------
Israel_AD_IronDome, Israel_AD_Barak8, Israel_MilitaryHQ, Israel dozer,
Israel_CommandCenter.ini, _SPEC_ART_ONE.big.

Buy path
--------
FactionIsrael dozer builds AirF_AmericaCommandCenter.
Select that Command Center. Slot 11 is Iron Dome Mobile.
