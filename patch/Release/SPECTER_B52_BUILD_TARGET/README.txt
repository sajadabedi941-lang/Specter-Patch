SPECTER_B52_BUILD_TARGET
========================

Minimal runtime patch (loads after B52 visual Draw lock):
  Data\INI\ZZZZZZZZ_ZZZZ_USA_B52_ZZZZ_BUILD_TARGET.ini

Command_ConstructTEODAmericaJetB52
  Object = AmericaJetB52H
  No RequiredScience / Options / SpecialPower

AmericaJetB52H
  Buildable = Ignore_Prerequisites
  Prerequisites empty (clears StrategyCenter / SCIENCE_Rank4)
  KindOf = selectable airfield AIRCRAFT (not ScienceObject)
  BuildCost / BuildTime / MaxSim inherited from USA_System.ini

Not modified: Draw / Model / Weapon / AI / Locomotor / Airfield slots / Cost values
