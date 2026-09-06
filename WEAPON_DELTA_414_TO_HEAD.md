# WEAPON DELTA 414 TO HEAD

PR #414 packed DATA was not present as a local BIG in this environment. This delta is reconstructed from packed Weapon.ini section markers and the packers that appended after the last global roster.

Marker: `; ===== SPECTER FINAL GLOBAL AIRFORCE ROSTER WEAPONS BEGIN =====` (L43180)
Marker: `; ===== SPECTER FINAL GLOBAL AIRFORCE ROSTER WEAPONS END =====` (L55675)
Marker: `; SPECTER JP/KR/VN airforce unique weapons. Inlined into Weapon.ini only.` (L55677)

## Introduced after global-roster END (JP/KR/VN second append + later passes)

| Weapon | Approx pass | Notes |
|---|---|---|
| VietnamJetMig29S_WpnRadar | jp-korea-vietnam-airforce-fix | valid A2A |
| VietnamJetMig29S_WpnIR | jp-korea-vietnam-airforce-fix | valid A2A; previous block before crash |
| VietnamJetMig29S_WpnGun | jp-korea-vietnam-airforce-fix | MALFORMED DamageType=GUN - repaired this pass |
| Japan_Weapon_AAM4B_F15JStd | jp-korea-vietnam / init-crash-fix | unique name after earlier dup cleanup |
| IraqJetMig25RB_WpnLT3 | jp-korea-vietnam-airforce-fix | kept |
| IraqJetMig25RB_WpnGun | jp-korea-vietnam-airforce-fix | same GUN template - repaired this pass |
| LibyaJetMig21MF_WpnRkt | jp-korea-vietnam-airforce-fix | kept |
| LibyaJetMig21_WpnBombHvy | jp-korea-vietnam-airforce-fix | kept |
| UkraineJetMig21_WpnBombMed | jp-korea-vietnam-airforce-fix | kept |
| ItalyJetC130J_WpnHeavy | jp-korea-vietnam-airforce-fix | kept |
| GermanyJetTornadoIDS_WpnBombHvy | airforce-repair-pass-3 | kept; not parser-broken |
| GermanyJetTornadoIDS_WpnIR2 | airforce-repair-pass-3 | kept; not parser-broken |

Vietnam guns in the *first* roster cluster (VietnamJetMig21_WpnGun, VietnamJetSu27_WpnGun, ...) already use COMANCHE_VULCAN + 30mm_API-T_Projectile and are not the crash.

DO NOT revert post-414 weapons. This pass only rewrote the two GUN cannons.
