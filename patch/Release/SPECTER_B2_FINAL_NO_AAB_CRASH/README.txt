SPECTER_B2_FINAL_NO_AAB_CRASH

Final USA Airfield B-2 release + AdvancedAirBase parse crash fix.

Includes:
- AmericaJetB2 final object
- AVB3bmbr draw/model (WeaponA01, Scale 0.55)
- Slot 5 production: Command_ConstructTEODAmericaJetB2 -> AmericaJetB2
- No Science / Upgrade / RequiredScience locks on B-2 button
- AAB parse fix: Aircraft_AAB_Global.ini stubbed
- Patch_America_B3 removed
- HeavyRunway AAB aircraft stubs
- Stock AmericaAirfield CommandSet path preserved (slot 5 B-2)
- Airfield object/model/dozer unchanged

Path:
  AmericaAirfieldCommandSet slot 5
    -> Command_ConstructTEODAmericaJetB2
      -> AmericaJetB2 (AVB3bmbr)
