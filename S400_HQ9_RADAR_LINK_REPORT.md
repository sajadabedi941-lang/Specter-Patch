# 92N6E / HT-233 radar-to-battery link fix

Reference: SPE.part001.rar–SPE.part058.rar, git `aac7ffc1e9e2a8541e2abc3d185e97a24c66cb61`.  
Source BIG for this rebuild is the GM AD ABM-fix `_SPEC_DATA_ONE.big` (`d205c953…`).  
Only `_SPEC_DATA_ONE.big` was rebuilt. SPE volumes, Arrow, S-300, S-500, IRIS-T, THAAD, Patriot, Pantsir-S1M, Krasukha-4, incoming-missile stats, and interceptor weapons were not changed.

**In-game test was not performed.** Generals Zero Hour is not available in this environment. Results below are BIG/INI last-win validation only.

## Engine constraint

SAGE does not share `VisionRange` from an independent radar to another unit. `RadarTrackingBeam` is `DamageType = STATUS` / `FAERIE_FIRE` and is not an intercept weapon. A deployed S-400 / HQ-9 battery fires from its own FCS object, gated by `AirdefenseLinkRestarter` (STATUS `NO_ATTACK` on colocated FCS). The designed radar cue is `SURRENDER` / `DeathType = EXTRA_6` against `PowerCircleArmor` (`SURRENDER = 9999%`), which kills the restarter so the FCS can attack. Without an active radar pulse, the restarter stays up and the battery must not engage.

## BIG hashes

| File | Size | SHA-256 |
|---|---|---|
| SPE original `_SPEC_DATA_ONE.big` | 373,898,957 | `169d07b3365817abdf9c2140644a2bf4ac68a4e367a57b48dbc1b347fbeb1ae8` |
| GM AD ABM-fix `_SPEC_DATA_ONE.big` | 373,902,745 | `d205c9539330110fa86559c296b8d282464009ef7ff22fafc02d9305182c7c0e` |
| This rebuild `_SPEC_DATA_ONE.big` | 373,914,308 | `7a0b9370d837501c458b77345c0e3faef4ba9b8cd731ad3c54a1edc829909cc5` |

Inner entries: 3552 → 3556. Header still BIGF; size field matches file length.

New last-win extras (alpha after stock `Weapon.ini` / `CommandButton.ini` / `ObjectCreationList.ini` / `ObjectCreationList_ZZZZ_ZZGmAdAbm.ini`):

- `Data\INI\Weapon_ZZZZ_ZZZ92N6Ht233.ini`
- `Data\INI\CommandButton_ZZZZ_ZZZ92N6E.ini`
- `Data\INI\ObjectCreationList_ZZZZ_ZZZ92N6Ht233.ini`
- `Data\INI\Object\zzzz_Specter92N6Ht233\Russia_92N6R.ini`

In-place only: `92N6R.ini` CombatMode DataLink, `HT233.ini` CombatMode DataLink.  
Unchanged: `Weapon.ini`, `S400.ini`, `HQ9B.ini`, Patriot `10x_PAC3_MSE_ABM` CRUSH.

## 92N6E (S-400 radar)

### Effective chain (packaged BIG, last-win)

- Button `Command_ConstructRussian_92N6E` previously `Object = Russia_92N6R` — **no `Object Russia_92N6R`**.
- Working packed unit is `RussiaVehicle92N6R` (GM copy `Iraq_MIC_92N6R`) → suicide `92N6R_Deploy` → `OCL_92N6R_Deployed` → `Russia_92N6R_CombatMode`.
- CombatMode already had `RadarTrackingBeam`, WaveEmitter, and stock `FireControlRadarDataLink`.
- `Weapon 92N6E_Deploy` referenced **missing** `OCL_92N6E_Deployed`.
- S-400 AA/ABM OCLs already spawn FCS + `AirdefenseLinkRestarter` (unchanged).

### Root cause

