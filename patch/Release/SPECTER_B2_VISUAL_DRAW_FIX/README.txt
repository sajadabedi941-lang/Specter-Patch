SPECTER_B2_VISUAL_DRAW_FIX

Minimal visual-only patch for AmericaJetB2.

Keeps:
  Object = AmericaJetB2
  Model = AVB3bmbr / _D / _D1
  Scale = 0.55

Removes leftover B-1R attach sources in Draw:
  HideSubObject = BurnerFX01 BurnerFX02 BurnerFX03 BurnerFX04
  ShowSubObject = None
  No US_B1R Model / Animation / dependency draws

Does NOT change:
  Airfield, CommandSet, Production, Weapon, AI, locomotor, build gates
