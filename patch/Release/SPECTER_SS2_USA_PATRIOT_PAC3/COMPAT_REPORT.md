# America Patriot PAC-3 — V25 hull, SS2 THAAD fire

## Crash (#787)

See `CRASH_REPORT.md`. #787 put `W3DTruckDraw`+TrackMarks on `US_MIM104F_L` and `FS_BASE_DEFENSE` on a CC vehicle. Live THAAD/USAPAC3 do not.

## V25 appearance used

From `AmericaPATRIO`: BOX 25×9×15, health 240, turret 180/180, scan 360, side America, CC UNIT_BUILD.
SS2 art: `US_MIM104F_L` + missile `PAC-3` (`_SPEC_ART_TWO.big`). V25 `USPAC3`/`PAC3MSE` W3Ds are absent; they were not referenced.

## THAAD fire cloned (unique names, THAAD files untouched)

| Role | Live THAAD | Patriot clone |
|---|---|---|
| AA weapon | `8x_LRSAM_THAAD` PENALTY, `THAAD_AA_OBJECT` | `AmericaPatriotPAC3_AA` → `AmericaPatriotPAC3_AA_Object` |
| ABM weapon | `THAADMissile_ABM` CRUSH + `AntiSmallMissile` | `AmericaPatriotPAC3_ABM` |
| ABM projectile | `THAAD_ABM_OBJECT` (WATER/FALLING fuze, 0% vs BM) | `AmericaPatriotPAC3_ABM_Object` + `AmericaPatriotPAC3_ABM_Fuze` CRUSH (USAPAC3 path) |
| FX/OCL/sound | `FX_LargeSamMissilesTubeOut`, `Thaad_fire`, `OCL_48N6TargetLock` / `OCL_40N6STargetLock` | same live names, not copied |

AirplaneArmor takes PENALTY. BallisticMissileArmor / CruiseMissileArmor take CRUSH, not PENALTY/FALLING/WATER.

## Wiring

`AmericaCommandCenterCommandSet` slot 10 = `Command_ConstructAmericaVehiclePatriotPAC3`. Slot 1 dozer and slot 6 `USAPAC3` kept. Unit CommandSet = live `GLAVehicleRocketBuggyCommandSet`. Turkey, GLA, Iran factory, `US_THAAD` unchanged.
