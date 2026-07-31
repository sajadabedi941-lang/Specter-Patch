AAB-ONLY BOOT TEST PACKAGE
==========================

Purpose: Verify Zero Hour boots with ONLY the Advanced Air Base modification
on original Specter factions. Strategy Center dozer slots are replaced by AAB.

NOT modified by this test:
- patch/Data (full working patch) — left intact
- patch/Release/SPECTER_FINAL_PLAYABLE_RELEASE — full playable backup intact

This folder is the ONLY patch-root merged into original _SPEC_DATA_ONE.big
for the AAB boot-test BIG.

Included:
- AdvancedAirBase_AllFactions.ini (America/Russia/China/Iran/Iraq/Nato/GLA)
- AdvancedAirBase_FutureFactions.ini (AirF/Israel/NK — original Specter sides)
- Dozer overrides for USA/RF/PLA/Iran/NATO/Israel (SC slot -> AAB)
- StrategyCenter overrides (sell-only CommandSets)
- CommandSet_AdvancedAirBase.ini / construct CommandButtons / strings / art

Excluded (intentionally):
- Added countries (Turkey, France, Germany, …)
- Aircraft_AAB_Global.ini / Aircraft_AAB_StrategicBombers.ini (new units)
- CommandButton_AdvancedAirBase_Aircraft.ini
- MilitaryHQ / drones / AirForceExpansion / AWACS / economy / donor rebuilds
- PlayerTemplate_SpecterPatch.ini

AAB production uses existing Specter airfield CommandSets (no new objects).
