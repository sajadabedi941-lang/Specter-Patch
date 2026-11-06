Iraq Command Center — Iron Dome Mobile (slot 3)
================================================

This pack adds the existing buy button

  Command_ConstructIsraelVehicleIronDomeMobile
    Command = UNIT_BUILD
    Object  = Israel_VehicleIronDomeMobile

to the Command Center Iraq actually uses. It does not change any
Israel Command Center CommandSet.

Iraq building that is used in-game
----------------------------------
PlayerTemplate FactionIraq
  StartingBuilding = Iraq_CommandCenter
  StartingUnit0    = Iraq_VT72B

Object Iraq_CommandCenter
  File: Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_CommandCenter.ini
        (inside _SPEC_DATA_ONE.big; unique definition)
  Side = Iraq
  DisplayName = OBJECT:CommandCenter
  Model = Irq_Command
  CommandSet = Iraq_CommandCenterCommandSet

Winning CommandSet
------------------
ControlBar reads only the loose file Data\INI\CommandSet.ini
(Launch_Specter.bat copies the game-root CommandSet.ini onto that path
every start). There is exactly one

  CommandSet Iraq_CommandCenterCommandSet

in ss1 CommandSet.ini. No CommandSet_ZZZZ / AA_ overlay redefines it.

ss1 slots:
  1  Command_ConstructIraq_VT72B
  12 Command_ConstructIraqDronesAbabil200Recon
  13 Command_SetRallyPoint
  14 Command_Sell
  15 Command_ConstructIraq_Sarab7
  16 Command_ConstructIraq_R11ScudB
  17 Command_ConstructIraq_Sarab3
  17 Command_ConstructIraqDroneQuds5_AI   (duplicate 17 left untouched)
Empty: 2, 3, 4-11, 18

This pack writes only:
  3 = Command_ConstructIsraelVehicleIronDomeMobile

AirF_AmericaCommandCenterCommandSet, AmericaCommandCenterCommandSet,
and Israel_CommandCenterCommandSet are unchanged. Static Iron Dome
and Barak8 objects are unchanged. BONDKS.W3D and its textures are
the existing files.

Side = Israel
-------------
The existing object keeps Side = Israel. SAGE UNIT_BUILD / canBuild
does not compare Object Side to the purchasing player's Side. The
object has no Prerequisites block. Side was not changed.

Install
-------
1. Extract this folder into SPECTER FINAL (the folder with generals.exe).
2. Run Install_Iraq_IronDomeMobile_CC.bat
3. The installer backs up into SpecterBackup_IraqIronDomeMobile_CC
   and verifies each copy with fc /b before any replace.
4. It replaces a file only when SHA-256 is the ss1 original or already
   this pack. Any other hash is left in place and install stops.
5. Live CommandSet.ini is patched in place. It is not deleted.
6. No new loose Object / CommandButton / CSF / art files are written.

Restore
-------
Run Restore_Iraq_IronDomeMobile_CC.bat.
It copies this pack's backup back and checks fc /b.
It does not delete CommandSet.ini, CSF, or unknown files.

In-game test
------------
Not run. Checks in this pack are archive, hash, and installer-script only.
