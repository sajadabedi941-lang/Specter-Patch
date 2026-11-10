# Iraq radar: remove Spy Satellite, fix map on place

Reference: SPE.part001.rar–SPE.part058.rar, git `aac7ffc1e9e2a8541e2abc3d185e97a24c66cb61`.  
Source BIG: 92N6E/HT-233 radar-link `_SPEC_DATA_ONE.big` (`7a0b9370…`).  
Only `_SPEC_DATA_ONE.big` was rebuilt. SPE volumes, S-400/HQ-9 DataLinks and OCLs, Patriot, Arrow, S-300, S-500, IRIS-T, THAAD, Pantsir-S1M, Krasukha-4, incoming-missile stats, and other countries’ radar CommandSets were not changed.

**In-game test was not performed.** Generals Zero Hour is not available in this environment. Results below are BIG/INI last-win validation only.

## Expected map behavior

This project’s Iraq radar is a ZH **RadarUpgrade** building (minimap / player radar + local Fog of War), not a dedicated full-screen map overlay. Spy Satellite is a separate click-to-reveal ping (`SpySatellitePing` + `EXGrid`). The broken “map” on place was a second structure (`IraqRadarP30` with `RebuildHoleExposeDie`) spawned on the station footprint, not a missing `VisionRange`.

## BIG hashes

| File | Size | SHA-256 |
|---|---|---|
| Prior radar-link `_SPEC_DATA_ONE.big` | 373,914,308 | `7a0b9370d837501c458b77345c0e3faef4ba9b8cd731ad3c54a1edc829909cc5` |
| This rebuild `_SPEC_DATA_ONE.big` | 373,920,910 | `43854413bf3cf8a1a942b2b271328dd33ff44a5d5962e5a451ccf73fa720ab8d` |

Inner entries: 3556 → 3558. Header still BIGF; size field matches file length. No in-place inner files were rewritten.

New last-win extras:

- `Data\INI\CommandSet_ZZZZ_ZZZIraqRadar.ini` (after `CommandSet_ZZZZ_SpySatelliteRadar.ini`)
- `Data\INI\Object\zzzzz_SpecterIraqRadar\Iraq_RadarStation.ini` (after overlay `Object\zzzz_SPECTER_CountryScans.ini`)

## 1. Spy Satellite source (Iraq radar only)

Effective activation path:

1. `CommandSet_ZZZZ_SpySatelliteRadar.ini` last-won `Iraq_RadarStationCommandSet` with `Command_SpySatelliteScan` and `Command_SpecterSpySatelliteFee`.
2. SPEC copies of `Object Iraq_RadarStation` (Iraq Army / Japan / SK / Vietnam) carry `OCLSpecialPower ModuleTag_SSC` → `SpecialPowerSpySatellite` → `SUPERWEAPON_SpySatellite` (`SpySatellitePing` + `SpecterSpySatelliteFeeStrip`).
3. `SpecialPowerSpySatellite` and `SpecialPowerIraqiRadarSearch` share `Enum = SPECIAL_SPY_SATELLITE`, so the Spy Satellite button can fire that enum on this building.
4. `Command_SpySatelliteScan` / `SUPERWEAPON_SpySatellite` themselves were left in place for Command Centers and other countries’ radars (North Korea / Iran CommandSets still have the Spy Satellite buttons).

**Fix:** last-win `Iraq_RadarStationCommandSet` restores `Command_IraqiRadarSearch` and drops Spy Satellite / fee buttons. Last-win `Object Iraq_RadarStation` has no `ModuleTag_SSC`.

## 2. Map corruption root cause

Effective `Object Iraq_RadarStation` (SPEC copies and overlay `zzzz_SPECTER_CountryScans.ini`) ran:

`FireWeaponUpdate` → weapon `P30_Radar_Deploy_St` → `OCL_P30_DeployViaSt` → `IraqRadarP30` at `LIKE_EXISTING`.

`IraqRadarP30` is a second `STRUCTURE IMMOBILE` (`Irq_P3R`) with `RebuildHoleExposeDie` → `IraqRadarP30Damaged` (`KindOf` includes `REBUILD_HOLE`, health 9999999). Spawning it on the station footprint overlaps geometry and can punch a rebuild hole into the terrain. That is the broken map/terrain view after place. `VisionRange` was not the cause; existing `RadarUpgrade` + `GrantUpgradeCreate Upgrade_AmericaRadar` (already on this object, not a new USA upgrade) remain the ZH minimap/fog radar.

**Fix:** last-win object omits `P30_Radar_Deploy_St`. Keeps `RadarUpgrade DisableProof = No`, `ShroudClearingRange = 280`, `SpecialPowerIraqiRadarSearch`, and defines `Object IraqiRadarScan` so `SUPERWEAPON_IraqiRadarScan` is not a missing Thing. Selling/destroying the station still uses `GenericSideObjectKiller` / `SamInstallationDismantle`; `RadarUpgrade` with `DisableProof = No` drops player radar when the building is gone or unpowered.

## 3. Other buildings

`Command_SpySatelliteScan`, `SUPERWEAPON_SpySatellite`, and other radar CommandSets in `CommandSet_ZZZZ_SpySatelliteRadar.ini` are byte-identical to the source BIG.

## 4. Prior S-400 / HQ-9 last-wins

`92N6R_FireControlDataLink`, `HT233_FireControlDataLink`, `OCL_HQ9_Deployed`, `Weapon.ini`, `S400.ini`, `HQ9B.ini`, `92N6R.ini`, `HT233.ini` unchanged.

Rebuild:

```
python3 patch/tools/big/patch_spec_data_one_iraq_radar.py \
  --src-big patch/Release/S400_HQ9_RADAR_LINK/_SPEC_DATA_ONE.big \
  --out-big _SPEC_DATA_ONE.big
```
