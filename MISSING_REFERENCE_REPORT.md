# MISSING_REFERENCE_REPORT.md

**Specter Ultimate Warfare Expansion — Missing Reference Scan**  
**Date:** 2026-07-23 02:07 UTC  
**Verdict:** **PASS** (0 open true gaps after auto-fix)

---

## Scan scope

Cross-checked patch INI references against:

- All definitions inside `patch/Data/INI/**`
- Specter stock extracts (`Weapon.ini`, `CommandButton.ini`, `CommandSet.ini`, `SpecialPower.ini`, `ObjectCreationList.ini`, `Locomotor.ini`, `Upgrade.ini`, `WeaponObjects.ini`, USA WeaponObjects)

## Results after auto-fix

| Reference class | Open true gaps |
|-----------------|----------------|
| Weapons | 0 |
| Projectiles / Objects | 0 |
| CommandSets | 0 |
| SpecialPowers | 0 |
| CommandButtons (from CommandSets) | 0 |
| Upgrades | 0 |
| Locomotors | 0 |
| OCLs (real names) | 0 |

## Auto-fixes applied

- Weapon_VerificationFixes.ini — Turkey_DecalCollisionDummyWeapon, 2A18_Turkey_122mm_ClusterShell_BD, 4x_Turkey_Fab-100_CenterRack_Mig23BN
- Upgrade_Turkey_Armor added to Upgrade_Turkey.ini
- Locomotor_VerificationFixes.ini — 6 Turkey locomotor overlays
- CommandSet_AdvancedAirBase.ini — Command_ConstructChinaNuclearMissile → Command_ConstructChinaNuclearMissileLauncher
- CommandSet_AdvancedAWACS.ini / CommandSet_AirForceFinal.ini — Command_FireWeapon → Command_FireMainWeapon
- CommandButton_VerificationFixes.ini — Command_FireWeapon compatibility alias

## Reviewed non-issues (not patch bugs)

| Item | Classification |
|------|----------------|
| `AmericaWarFactory` | **EXTERNAL_SPECTER_OK** — stock Specter/Alliance factory Object |
| `AwacsRadarBeamObject` | **EXTERNAL_SPECTER_OK** — defined in Specter `USA_WeaponObjects.ini` |
| `OCL = FINAL / INITIAL / MIDPOINT` | **FALSE_POSITIVE** — SlowDeathBehavior phase keywords before real OCL name |
| `CommandSet = None` / commented sets | **FALSE_POSITIVE** — parser noise |

## Pre-fix findings (resolved)

| Missing | Resolution |
|---------|------------|
| `Turkey_DecalCollisionDummyWeapon` | Added in `Weapon_VerificationFixes.ini` |
| `2A18_Turkey_122mm_ClusterShell_BD` | Added (Specter 2A18 cluster profile) |
| `4x_Turkey_Fab-100_CenterRack_Mig23BN` | Added (projectile `Turkey_Fab-100`) |
| `Upgrade_Turkey_Armor` | Added to `Upgrade_Turkey.ini` |
| Turkey missile/SF locomotors (6) | Added in `Locomotor_VerificationFixes.ini` |
| `Command_ConstructChinaNuclearMissile` | Renamed ref → `...Launcher` (Specter name) |
| `Command_FireWeapon` | CS switched to `Command_FireMainWeapon` + compatibility alias button |

---

**END MISSING REFERENCE REPORT — PASS**
