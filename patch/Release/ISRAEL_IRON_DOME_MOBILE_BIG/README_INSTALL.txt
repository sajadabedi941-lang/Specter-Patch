Israel Iron Dome Mobile  (BIG install)
======================================

This pack patches SPECTER FINAL archives. It does not copy extra INI
files into Data\INI for the game to run.

Install
-------
1. Extract this folder into SPECTER FINAL (the folder with generals.exe).
2. Run Install_Israel_IronDomeMobile.bat
3. The installer checks for generals.exe, then copies the current BIGs
   into SpecterBackup_IronDomeMobile and verifies each copy
   byte-for-byte. Only after that backup finishes does it replace:
     _SPEC_DATA_ONE.big
     _SPEC_ART_TWO.big
   _SPEC_ART_ONE.big is backed up and not replaced.
4. Re-running the installer does not overwrite an existing verified
   backup (BACKUP_COMPLETE.txt). A stopped install can still be
   restored from that folder.

CommandSet.ini
--------------
Live file:
  <game>\Data\INI\CommandSet.ini

Backup path and name:
  <game>\SpecterBackup_IronDomeMobile\Data\INI\CommandSet.ini

The installer copies that file, checks it with fc /b against the live
file, and deletes the live file only if SHA-256 is the known ss1 value:

  f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223

Size is not used. Any other hash is left in place, except the known
Iron Dome Mobile v2 leftover hash, which is removed as v2 cleanup and
is not stored as the ss1 original.

Restore
-------
Run Restore_Israel_IronDomeMobile.bat.

It puts the three backed-up BIGs back (ART_ONE only if it was backed
up), copies the ss1 CommandSet.ini backup back to Data\INI\CommandSet.ini
after hashing it, and removes v2 loose files only when SHA-256 matches
the v2 installer files listed in KNOWN_HASHES.txt.

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

In-game test
------------
Not run. These checks are archive and installer-script only.
