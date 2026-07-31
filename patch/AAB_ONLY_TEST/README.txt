AAB COMMAND VISIBILITY FIX
==========================

Root cause: SAGE keeps the FIRST CommandButton definition. Redefining
Command_ConstructAmericaStrategyCenter_T in a patch INI never wins over
Data/INI/CommandButton.ini — Strategy Center slot kept stock SC object.

Fix (visibility only; AdvancedAirBase object untouched):
1. Playable USA Dozer -> AmericaDozerCommandSet_AAB (new CommandSet name)
2. Slot 2/15 = Command_ConstructAmerica_AdvancedAirBase (unique button)
3. ButtonImage = us_stratcenter
4. Stock AmericaDozerCommandSet / CommandButton.ini left as-is (not overridden)

DEBUG: Command_AAB_VisibilityTest_Barracks + AmericaDozerCommandSet_AAB_DEBUG_BARRACKS
exist for swap tests (Barracks icon at SC slot). Final ship uses AAB mapping.
