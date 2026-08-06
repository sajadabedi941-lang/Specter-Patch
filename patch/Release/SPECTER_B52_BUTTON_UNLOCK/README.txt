SPECTER_B52_BUTTON_UNLOCK
=========================

Problem
-------
B-52 Airfield button stayed disabled because:
1) Command_ConstructAmericaJetB52H pointed at missing Patch_America_B52
2) AmericaJetB52H required Strategy Center + SCIENCE_Rank4

Fix (unlock only)
-----------------
- Rebind B-52 UNIT_BUILD buttons -> AmericaJetB52H
- AmericaJetB52 / AmericaJetB52H: Buildable = Ignore_Prerequisites
- Empty Prerequisites (no Strategy Center / Rank / Science)
- No RequiredScience / Options on buttons

Unchanged
---------
Draw / Model / Scale / Weapon / AI / Locomotor /
Airfield CommandSet slots / Cost / Limit
