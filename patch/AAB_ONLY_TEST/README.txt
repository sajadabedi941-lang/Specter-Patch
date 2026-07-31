AAB BUILD WIRING ONLY
=====================

Does NOT modify countries or add units.
Does NOT overwrite original Specter Dozer / CommandSet / StrategyCenter files.

Wiring:
1) Stock dozer CommandSets unchanged (AmericaDozerCommandSet slot 2/15 = Strategy Center buttons)
2) CommandButton_AdvancedAirBase_SpecterFactions.ini redefines those stock buttons:
     Object = America_AdvancedAirBase / Nato_AdvancedAirBase / AirF_AmericaAdvancedAirBase
     ButtonImage = us_stratcenter (USA/Nato) or isi_indup (AirF)
3) AdvancedAirBase objects use Strategy Center Prerequisites / BuildCost / BuildTime
   and BuildCompletion = PLACED_BY_PLAYER

Full patch Data and SPECTER_FINAL_PLAYABLE_RELEASE remain untouched.
