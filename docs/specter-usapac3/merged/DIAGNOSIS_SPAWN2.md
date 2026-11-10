# USAPAC3 spawn crash — second diagnosis (packed BIG, not overlay)

Zero Hour was not run. In-game crash after the previous spawnfix release is the user's report.

## Packed winners

| Name | Packed path | Count |
|---|---|---:|
| `Object USAPAC3` | `Data\INI\Object\Specter\PatchSystems\AirDefense\USAPAC3.ini` | 1 |
| `Weapon USAPAC3_Weapon` | `Data\INI\Weapon_USAPAC3.ini` | 1 |
| `Object USAPAC3_Projectile` | `Data\INI\Object\Specter\PatchSystems\AirDefense\USAPAC3_Projectile.ini` | 1 |
| `CommandSet USAPAC3CommandSet` | `Data\INI\CommandSet_ZZZZ_USAPAC3.ini` | 1 |

`Object America_AD_THAAD` is **not** in `_SPEC_DATA_ONE.big`. Gameplay was cloned from an overlay that the live game does not load.

Live American deploy TEL in the same BIG: `Object US_THAAD` in
`Data\INI\Object\Specter\United States Of America\AirDefense\US_M1120.ini`.
Same Command Center spawn class: `W3DTruckDraw` + `DeployStyleAIUpdate` + `Generic8x8Locomotor` + `Weapon` SECONDARY/TERTIARY + `CAN_ATTACK`.

Live Patriot truck with no animation: `Object AmericaMobileSamSiteMIM104F` (`MIM104F.ini`), model `US_M1075`.

## Spawn-time load (W3DModelDraw loads every ConditionState model at create)

Previous Draw still loaded at the moment construction finishes:

- `UsaPac3Car`, `UsaPac3Car_d`
- `UsaPac3F`, `UsaPac3F_d` (PACKING / DEPLOYED)
- `UsaPac3Car_w` (second `W3DTruckDraw`)

So `UsaPac3F` and `UsaPac3Car_w` **are** on the spawn path even if the default state is the packed car. The attach-only change left that intact.

## Draw vs live `US_THAAD` (line-level)

| Item | Live `US_THAAD` (spawns) | Packed `USAPAC3` (crashes) |
|---|---|---|
| Draw modules | 1× `W3DTruckDraw` | 2× `W3DTruckDraw` |
| Default model | `US_M1120` | `UsaPac3Car` |
| Default animation flags | `ONCE_BACKWARDS` + `START_FRAME_FIRST` | `ONCE` + `MAINTAIN_FRAME_ACROSS_STATES PRISTINE_BONE_POS_IN_FINAL_FRAME` |
| Turret in Draw | none | `Turret01` / `TurretEL01` on almost every state |
| WeaponLaunchBone | none | PRIMARY/SECONDARY/TERTIARY `FIREPOINT` (no PRIMARY weapon) |
| Deployed model | `US_M1120_A` + `ONCE`/`START_FRAME_LAST` | `UsaPac3F` + `MANUAL` + `PRISTINE_BONE_POS_IN_FINAL_FRAME` |
| Extra axle Draw | none | `UsaPac3Car_w` (`TIRE09`/`TIRE10` only) |
| Body / Physics / Loco / Geometry | ActiveBody 400 / Mass 400 / Generic8x8 / BOX 45×12×16 | same pattern (health 900) |
| WeaponSet | SECONDARY+TERTIARY only | same |
| KindOf CAN_ATTACK | yes | yes |
| DeployStyleAIUpdate turret block | none | none |

`UsaPac3Car` is a complete TEL (53 bones, chassis, tires, turret). `UsaPac3Car_w` is not; it is a 3-bone wheel fragment. Live `US_THAAD` never attaches a second truck Draw.

`PRISTINE_BONE_POS_IN_FINAL_FRAME` plus `WeaponLaunchBone PRIMARY FIREPOINT` runs when the drawable is constructed. Live `US_THAAD` does not.

## Names used at create (exist in packed DATA/ART)

Present: `Generic8x8Locomotor`, `USAPAC3_Weapon`, `USAPAC3_Projectile`, `AIM-120CLocomotor`, `LargeVehicleArmor`, `TankDamageFX`, `USAPAC3CommandSet` and its CommandButtons, `MappedImage USAPAC3`, `RocketBuggyDust`, `EXTireTrack.tga`, W3D+texture stems in ART TWO.

Not used at create: death OCL/FX, projectile fire, `Engine01` on `pac3mis_m`.

## Cause (evidence)

Not CommandSet slot 6, not Science, not missing W3D files, not duplicate Object.

The spawn drawable is not the live American TEL Draw. Three spawn-time differences vs `US_THAAD`:

1. Second `W3DTruckDraw` on `UsaPac3Car_w` (still present after spawnfix).
2. `PRISTINE_BONE_POS_IN_FINAL_FRAME` + turret + PRIMARY launch bones on DefaultConditionState.
3. `UsaPac3F` loaded at create via PACKING/DEPLOYED, with `MANUAL` flags live THAAD does not use.

Fix: one `W3DTruckDraw`, `US_THAAD` condition/animation flags, New Donor models only, no second Draw, no turret/launch-bone/pristine flags. Cost, time, slot 6, weapons, THAAD/Patriot/NASAMS unchanged.
