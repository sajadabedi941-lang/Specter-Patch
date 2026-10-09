SPECTER: Iraq Al-Abbas 30s production + immediate fire

Object Iraq_AlAbbas (missile factory slot 4 / CB_MISSILE_D)
now has BuildTime 30.0. AutoReloadsClip = No was removed from
Weapon_Iraq_AlAbbas so the missile can load and fire after
production without an extra clip-activation wait.

Place this complete replacement DATA BIG in the SPECTER folder:
  _SPEC_DATA_ONE.big

Keep the existing PR #574/_SPEC_ART_ONE.big (not rebuilt):
  SHA256=e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4

Static validation completed; runtime game test not performed.
