Iron Dome Mobile — live CommandSet.ini slot 3
=============================================

ControlBar reads only Data\INI\CommandSet.ini. Launch_Specter.bat copies
CommandSet.ini from next to the launcher onto that path on every start.
Edits inside _SPEC_DATA_ONE.big never reach this panel.

This pack changes only that live CommandSet.ini.

Install
-------
Extract into SPECTER FINAL (generals.exe / Launch_Specter.bat).
Run Install_Israel_IronDomeMobile_CommandSet.bat

It backs up, then writes the patched file to:
  <game>\CommandSet.ini          (launcher source, if that file already exists)
  <game>\Data\INI\CommandSet.ini (ControlBar dest, if that file already exists)

It does not create a new CommandSet sidecar. It does not change BIGs,
Object, CommandButton, models, or textures.

Backup
------
  <game>\SpecterBackup_IronDomeMobile_CommandSet\launcher_CommandSet.ini
  <game>\SpecterBackup_IronDomeMobile_CommandSet\Data_INI_CommandSet.ini
Pack original (ss1):
  backup_original\CommandSet.ini

Restore
-------
Run Restore_Israel_IronDomeMobile_CommandSet.bat

Change
------
AirF_AmericaCommandCenterCommandSet only:
  3  = Command_ConstructIsraelVehicleIronDomeMobile

Unchanged: slots 1, 2, 4-10, 13-15. Slot 11 was not present in ss1 and
was not added. Dozer, Spy Satellite, Rally, Sell stay as they are.

ss1 SHA-256:
  f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223
Patched SHA-256:
  0a826f14e6d5253a9edd81ce3500a834edfc36cda37d1249d2d72011a742f3f8

The unit Object and CommandButton still come from the earlier DATA BIG
pack. This pack does not redefine them.

In-game test
------------
Not run here. There is no live SPECTER FINAL install in this environment.
The installer simulates the launcher copy locally. That is not a game install.
