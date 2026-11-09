America Command Center — PAC-3 (New Donor deploy + THAAD combat)
================================================================

Buy button (unchanged, not rewritten by this installer)
-------------------------------------------------------
CommandButton Command_ConstructUSAPAC3
  Command = UNIT_BUILD
  Object  = USAPAC3

CommandSet AmericaCommandCenterCommandSet
  6 = Command_ConstructUSAPAC3

ControlBar still reads the existing loose file Data\INI\CommandSet.ini
(Launch_Specter.bat copies the game-root CommandSet.ini onto that path
every start). This pack does not edit, replace, or delete that file.
Slot 6 already builds Object USAPAC3. The packed object definition
behind that name is what changed.

v8 Deploy unlock
----------------
v7 still greys Deploy after AA/ABM. ControlBar FIRE_WEAPON does not
check turret state. It greys the button when the slot weapon is
missing. TheWeaponStore loads only Data\INI\Weapon.ini; the sidecar
Data\INI\Weapon_US_PAC3.ini is never opened, so US_PAC3_DeployCue
was NULL. v8 puts those Weapon templates at the top of the packed
Object file (Data\INI\Object\...\US_PAC3.ini), which ThingFactory
does load. Cue ClipReloadTime is omitted (ZH default 0), matching
S400R_Deploy. ControlledWeaponSlots stays PRIMARY so the packed
cue is a body shot, not turret-gated. Combat PRIMARY is unchanged.

v7 turret change (did not unlock the button)
--------------------------------------------
v7 set ControlledWeaponSlots = PRIMARY only. That is kept for the
packed cue shot. It was not the ControlBar grey-out.

v6 construct unlock
-------------------
v5 greyed the PAC-3 button because Object USAPAC3 required
AmericaStrategyCenter. Other Command Center units (Dozer, M2A3) do
not. v6 clears that Prerequisites block only. Deploy/pack, THAAD
weapons, and ART are unchanged.

What is in this pack (v5 architecture + v6 unlock)
--------------------------------------------------
_SPEC_DATA_ONE.big
  Object USAPAC3 is a single New Donor truck (DeployStyle unpack/pack,
  UsaPac3Car jack clip, UsaPac3F deployed mesh). THAAD intercept
  weapons sit on PRIMARY. Deploy buttons fire a 0-damage cue, not
  S400R_Deploy. CombatMode / PackMode / FCS objects and
  ObjectCreationList_US_PAC3.ini are removed.
  US_M1120.ini (Object US_THAAD) is unchanged.

_SPEC_ART_TWO.big
  Restored original New Donor W3Ds:
    UsaPac3Car.W3D / UsaPac3Car_d.W3D  (jack Z clip USAPAC3CAR)
    UsaPac3Car_w.W3D / UsaPac3F.W3D / UsaPac3F_d.W3D
  pac3mis_m.W3D left as the v2-stripped projectile (empty clip header
  removed). Other ART TWO entries are byte-identical to ss1.

How to use in game (intended cycle)
-----------------------------------
1. Build PAC-3 from America CC slot 6. The truck appears packed.
2. Choose AA, ABM, or MTS.
3. Click Deploy. The New Donor jack clip plays, then the model swaps
   to the deployed F mesh.
4. After deploy, AutoAcquire uses the THAAD-cloned weapons.
5. Missiles use the PAC-3 model (pac3mis_m) and THAAD numbers.
6. Pack is a move order (native DeployStyle). The shared Pack button
   is FIRE_WEAPON and cannot pack a DeployStyle unit.

This pack does not write files under Data\.

Install
-------
1. Extract this folder into SPECTER FINAL (the folder with generals.exe).
2. Run Install_USA_PAC3_THAAD_DONOR.bat
3. The installer backs up into SpecterBackup_USA_PAC3_THAAD_DONOR
   and verifies each copy with fc /b before any replace.
4. It replaces a file only when SHA-256 is ss1, v1–v4 of this pack,
   or this pack. Any other hash is left in place and install stops.
5. Loose Data\INI is not touched.

Restore
-------
Run Restore_USA_PAC3_THAAD_DONOR.bat.
It copies this pack's backup back and checks fc /b.
It does not delete CommandSet.ini, CSF, or unknown files.

In-game test
------------
Not run. Checks in this pack are archive, hash, INI/W3D parse, and
installer-script only. This is not an in-game pass.
