SPECTER ULTIMATE EXPANSION - Britain CombatDrone INI FIX
=======================================================

Crash fixed:
  Error parsing INI file:
  Data\INI\Object\specter\british armed forces\drones\britain_combatdrone.ini

What changed:
  - Removed broken Britain_CombatDrone.ini (UTF-8 junk + non-donor structure)
  - Rebuilt from healthy USA MQ-9 donor (AmericaDronesMq9 / France_CombatDrone pattern)
  - Kept Britain identity: Object Britain_CombatDrone, Side=Britain
  - Kept Britain weapon balance: Britain_Weapon_ATGM + 2x_GBU12II_Mq9
  - Kept Britain cost/time: 1147 / 11.1s and MQ-9 models (US_MQ9*)
  - Prerequisites: Britain_AdvancedAirBase + SCIENCE_Rank3
  - CommandSet: GenericTacticalBomberCommandSet
  - Validated weapons, projectile, W3D, CommandButton/CommandSet refs
  - INI parse-safety tested before publish

INSTALL
-------
1. Close Specter / Generals Zero Hour
2. Backup existing _SPEC_DATA_ONE.big / _SPEC_ART_ONE.big
3. Copy the two BIG files from this ZIP into your game folder
4. Launch normally or via Launch_Specter.bat

CHECKSUMS
---------
_SPEC_DATA_ONE.big SHA256: 2250ec1f0f0ae23c3e46fca7b3e1c906d5eb74dd175488fde35292ee980b4d63
_SPEC_ART_ONE.big  SHA256: bf7ca6982fe38c51260be7b0a2ba25eef17c7c50ce2e9b20119001fcac8b0a73
