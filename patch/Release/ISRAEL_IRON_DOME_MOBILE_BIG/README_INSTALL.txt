Israel Iron Dome Mobile  (BIG install)
======================================

This pack patches SPECTER FINAL archives. It does not copy extra INI
files into Data\INI for the game to run.

Why the previous Israel_CommandCenter slot 3 patch did not show
---------------------------------------------------------------
The selected building in-game is not Object Israel_CommandCenter.

In-game slots:
  1  Dozer
  10 Spy Satellite
  13 Rally Point
  14 Sell

That layout is AirF_AmericaCommandCenterCommandSet.

The object is AirF_AmericaCommandCenter in
  Data\INI\Object\Specter\Israel Defense Forces\Buildings\HQ.ini
  CommandSet = AirF_AmericaCommandCenterCommandSet
  DisplayName = OBJECT:CommandCenter
  Model = Isr_Command, portrait isi_hq

FactionIsrael starts with Israel_MilitaryHQ. The Israel dozer slot 8
builds AirF_AmericaCommandCenter (AirF_Command_ConstructAmericaCommandCenter).

Israel_CommandCenterCommandSet has no Dozer and no Spy Satellite, so
edits in CommandSet_SpecterPatch.ini cannot appear on this panel.

ss1 also ships a loose Data\INI\CommandSet.ini. SAGE uses that file
instead of the same path inside _SPEC_DATA_ONE.big. Slot 11 added only
inside the BIG therefore never reached the live AirF set.

This pack puts slot 3 on AirF_AmericaCommandCenterCommandSet in the BIG
CommandSet.ini, and also in unique INI paths that load before and after
CommandSet.ini so the override is not hidden by the loose file.

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

What is inside the patched DATA BIG
-----------------------------------
Updated:
  Data\INI\CommandSet.ini
    AirF_AmericaCommandCenterCommandSet slot 3 added
    slot 11 line left as it was
    slots 1, 10, 13, 14 unchanged
  Data\INI\CommandSet_SpecterPatch.ini
    Israel_CommandCenterCommandSet (not the in-game CC panel)
  Data\English\generals.csf

Added:
  Data\INI\AA_IsraelIronDomeMobile_AirFCC.ini
    same AirF set + slot 3 (loads before CommandSet.ini)
  Data\INI\CommandSet_ZZZZ_ZZZZZZIsraelIronDomeMobile.ini
    same AirF set + slot 3 (loads last among CommandSet files)
  Data\INI\CommandButton_Israel_VehicleIronDomeMobile.ini
  Data\INI\CommandSet_Israel_VehicleIronDomeMobile.ini
  Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Israel_VehicleIronDomeMobile.ini

What is inside the patched ART TWO BIG
--------------------------------------
Unchanged in this pass. Still contains BONDKS.W3D and the purchased TGAs.

Unchanged
---------
Israel_AD_IronDome, Israel_AD_Barak8, Israel_MilitaryHQ, Israel dozer,
Israel_CommandCenter.ini, HQ.ini, CommandButton, Object, ART BIGs.

Buy path
--------
Build AirF_AmericaCommandCenter with the Israel dozer (slot 8).
That building uses AirF_AmericaCommandCenterCommandSet.
Slot 3 = Command_ConstructIsraelVehicleIronDomeMobile
  -> Object Israel_VehicleIronDomeMobile.

In-game test
------------
Not run. These checks are archive and installer-script only.
