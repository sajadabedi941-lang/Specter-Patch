AAB-ONLY TEST — STOCK DOZER RESTORED
====================================

Rolled back AmericaDozerCommandSet_AAB (empty build menu regression).

Playable USA AmericaVehicleDozer now uses original Specter:
  CommandSet = AmericaDozerCommandSet
  (Power, Barracks, War Factory, Strategy Center, etc.)

Removed:
- Dozer.ini overrides (USA/NATO/Israel)
- CommandSet_AdvancedAirBase.ini (AmericaDozerCommandSet_AAB*)

NOT changed:
- AdvancedAirBase object INIs
- Countries / units
- Stock CommandSet.ini / CommandButton.ini

Next step (only after in-game stock menu confirmed):
  Wire AAB onto dozer without replacing the whole CommandSet incorrectly.
