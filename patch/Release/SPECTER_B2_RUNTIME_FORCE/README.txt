SPECTER_B2_RUNTIME_FORCE

Runtime path traced and force-replaced:

  AmericaDozerCommandSet slot 13
    -> Command_ConstructAmericaAirfield_T
      -> Object AmericaAirfield_T
        -> CommandSet AmericaAirfieldCommandSet_T
        -> CommandSetUpgrade -> _T1 / _T2 / _T3

Every USA Airfield CommandSet slot 5 =
  Command_ConstructTEODAmericaJetB2 -> AmericaJetB2

Also:
- Airfield / Airfield_T CommandSet rebound in absolute last-wins INI
- AmericaJetB2 Buildable = Ignore_Prerequisites
- Legacy Spirit / Patch_America_B2 buttons redirected to AmericaJetB2
- AAB StrategyCenter redirect stubbed

Untouched: AVB3bmbr, weapon, AI, locomotor
