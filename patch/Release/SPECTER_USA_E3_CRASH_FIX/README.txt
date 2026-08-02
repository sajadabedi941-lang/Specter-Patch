SPECTER - USA E3 CRASH FIX (USA ONLY)
=====================================
Fixes Patch_America_E3 init crash in USA heavy runway aircraft INI.

Root cause:
  OCLInitialDeath = OCL_AmericaJetSlowDeathInitial (undefined)

Fix:
  Remap to stock OCL_AmericaJetCargoDeathStart on USA heavies
  (E3, B-1B, B-52, KC-135, C-17, HeavyBomber) and USA drones.

Also removed multi-faction aircraft overlays that overrode USA E3:
  Aircraft_AAB_Global.ini, Aircraft_AirForceFinal.ini,
  Aircraft_AAB_StrategicBombers.ini, non-America PatchSystems drones.

Contains ONLY USA Advanced Air Base + USA aircraft / dozer wiring.
CommandSet.ini untouched. AdvancedAirBase Art/Draw/Geometry untouched.
No factions added.
