SPECTER Iraq B/C/D/H/I/J spawn-crash fix (PR #574 baseline)

Place this complete replacement DATA BIG in the SPECTER folder:
  _SPEC_DATA_ONE.big

Keep the existing PR #574 ART BIG (do not replace ART):
  _SPEC_ART_ONE.big
  SHA256=e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4

Fixes:
- B/C/D/H/I/J no longer reference unloaded rebuild Upgrades at spawn
- B/C/D/H/I/J weapons now live in engine-loaded Weapon.ini
- PR #574 missile stats and projectile artwork preserved
- Al-Fahd500 / A unchanged
- Does NOT include PR #575+ locomotor/alias experiments

Static validation completed; runtime game test not performed.
