# Global Market ABM intercept fix

Reference: SPE.part001.rar–SPE.part058.rar, git `aac7ffc1e9e2a8541e2abc3d185e97a24c66cb61`.  
Only `_SPEC_DATA_ONE.big` was rebuilt. SPE volumes, Pantsir-S1M, Krasukha-4, incoming-missile stats, AA interceptors, and Patriot were not changed.

**In-game test was not performed.** Generals Zero Hour is not available in this environment. Results below are BIG/INI validation only.

## BIG hashes

| File | Size | SHA-256 |
|---|---|---|
| SPE original `_SPEC_DATA_ONE.big` | 373,898,957 | `169d07b3365817abdf9c2140644a2bf4ac68a4e367a57b48dbc1b347fbeb1ae8` |
| Patched `_SPEC_DATA_ONE.big` | 373,902,745 | `d205c9539330110fa86559c296b8d282464009ef7ff22fafc02d9305182c7c0e` |

Inner entries: 3551 → 3552. Header still BIGF; size field matches file length.  
New last-win file: `Data\INI\ObjectCreationList_ZZZZ_ZZGmAdAbm.ini` (sorts after `ObjectCreationList.ini` and `ObjectCreationList_SpecterABMDedicatedRadar.ini`).

## Patriot (unchanged)

`America_MIM104F` → `America_MIM104F_ABM_Launcher` → `10x_PAC3_MSE_ABM` (`AntiBallisticMissile = Yes`, `DamageType = CRUSH`, `CAN_ATTACK`, `AutoAcquireEnemiesWhenIdle = Yes`, VisionRange 1600). Reconfirmed after the rebuild.

## What changed and why

Root cause for launchers: `SRBMArmor` has `FALLING = 0%` / `CRUSH = 100%`. Engine `estimateWeaponDamage == 0` → `INVALID_SHOT`. `AntiBallisticMissile = Yes` is not enough.

Root cause for three radars: CombatMode `VisionRange` 100–200 and no `RadarTrackingBeam`, so they cannot acquire `PROJECTILE BALLISTIC_MISSILE` the way 92N6R / TPY-2 already do. They were not turned into launchers. `RadarTrackingBeam` remains `DamageType = STATUS`.

## Before / after (12 systems)

| System | Before (effective SPE) | After (`_SPEC_DATA_ONE.big`) | Why |
|---|---|---|---|
| 1 Arrow | Overlay ABM FCS already `Hq9_AA_Missile_ABM` CRUSH; SPEC `THAADMissile_ABM` was FALLING. SPEC `OCL_Arrow_Deployed_ABM` did not spawn AUM | Weapon `THAADMissile_ABM` → CRUSH. Last-win OCL spawns `THAAD_FireControlSystem_ABM` + AUM | Overlay CRUSH path kept; SPEC last-win OCL makes ABM FCS spawn reliable |
| 2 Israel AN/TPY-2 | Radar. CombatMode already `RadarTrackingBeam` + Vision 900 | Unchanged | Identification already valid; not a launcher |
| 3 92N6R | Radar. CombatMode already tracking beam + Vision 800/900 | Unchanged | Same |
| 4 S-400 | `3x_LRSAM_40N6KMissile_ABM` FALLING (INVALID_SHOT). AUM `4x_MRSAM_9M96E2` CRUSH but VisionRange 900 vs AttackRange 1550 | 40N6K ABM → CRUSH. AUM VisionRange 1600. AA `4x_LRAAM_48N6` still PENALTY / AntiBM No | Named ABM weapon can now start and damage SRBM. AUM can acquire out to Patriot-like vision |
| 5 96L6-TSP | Radar. CombatMode Vision 200, no PRIMARY, AutoAcquire on empty slot | PRIMARY `RadarTrackingBeam`, VisionRange 900 | Identification only |
| 6 S-500 | Overlay ABM FCS already CRUSH. SPEC `OCL_S500_Deployed_ABM` spawned AA `S500_FireControlSystem`. SPEC `77H6Missile_ABM` FALLING | `77H6Missile_ABM` → CRUSH. Last-win OCL spawns `S500_FireControlSystem_ABM` + AUM, not AA FCS | ABM deploy cannot fall back to AA FCS |
| 7 HQ-9 | AA OCL has no FCS (left as-is). ABM FCS already `Hq9_AA_Missile_ABM` + `4x_MRSAM_9M83ME_ACM` CRUSH | Unchanged | ABM path already valid |
| 8 HT-233 | Radar. Vision 100, pack-only weapon, empty AIUpdate | Tracking beam, Vision 900, AutoAcquire Yes | Identification only |
| 9 TRML-4D | Radar. Vision 100, pack-only weapon, empty AIUpdate | Tracking beam, Vision 900, AutoAcquire Yes | Identification only |
| 10 IRIS-T | `IRIST_FireControlSystem_ABM` / `THAADMissile_ABM` FALLING; no AUM; Vision 1500 vs weapon 1700 | `THAADMissile_ABM` → CRUSH. FCS VisionRange 1800. AA IRIS-T still PENALTY / AntiBM No | Minimal valid ABM intercept path using existing projectile `THAAD_ABM_OBJECT` |
| 11 USA AN/TPY-2 | Radar. Tracking beam + Vision 900 | Unchanged | Identification already valid |
| 12 THAAD | Same as Arrow | Same weapon + last-win OCL as Arrow | Same |

AA interceptors were not given `AntiBallisticMissile`. Incoming SRBM armor, health, cost, reload, and country rosters were not edited.

## Last-win

`ObjectCreationList_ZZZZ_ZZGmAdAbm.ini` inside `_SPEC_DATA_ONE.big` last-wins `OCL_S500_Deployed_ABM`, `OCL_THAAD_Deployed_ABM`, and `OCL_Arrow_Deployed_ABM` after the `0_SPECTER_ABMDedicatedRadar` extra OCL file. No new overlay BIG was added. No loose Data/ files are required to play.

## How to use

Replace the game `_SPEC_DATA_ONE.big` with the patched BIG of SHA-256 `d205c9539330110fa86559c296b8d282464009ef7ff22fafc02d9305182c7c0e`. Keep `0_SPECTER_ABMDedicatedRadar.big`. Deploy launchers in ABM mode before expecting intercepts; radars only paint/detect.

Rebuild from SPE original:

```
python3 patch/tools/big/patch_spec_data_one_gm_ad_abm.py \
  --src-big /path/to/SPE/_SPEC_DATA_ONE.big \
  --out-big _SPEC_DATA_ONE.big
```

## In-game confirmation still required

For each launcher: packed (no shot), AA deploy (no BM intercept), ABM deploy vs an SRBMArmor missile inside min/max range (detect, attack start, interceptor spawn, kill).  
For each radar: deploy only; STATUS paint / vision; no interceptor.