1. The 92N6E factory button built a missing object, so that control never produced a radar.
2. Even the working `RussiaVehicle92N6R` / `Iraq_MIC_92N6R` CombatMode fired stock `FireControlRadarDataLink` **without** `DamageDealtAtSelfPosition`. `FireWeaponUpdate` therefore does not pulse SURRENDER/EXTRA_6 at the radar, `AirdefenseLinkRestarter` on the S-400 FCS survives, and the battery stays `NO_ATTACK`. STATUS beam paint is not a cue.

### Fix

- Last-win `Command_ConstructRussian_92N6E` / `_AI` → `RussiaVehicle92N6R`.
- Alias `Object Russia_92N6R` (clone of the packed vehicle) for leftover references.
- Last-win `OCL_92N6E_Deployed` → `Russia_92N6R_CombatMode`.
- CombatMode DataLink → `92N6R_FireControlDataLink` (`SURRENDER`/`EXTRA_6`/`ALLIES`, `DamageDealtAtSelfPosition = Yes`, radius 1800 matching `92N6R_Radar_Power`). Radar is not a launcher.

### Validation (static)

Last-win button Object = `RussiaVehicle92N6R`; alias object present; CombatMode weapon = `92N6R_FireControlDataLink`; `OCL_92N6E_Deployed` present; S-400 interceptor `3x_LRSAM_40N6KMissile_ABM` still CRUSH; `S400.ini` byte-identical to the ABM-fix BIG.

## HT-233 (HQ-9 radar)

### Effective chain (packaged BIG, last-win)

- `Command_ConstructChinaVehicleHT233` / `Iraq_MIC_HT233` → existing objects → `OCL_HT233_Deployed` → `ChinaVehicleHT233_CombatMode`.
- CombatMode already had tracking beam + stock DataLink from the ABM-fix identification pass.
- `OCL_HQ9_Deployed` (AA) spawned **only** `ChinaVehicleHQ9_CombatMode` — no `HQ9_FireControlSystem`, no restarter. ABM OCL already had FCS + restarter (unchanged).

### Root cause

1. Same broken DataLink pulse as 92N6E: stock `FireControlRadarDataLink` never hits `AirdefenseLinkRestarter` on HQ-9 ABM FCS, so HT-233 deploy does not lift `NO_ATTACK`.
2. Default HQ-9 AA deploy had no FCS at all, so there was no shooter for HT-233 to cue. Independent radar vision cannot be handed to the launcher.

### Fix

- CombatMode DataLink → `HT233_FireControlDataLink` (same SURRENDER/EXTRA_6 self-pulse, radius 1600 matching `HT233_Radar_Power`).
- Last-win `OCL_HQ9_Deployed` spawns CombatMode + existing `HQ9_FireControlSystem` (AA, `AntiBallisticMissile = No`) + `AirdefenseLinkRestarter`, parallel to S-400 AA. Without HT-233 the restarter keeps AA FCS off; HT-233 does not become a launcher. ABM FCS/weapons untouched.

### Validation (static)

CombatMode weapon = `HT233_FireControlDataLink`; `OCL_HQ9_Deployed` last-win includes FCS + restarter; `OCL_HQ9_Deployed_ABM` unchanged; `Hq9_AA_Missile_ABM` still CRUSH; `HQ9B.ini` and `Weapon.ini` byte-identical to the ABM-fix BIG.

## How to use

Replace the game `_SPEC_DATA_ONE.big` with SHA-256 `7a0b9370d837501c458b77345c0e3faef4ba9b8cd731ad3c54a1edc829909cc5`. Keep `0_SPECTER_ABMDedicatedRadar.big`. Deploy 92N6E/92N6R with the S-400 battery, and HT-233 with the HQ-9 battery, inside the radar pulse radius. Packing or losing the radar must leave the restarter up (no BM intercept).

Rebuild:

```
python3 patch/tools/big/patch_spec_data_one_92n6e_ht233_radar.py \
  --src-big patch/Release/GM_AD_ABM_FIX/_SPEC_DATA_ONE.big \
  --out-big _SPEC_DATA_ONE.big
```
