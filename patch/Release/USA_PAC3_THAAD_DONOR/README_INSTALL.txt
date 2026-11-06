America Command Center — mobile Patriot rebuild (slot 6)
=======================================================

This pack replaces the broken USAPAC3 implementation inside the
packed DATA BIG with a new independent THAAD clone that keeps the
New Donor Patriot truck / launcher / missile art.

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

What is in this pack
--------------------
_SPEC_DATA_ONE.big
  Removed (USAPAC3-only):
    Data\INI\Object\Specter\PatchSystems\AirDefense\USAPAC3.ini
    Data\INI\Object\Specter\PatchSystems\AirDefense\USAPAC3_Projectile.ini
    Data\INI\Weapon_USAPAC3.ini
    Data\INI\CommandSet_ZZZZ_USAPAC3.ini
  Added:
    Data\INI\Object\Specter\United States Of America\AirDefense\US_PAC3.ini
    Data\INI\Weapon_US_PAC3.ini
    Data\INI\ObjectCreationList_US_PAC3.ini
  Unrelated packed files are byte-identical to ss1, including
  US_M1120.ini (Object US_THAAD), CommandSet.ini, CommandButton.ini,
  Weapon.ini, ObjectCreationList.ini.

_SPEC_ART_TWO.big
  Stripped ANIMATION chunks from:
    Art\W3D\UsaPac3Car.W3D / UsaPac3Car_d.W3D  (BIT_CHANNEL-only clips)
    Art\W3D\pac3mis_m.W3D / UsaPac3Car_w.W3D   (empty 101-frame clips)
  All other ART TWO entries are byte-identical to ss1, including
  US_M1120*.W3D, THAAD_FCS.W3D, and the New Donor meshes/textures.

Crash fix (v2)
--------------
The first pack still crashed: W3DTruckDraw preloaded UsaPac3Car's
BIT_CHANNEL clip (and a second tire Draw without DefaultConditionState)
at object create / PRELOAD. This pack uses W3DModelDraw, no Animation=
lines, no extra Draw, and drops PRELOAD on the TEL objects. THAAD
gameplay (S400R_Deploy / FCS / missiles) is unchanged. Generals.exe
was still not launched here.

This pack does not write files under Data\.

Install
-------
1. Extract this folder into SPECTER FINAL (the folder with generals.exe).
2. Run Install_USA_PAC3_THAAD_DONOR.bat
3. The installer backs up into SpecterBackup_USA_PAC3_THAAD_DONOR
   and verifies each copy with fc /b before any replace.
4. It replaces a file only when SHA-256 is the ss1 original or already
   this pack. Any other hash is left in place and install stops.
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
