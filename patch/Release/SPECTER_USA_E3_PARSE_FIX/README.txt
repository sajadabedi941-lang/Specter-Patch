SPECTER - USA E3 PARSE FIX (USA ONLY)
=====================================
Fixes Object Patch_America_E3 parsing failure in
AAA_USA_HeavyRunway/Aircraft_USA_Heavy_Runway.ini.

Cause:
  Invalid ArmorUpgrade field ArmorSetFlag = PLAYER_UPGRADE
  (not a valid ArmorUpgrade INI key; ArmorSet Conditions=PLAYER_UPGRADE remains)

Also ASCII-cleaned corrupted comment mojibake in the E3 block.

Unchanged:
- E-3 AWACS weapons / special powers / CommandSet Patch_AWACS_CommandSet
- General Star B-2 AAB runway fix
- CommandSet.ini
- AdvancedAirBase Draw/Geometry
- Other factions
