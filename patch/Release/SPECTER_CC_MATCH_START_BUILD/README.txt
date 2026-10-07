SPECTER Command Center start=construct match
Countries: India, Pakistan, Saudi Arabia, UAE, Libya, Syria, South Africa

Place this complete replacement DATA BIG in the SPECTER folder:
  _SPEC_DATA_ONE.big

Keep the existing PR #574 ART BIG (do not replace ART):
  _SPEC_ART_ONE.big
  SHA256=e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4

Fix:
- Starting Command Center and later-constructed Command Center now use
  the same country-specific *_CommandCenter object (model, flag,
  CommandSet, health, armor, geometry).
- Dozer/Worker construct slot 2 no longer builds *_MilitaryHQ.
- Pakistan construct-CommandCenter button added to CommandButton.ini.
- PR #583 missile spawn-fix data preserved. ART not rebuilt.

Static validation completed; runtime game test not performed.
