AAB-ONLY TEST — USA Strategy Center -> AdvancedAirBase
======================================================

Constraints:
- Stock CommandSet.ini NOT modified
- Stock Dozer.ini NOT modified
- All original AmericaDozerCommandSet slots unchanged
- USA only (no NATO/Israel/other faction button retargets)
- Countries / units NOT touched
- AdvancedAirBase object NOT edited

Wiring (separate override only):
  Data/INI/CommandButton_AdvancedAirBase_SpecterFactions.ini
    Command_ConstructAmericaStrategyCenter_T -> Object = America_AdvancedAirBase
    Command_ConstructAmericaStrategyCenter   -> Object = America_AdvancedAirBase

Playable USA dozer still uses:
  CommandSet = AmericaDozerCommandSet
  (Power, Barracks, War Factory, Airfield, Strategy Center slots, ...)

Strategy Center slots still appear as stock SC UI; placing them builds America_AdvancedAirBase.
