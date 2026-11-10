SPECTER USA Patriot PAC-3 (New Donor + THAAD missiles) — test pack
==================================================================

Baseline: ss1 SPECTER FINAL (GitHub commit 84e4b946 / main 116820aa).
This pack does not continue previous PAC-3 v1–v8 work.

Install
-------
1. Extract this ZIP into SPECTER FINAL (the folder with generals.exe).
2. Replace the two BIGs:
     _SPEC_DATA_ONE.big
     _SPEC_ART_TWO.big
3. Do not replace _SPEC_ART_ONE.big. Loose Data\INI is not in this ZIP.

What changed
------------
_SPEC_DATA_ONE.big
  Only Object USAPAC3 (PatchSystems AirDefense INI). New Donor truck,
  DeployStyle pack/unpack, Donor CommandSet. Missiles are ss1 THAAD
  8x_LRSAM_THAAD / THAADMissile_ABM launched from Patriot FIREPOINT bones.
  Object US_THAAD, Weapon.ini, CommandSet.ini, and other countries are unchanged.

_SPEC_ART_TWO.big
  UsaPac3F.W3D and UsaPac3F_d.W3D restored to original New Donor meshes.
  Car / textures already matched Donor in ss1 and were not replaced.

How to use in game
------------------
1. America Command Center slot 6 already builds Object USAPAC3 in ss1.
2. The packed truck appears. Move it (packed / jacked travel mesh).
3. Issue an attack on aircraft or ballistic missiles. DeployStyle unpacks
   (jack animation, then UsaPac3F), then fires THAAD missiles.
4. Move order packs the launcher.

This pack does not write files under Data\.

In-game test
------------
Not run on this machine. Archive/hash/INI/W3D checks only.
